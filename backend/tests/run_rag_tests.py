import asyncio
import os
import sys

# Ensure backend package is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import db, connect_to_mongo, close_mongo_connection
from backend.app.schemas.conversation import ConversationContext
from backend.app.services.retrieval_orchestrator import orchestrate_production_pipeline

# Test Questions Grouped by Section
test_questions = [
    # Beginning of the PDF
    "What is the objective of this groundwater report?",
    "Which organization published this report?",
    
    # Early Sections
    "What is the total number of observation wells?",
    "What methodology was used for groundwater monitoring?",
    
    # Middle of the PDF
    "What percentage of wells showed a rise during the 2017-18 seasonal fluctuation?",
    "Explain the seasonal groundwater fluctuation.",
    "What was the annual groundwater fluctuation?",
    
    # Later Sections
    "What are the groundwater quality parameters discussed in the report?",
    "Which districts reported groundwater quality issues?",
    "What recommendations are given for groundwater management?",
    
    # End of the PDF
    "What information is provided in the annexures?",
    "List the groundwater statistics reported for Erode district.",
    
    # Negative Test
    "What is the groundwater recharge percentage for Atlantis district?"
]

async def run_tests():
    await connect_to_mongo()
    try:
        print("\n" + "="*80)
        print("RAG RETRIEVAL DEBUG MODE - TEST REPORT")
        print("="*80 + "\n")
        
        for idx, query in enumerate(test_questions, 1):
            # Append keyword to force document retrieval planner
            query_for_planner = query + " in the report"
            print(f"\n--- Test Question {idx}/{len(test_questions)} ---")
            print(f"Q: {query}")
            
            ctx = ConversationContext(conversation_id="test_suite", chat_history=[], conversation_state={"conversation_id": "test_suite"})
            res = await orchestrate_production_pipeline(query_for_planner, ctx)
            
            # Print Retrieval Diagnostics (Debug Mode)
            print("\n[Retrieval Diagnostics]")
            diagnostics = res.get("diagnostics", [])
            if not diagnostics:
                print("No relevant chunks retrieved.")
            else:
                for d in diagnostics:
                    print(f"  Chunk {d.get('rank')}:")
                    print(f"    Document: {d.get('document')}")
                    print(f"    Page: {d.get('page')}")
                    print(f"    Section: {d.get('section')}")
                    print(f"    Neighbor Expansion: {d.get('neighbor_expansion')}")
                    print(f"    Vector Similarity: {d.get('vec_score', 0):.2f}")
                    print(f"    Keyword Score    : {d.get('keyword_score', 0):.2f}")
                    print(f"    Section Match    : {d.get('section_match', 0):.2f}")
                    print(f"    TOC Penalty      : {d.get('toc_penalty', 0):.2f}")
                    print(f"    Final Score      : {d.get('final_score', 0):.2f}")
                    print(f"    --------------------------")
                    
            print(f"\n[Retrieved Context Snippet]")
            merged_context = res.get("merged_context", "")
            if len(merged_context) > 0:
                print(f"Length: {len(merged_context)} characters")
                preview_len = min(600, len(merged_context))
                safe_text = merged_context[:preview_len].encode('ascii', 'ignore').decode('ascii')
                print(f"{safe_text}...\n")
            else:
                print("No context provided to the LLM.\n")
                
            # Print LLM Response
            final_resp = res.get("response", "")
            safe_resp = final_resp.encode('ascii', 'ignore').decode('ascii')
            print(f"[Final Answer]\n{safe_resp}")
            print("\n" + "-"*80)

    except Exception as e:
        import traceback
        print(f"Error during tests: {e}")
        traceback.print_exc()
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(run_tests())
