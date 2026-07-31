import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.database import connect_to_mongo, close_mongo_connection, db
from backend.app.services.ai_service import search_relevant_knowledge

async def run_verifications():
    await connect_to_mongo()
    try:
        print("\n--- Running Retrieval Engine Verifications ---")
        
        # 1. Verify Chunk Schema
        print("\n1. Verifying Chunk Schema...")
        sample_chunk = await db.db.document_chunks.find_one()
        if not sample_chunk:
            print("  [FAIL] No chunks found in database. Run migrate_chunks.py first.")
        else:
            required_keys = ["page_number", "chunk_index", "section_heading", "embedding", "is_table_of_contents"]
            missing = [k for k in required_keys if k not in sample_chunk]
            if missing:
                print(f"  [FAIL] Missing keys in chunk: {missing}")
            else:
                print("  [PASS] Chunk schema contains all required fields.")
                
        # 2. Verify TOC Chunks are flagged
        print("\n2. Verifying TOC Flags...")
        toc_count = await db.db.document_chunks.count_documents({"is_table_of_contents": True})
        if toc_count > 0:
            print(f"  [PASS] Found {toc_count} chunks flagged as TOC.")
        else:
            print("  [WARN] No chunks flagged as TOC found.")

        # 3. Verify Document Filtering
        print("\n3. Verifying Document Filtering...")
        # Querying specifically for "year book"
        _, sources, _ = await search_relevant_knowledge("year book 2017-18")
        if any("quality report" in s.lower() for s in sources):
            print(f"  [FAIL] Document filtering failed. Found quality report in sources: {sources}")
        else:
            print(f"  [PASS] Filtering successful. Sources retrieved: {sources}")
            
        # Querying specifically for "quality report"
        _, sources_qr, _ = await search_relevant_knowledge("quality report 2025")
        if any("year book" in s.lower() for s in sources_qr):
            print(f"  [FAIL] Document filtering failed. Found year book in sources: {sources_qr}")
        else:
            print(f"  [PASS] Filtering successful. Sources retrieved: {sources_qr}")

        # 4. Verify Adjacent Chunk Expansion
        print("\n4. Verifying Adjacent Chunk Expansion...")
        _, _, diagnostics = await search_relevant_knowledge("What percentage of wells showed a rise during the 2017-18 seasonal fluctuation?")
        
        has_expansion = False
        for diag in diagnostics:
            expansion = diag.get("neighbor_expansion", "")
            if "-" in expansion:
                has_expansion = True
                print(f"  [PASS] Adjacent expansion found: {expansion}")
                break
                
        if not has_expansion:
            print("  [WARN] No adjacent chunks fetched for this query.")
            
    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(run_verifications())
