import logging
from typing import Dict, Any, List, Optional
from backend.app.schemas.conversation import ConversationState, ConversationContext
from backend.app.services.ai_service import normalize_query
from backend.app.services.intent_service import KNOWN_STATES, KNOWN_DISTRICTS, KNOWN_RIVERS
from backend.app.services.cache_manager import conversation_cache

logger = logging.getLogger("ingres.conversation_manager")

class ConversationManager:
    """
    Domain-agnostic Conversation Manager handling:
    - State Manager
    - Entity Memory
    - Coreference Resolver
    - Context Builder
    - Cache Interactions
    """
    
    def __init__(self, cache_manager=conversation_cache):
        self.cache = cache_manager

    async def get_state(self, conversation_id: str, db_collection: Any) -> ConversationState:
        """Fetch the most recent conversation state."""
        # Check cache first
        cached_state = self.cache.get(f"state:{conversation_id}")
        if cached_state:
            return cached_state
            
        # Fallback to DB
        last_chat = await db_collection.find_one(
            {"conversation_id": conversation_id},
            sort=[("timestamp", -1)]
        )
        if last_chat and "state" in last_chat:
            state = ConversationState(**last_chat["state"])
            self.cache.set(f"state:{conversation_id}", state)
            return state
            
        # New State
        return ConversationState(conversation_id=conversation_id)

    def update_entity_memory(self, current_state: ConversationState, query: str) -> Dict[str, str]:
        """Level 2 Coreference: Update entity memory dynamically based on recognized entities."""
        lower_q = normalize_query(query)
        entities = {}
        
        # We perform domain-agnostic extraction using the globally loaded dynamic entities
        for d in KNOWN_DISTRICTS:
            if d in lower_q:
                entities["district"] = d.title()
                break
                
        for s in KNOWN_STATES:
            if s in lower_q:
                entities["state"] = s.title()
                break
                
        # Merge with previous state if missing but context implies continuity
        # Wait, Level 1 and 2 Coreference resolution handles this.
        return entities

    async def resolve_coreference(self, query: str, state: ConversationState, current_entities: Dict[str, str]) -> str:
        """
        Level 1: Conversation State
        Level 2: Entity Memory
        Level 3: LLM Rewrite (if highly ambiguous)
        """
        lower_q = normalize_query(query)
        
        # Level 1 & 2: Deterministic Resolution
        is_follow_up_pointer = any(k in lower_q for k in ["there", "here", "what about", "how about", "same place", "that district", "this state"])
        
        if (is_follow_up_pointer or len(query.split()) <= 4) and not current_entities:
            # We lack entities but have a pointer word OR the query is short context-dependent like "Show rainfall"
            resolved_query = query
            if state.entities.get("district"):
                resolved_query += f" in {state.entities['district']}"
            elif state.entities.get("state"):
                resolved_query += f" in {state.entities['state']}"
            
            logger.info(f"Coreference Level 1/2 resolved: '{query}' -> '{resolved_query}'")
            return resolved_query
            
        # Level 3: LLM Rewrite
        # Only invoke if it's highly ambiguous and didn't get resolved deterministically above.
        if len(query.split()) <= 8 and not current_entities and not is_follow_up_pointer:
            from backend.app.services.ai_service import generate_gemini_response
            prompt = f"Rewrite this follow-up query to be self-contained using the previous topic: '{state.current_topic}'. Query: '{query}'. Output ONLY the rewritten query."
            try:
                rewritten = await generate_gemini_response(prompt, "")
                logger.info(f"Coreference Level 3 LLM resolved: '{query}' -> '{rewritten}'")
                return rewritten
            except Exception as e:
                logger.warning(f"LLM Coreference failed: {e}")
                
        return query

    def build_context(self, history: List[Dict[str, Any]], state: ConversationState) -> ConversationContext:
        """Context Builder: Assembles everything into ConversationContext."""
        return ConversationContext(
            history=history,
            conversation_state=state,
            current_topic=state.current_topic,
            entities=state.entities,
            retrieved_documents=state.active_sources,
            active_sources=state.active_sources,
            active_tools=[state.last_tool] if state.last_tool else []
        )
        
    async def process_message(self, query: str, conversation_id: str, db_collection: Any, history: List[Dict[str, Any]]) -> ConversationContext:
        """Main pipeline entrypoint for Conversation Manager."""
        logger.info(f"[Audit] Phase: Conversation Manager initialized for query: '{query}'")
        
        # 1. State Manager
        state = await self.get_state(conversation_id, db_collection)
        logger.info(f"[Audit] Phase: Conversation State loaded: {state.current_topic}, Entities: {state.entities}")
        
        # 2. Entity Memory Update
        current_entities = self.update_entity_memory(state, query)
        
        # 3. Coreference Resolver
        resolved_query = await self.resolve_coreference(query, state, current_entities)
        logger.info(f"[Audit] Phase: Coreference Resolution complete. Final Query: '{resolved_query}'")
        
        # 4. Context Builder
        context = self.build_context(history, state)
        
        return context, resolved_query, current_entities

conversation_manager = ConversationManager()
