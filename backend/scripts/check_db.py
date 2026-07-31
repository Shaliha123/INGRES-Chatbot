import asyncio
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

# Ensure backend package is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import db, connect_to_mongo, close_mongo_connection

async def check_db():
    await connect_to_mongo()
    
    try:
        # 1. Search for documents
        doc_count = await db.db.documents.count_documents({})
        kb_count = await db.db.knowledge_base.count_documents({})
        print("\n--- Debugging Sliding Window ---")
        cursor = db.db.documents.find({"filename": "16881058231005451482file.pdf"})
        async for doc in cursor:
            content = doc.get("extracted_text", "")
            lower_content = content.lower()
            
            query = "What percentage of wells showed a rise during the 2017-18 seasonal fluctuation?"
            from backend.app.services.ai_service import normalize_query, STOP_WORDS
            import re
            
            clean_q = normalize_query(query)
            words = [k for k in re.findall(r'\w+', clean_q) if len(k) > 2]
            filtered_words = [w for w in words if w not in STOP_WORDS]
            
            print(f"Filtered words: {filtered_words}")
            
            WINDOW_SIZE = 1500
            max_score = -1
            best_window = ""
            best_idx = 0
            
            step = WINDOW_SIZE // 3
            for i in range(0, len(content), step):
                window_lower = lower_content[i:i+WINDOW_SIZE]
                matches = sum(1 for word in filtered_words if word in window_lower)
                phrase_matches = sum(1 for j in range(len(filtered_words)-1) 
                                     if f"{filtered_words[j]} {filtered_words[j+1]}" in window_lower)
                total_score = matches + (phrase_matches * 3)
                
                if total_score > max_score:
                    max_score = total_score
                    best_window = content[i:i+WINDOW_SIZE]
                    best_idx = i
                    
                if 54617 >= i and 54617 < i + WINDOW_SIZE:
                    print(f"Window at {i} (contains correct answer) - Score: {total_score}, Matches: {matches}, Phrases: {phrase_matches}")
                    
            print(f"\nBest window at {best_idx} - Score: {max_score}")
            print(f"Best window preview:\n{best_window[:200]} ...")

        # Run Retrieval orchestration directly
        from backend.app.schemas.conversation import ConversationContext
        from backend.app.services.retrieval_orchestrator import orchestrate_production_pipeline
        
        ctx = ConversationContext(conversation_id="test", chat_history=[], conversation_state={})
        res = await orchestrate_production_pipeline("What percentage of wells showed a rise during the 2017-18 seasonal fluctuation?", ctx)
        
        print("\n--- Retrieval Orchestrator Result ---")
        scores = res.get("evidence_scores", [])
        print(f"Extracted Context Blocks: {len(scores)}")
        for s in scores:
            print(f"- Source: {s.get('source_name', 'Unknown')} | Score: {s.get('composite_confidence')}")
        final_resp = res.get('response', '')
        print(f"Final Response: {final_resp.encode('ascii', 'ignore').decode('ascii')}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(check_db())
