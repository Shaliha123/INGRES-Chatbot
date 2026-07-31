import os

with open('rag_test_output.txt', 'r', encoding='utf-16le') as f:
    content = f.read()

# Write to the artifact file
artifact_path = r'C:\Users\N.AJAYKUMAR\.gemini\antigravity-ide\brain\be5a28f9-e817-415a-aaf9-e69c0a6c3a7b\rag_test_results.md'
with open(artifact_path, 'w', encoding='utf-8') as f:
    f.write("# RAG System Verification Report\n\n")
    f.write("Below are the results of the RAG system verification test. ")
    f.write("The system was run in debug mode to display retrieved chunks, similarity scores, and LLM answers.\n\n")
    f.write("```text\n")
    f.write(content)
    f.write("\n```")
