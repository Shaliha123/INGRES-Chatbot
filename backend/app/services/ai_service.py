import logging
import re
import httpx
from typing import List, Tuple
from backend.app.config import settings
from backend.app.database import db

logger = logging.getLogger("ingres.ai")

SYSTEM_PROMPT = """You are an evidence-bound RAG assistant (Integrated Groundwater Information Retrieval System).
You act as a senior Hydrogeological AI Expert, but your knowledge is strictly limited to the provided context.

YOUR CORE PRINCIPLE:
1. Treat the retrieved evidence as the only authoritative source for factual claims.
2. Do not introduce facts, statistics, reports, organizations, citations, or conclusions that are not directly supported by the retrieved evidence.
3. If the retrieved evidence is insufficient or empty, you must explicitly state that instead of guessing or filling gaps.

EXPECTED RESPONSE STRUCTURE:
1. Direct Answer: Provide a concise answer to the user's question, sourced strictly from the context.
2. Supporting Evidence: Present the exact retrieved evidence that supports the answer.
3. Analysis: Explain how the evidence answers the query. Do not add external facts here.
4. Confidence: Indicate confidence based purely on the quality of the provided context.
5. Sources Used: List every source actually used from the context. Never fabricate citations.
6. Follow-Up Questions: Generate 2-3 dynamic, highly relevant follow-up questions the user can ask next based on this conversation and retrieved evidence.

WHEN EVIDENCE IS MISSING:
If the provided context does not contain sufficient information to answer the question, you MUST respond honestly. State "I do not have sufficient evidence to answer this." Do NOT substitute fabricated statistics, predefined reports, or external knowledge. Suggest alternative related questions based on the available capabilities.
"""

def clean_extracted_text(text: str) -> str:
    """Filter cover page boilerplate, author lists, and merge fragmented PDF lines into continuous cohesive sentences."""
    if not text:
        return ""
    
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    skip_patterns = [
        r"CONTRIBUTORS", r"PRINCIPAL AUTHORS", r"HYDROCHEMISTRY",
        r"DATA COLLECTION", r"Scientist\s*-[A-Z]", r"Scientist\s*–[A-Z]", r"Smt\.", r"Shri", r"PAGE\s*\d+",
        r"GOVERNMENT OF INDIA", r"MINISTRY OF WATER RESOURCES", r"Drawing Section",
        r"OF PUDUCHERRY", r"HYDROGEOLOGY Ms\.", r"Rajarajan", r"Dhayamalar", r"Senthil Kumar", r"AUTHOR"
    ]
    
    filtered_lines = []
    for line in lines:
        if any(re.search(pat, line, re.IGNORECASE) for pat in skip_patterns) and len(line) < 75:
            continue
        filtered_lines.append(line)
        
    if not filtered_lines:
        return text

    paragraphs = []
    current_para = []
    
    for line in filtered_lines:
        current_para.append(line)
        if line.endswith(('.', '?', '!', ':', ';')):
            paragraphs.append(" ".join(current_para))
            current_para = []
            
    if current_para:
        paragraphs.append(" ".join(current_para))
        
    return "\n\n".join(paragraphs)

TYPO_MAPPINGS = {
    "tmailnadu": "tamil nadu",
    "tamilnadu": "tamil nadu",
    "stae": "state",
    "distrct": "district",
    "distrcit": "district",
    "districts": "district",
    "distrcts": "district",
    "distrcits": "district",
    "disticts": "district",
    "ground water": "groundwater",
    "aqufer": "aquifer",
    "recharhe": "recharge"
}

def normalize_query(query: str) -> str:
    """Correct common hydrogeological and geographical typos in user prompts."""
    normalized = query.lower()
    for typo, correction in TYPO_MAPPINGS.items():
        normalized = re.sub(r'\b' + re.escape(typo) + r'\b', correction, normalized)
    return normalized

STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "and", "or", "but", "if", "then", "else", "when", "up", "down", "left", "right", "what", "where", "how", "why", "who", "this", "that", "those", "these", "all", "have", "has", "had", "do", "does", "did", "list", "show", "give", "tell", "me", "about", "data", "info", "information"}

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    import math
    if not v1 or not v2: return 0.0
    dot = sum(a*b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a*a for a in v1))
    norm2 = math.sqrt(sum(a*a for a in v2))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

async def search_relevant_knowledge(query: str, limit: int = 5) -> Tuple[str, List[str], List[dict]]:
    """Advanced Hybrid Retrieval with Vector Embeddings, Reranking, and Neighbor Expansion."""
    clean_q = normalize_query(query).lower()
    
    # 1. Document Filtering
    doc_filter = {}
    if "year book" in clean_q or "yearbook" in clean_q:
        doc_filter["document_title"] = {"$regex": "year book", "$options": "i"}
    elif "quality report" in clean_q:
        doc_filter["document_title"] = {"$regex": "quality report", "$options": "i"}
        
    if "table of contents" not in clean_q and "contents" not in clean_q:
        doc_filter["is_table_of_contents"] = {"$ne": True}
        
    # 2. Query Embedding
    query_emb = await generate_embedding(query)
    
    # 3. Retrieve Candidate Chunks
    words = [k for k in re.findall(r'\w+', clean_q) if len(k) > 2]
    filtered_words = [w for w in words if w not in STOP_WORDS]
    
    candidates = []
    if db.db is not None:
        cursor = db.db.document_chunks.find(doc_filter)
        async for chunk in cursor:
            # BM25 Keyword Score Approximation
            chunk_lower = chunk.get("text_content", "").lower()
            keyword_score = sum(1 for w in filtered_words if w in chunk_lower) / max(1, len(filtered_words))
            
            # Vector Similarity
            chunk_emb = chunk.get("embedding", [])
            vec_score = cosine_similarity(query_emb, chunk_emb) if query_emb and chunk_emb else 0.0
            
            # Section Heading Match
            heading = chunk.get("section_heading", "").lower()
            section_match = 1.0 if any(w in heading for w in filtered_words) else 0.0
            
            # TOC Penalty
            toc_penalty = 1.0 if "contents" in heading or "table of" in heading or "..." in chunk_lower[:50] else 0.0
            
            # Calculate Final Score (leaving Neighbor Consistency to be added if expanded)
            final_score = (0.45 * vec_score) + (0.25 * keyword_score) + (0.15 * section_match) - (0.15 * toc_penalty)
            
            chunk["vec_score"] = vec_score
            chunk["keyword_score"] = keyword_score
            chunk["section_match"] = section_match
            chunk["toc_penalty"] = toc_penalty
            chunk["final_score"] = final_score
            candidates.append(chunk)
            
    # Sort and select Top-K
    candidates.sort(key=lambda x: x["final_score"], reverse=True)
    top_k = candidates[:limit]
    
    # 4. Neighbor Expansion & Consistency
    final_chunks = []
    seen_ids = set()
    
    for rank, chunk in enumerate(top_k, 1):
        chunk["rank"] = rank
        c_idx = chunk.get("chunk_index")
        d_id = chunk.get("document_id")
        
        # Neighbor consistency logic
        neighbors = [c_idx]
        if c_idx is not None and d_id:
            # Try to fetch neighbors from DB
            adj_cursor = db.db.document_chunks.find({"document_id": d_id, "chunk_index": {"$in": [c_idx - 1, c_idx + 1]}})
            async for adj in adj_cursor:
                if adj["chunk_id"] not in seen_ids:
                    adj["rank"] = rank # inherit rank for diagnostics
                    adj["is_neighbor"] = True
                    final_chunks.append(adj)
                    seen_ids.add(adj["chunk_id"])
                    neighbors.append(adj["chunk_index"])
        chunk["neighbor_expansion"] = f"{min(neighbors)}-{max(neighbors)}" if len(neighbors) > 1 else str(c_idx)
        
        if chunk["chunk_id"] not in seen_ids:
            chunk["is_neighbor"] = False
            final_chunks.append(chunk)
            seen_ids.add(chunk["chunk_id"])

    # 5. Format Context
    context_parts = []
    sources = []
    diagnostic_logs = []
    
    final_chunks.sort(key=lambda x: (x.get("document_id", ""), x.get("chunk_index", 0)))
    
    for c in final_chunks:
        title = c.get("document_title", "Unknown")
        page = c.get("page_number", "?")
        section = c.get("section_heading", "Unknown")
        idx = c.get("chunk_index", "?")
        
        sources.append(title)
        context_parts.append(f"[Document: {title} | Page: {page} | Section: {section}]\n{c.get('text_content', '')}")
        
        diagnostic_logs.append({
            "document": title,
            "page": page,
            "chunk_index": idx,
            "section": section,
            "vec_score": c.get("vec_score", 0.0),
            "keyword_score": c.get("keyword_score", 0.0),
            "section_match": c.get("section_match", 0.0),
            "toc_penalty": c.get("toc_penalty", 0.0),
            "final_score": c.get("final_score", 0.0),
            "rank": c.get("rank"),
            "neighbor_expansion": c.get("neighbor_expansion", str(idx)),
            "is_neighbor": c.get("is_neighbor", False)
        })

    context_text = "\n\n".join(context_parts)
    unique_sources = list(dict.fromkeys(sources))
    return context_text, unique_sources, diagnostic_logs

async def generate_embedding(text: str) -> List[float]:
    """Generate vector embeddings for semantic search using Gemini API."""
    if not settings.GEMINI_API_KEY:
        return []
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {
            "parts": [{"text": text[:9000]}]
        }
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("embedding", {}).get("values", [])
            else:
                logger.error(f"Embedding generation failed: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Embedding generation exception: {e}")
            
    return []

async def generate_gemini_response(question: str, context: str) -> str:
    """
    Generative AI Reasoning Engine with API Key Rotation Fallback & Token Optimization.
    """
    # Build list of active API keys to attempt (Primary Key + Fallback Key)
    api_keys = []
    if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 20:
        api_keys.append(("Primary", settings.GEMINI_API_KEY))
    if settings.GEMINI_API_KEY_FALLBACK and len(settings.GEMINI_API_KEY_FALLBACK) > 20:
        api_keys.append(("Fallback", settings.GEMINI_API_KEY_FALLBACK))

    prompt = f"{SYSTEM_PROMPT}\n\n"
    if context:
        prompt += f"=== INTEGRATED MULTI-SOURCE CONTEXT ===\n{context}\n=======================================\n\n"
    else:
        prompt += "=== INTEGRATED MULTI-SOURCE CONTEXT ===\nNo specific local document matches found for this query.\n=======================================\n\n"

    prompt += f"User Question: {question}\n\nSynthesized Expert Answer:"

    # Estimate prompt tokens (~4 chars per token)
    estimated_tokens = len(prompt) // 4
    logger.info(f"Gemini Generative Request: Estimated Prompt Tokens = {estimated_tokens}")

    models_to_try = [
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash"
    ]

    async with httpx.AsyncClient(timeout=15.0) as client:
        if api_keys:
            for key_label, api_key in api_keys:
                for model in models_to_try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.4,
                            "maxOutputTokens": 750
                        }
                    }
                    try:
                        response = await client.post(url, json=payload)
                        if response.status_code == 200:
                            data = response.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    ans = parts[0].get("text", "").strip()
                                    logger.info(f"Gemini Generative Success via {key_label} Key ({model})!")
                                    return ans
                        elif response.status_code == 403:
                            logger.warning(f"Gemini API {key_label} Key ({model}) forbidden (HTTP {response.status_code}). Trying next key...")
                            break  # Switch to next key immediately if key is invalid
                        elif response.status_code == 429:
                            logger.warning(f"Gemini API {key_label} Key ({model}) quota limit hit (HTTP {response.status_code}). Trying next model...")
                            continue  # Try the next model on the same key
                    except Exception as e:
                        logger.warning(f"Gemini API {key_label} Key ({model}) attempt failed: {e}")

        # Fallback Agent #2: OpenAI API (ChatGPT) if configured
        openai_key = settings.OPENAI_API_KEY
        if openai_key and openai_key.startswith("sk-"):
            openai_url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            openai_payload = {
                "model": settings.OPENAI_MODEL or "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"=== INTEGRATED MULTI-SOURCE CONTEXT ===\n{context}\n\nUser Question: {question}"}
                ],
                "temperature": 0.4,
                "max_tokens": 750
            }
            try:
                logger.warning(f"Attempting OpenAI Fallback Agent ({settings.OPENAI_MODEL})...")
                res = await client.post(openai_url, headers=headers, json=openai_payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        ans = choices[0].get("message", {}).get("content", "").strip()
                        logger.info("OpenAI Fallback Agent Success!")
                        return ans
                else:
                    logger.error(f"OpenAI Fallback Agent failed with HTTP {res.status_code}: {res.text}")
            except Exception as e:
                logger.warning(f"OpenAI Fallback Agent attempt failed: {e}")

        # Fallback Agent #3: Groq API if configured
        groq_key = settings.GROQ_API_KEY
        if groq_key and len(groq_key) > 10:
            groq_url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            groq_payload = {
                "model": settings.GROQ_MODEL or "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"=== INTEGRATED MULTI-SOURCE CONTEXT ===\n{context}\n\nUser Question: {question}"}
                ],
                "temperature": 0.4,
                "max_tokens": 750
            }
            try:
                logger.warning(f"Attempting Groq Fallback Agent ({settings.GROQ_MODEL})...")
                res = await client.post(groq_url, headers=headers, json=groq_payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        ans = choices[0].get("message", {}).get("content", "").strip()
                        logger.info("Groq Fallback Agent Success!")
                        return ans
                else:
                    logger.error(f"Groq Fallback Agent failed with HTTP {res.status_code}: {res.text}")
            except Exception as e:
                logger.warning(f"Groq Fallback Agent attempt failed: {e}")

        # Fallback Agent #4: OpenRouter API if configured
        or_key = settings.OPENROUTER_API_KEY
        if or_key and len(or_key) > 10:
            or_url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {or_key}",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "INGRES AI Assistant",
                "Content-Type": "application/json"
            }
            or_payload = {
                "model": settings.OPENROUTER_MODEL or "meta-llama/llama-3-8b-instruct:free",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"=== INTEGRATED MULTI-SOURCE CONTEXT ===\n{context}\n\nUser Question: {question}"}
                ],
                "temperature": 0.4,
                "max_tokens": 750
            }
            try:
                logger.warning(f"Attempting OpenRouter Fallback Agent ({settings.OPENROUTER_MODEL})...")
                res = await client.post(or_url, headers=headers, json=or_payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        ans = choices[0].get("message", {}).get("content", "").strip()
                        logger.info("OpenRouter Fallback Agent Success!")
                        return ans
                else:
                    logger.error(f"OpenRouter Fallback Agent failed with HTTP {res.status_code}: {res.text}")
            except Exception as e:
                logger.warning(f"OpenRouter Fallback Agent attempt failed: {e}")

    # Fallback Level 5: System Error
    logger.error("All generative AI backends failed to produce a response.")
    return "I am currently experiencing technical difficulties connecting to the Generative AI engine. Please try again later."
