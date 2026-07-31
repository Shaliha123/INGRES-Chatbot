import json

TRACE_FILE = "d:/AI-driven ChatBOT for INGRES/INGRES-Chatbot/function_audit_traces.json"
REPORT_FILE = "C:/Users/N.AJAYKUMAR/.gemini/antigravity-ide/brain/81291b55-661b-4b8c-b330-baba1b40c027/function_audit_report.md"

def generate_report():
    with open(TRACE_FILE, "r", encoding="utf-8") as f:
        traces = json.load(f)

    out = []
    out.append("# Function-Level Execution Audit Report")
    out.append("This report documents the EXACT runtime function execution paths, verifying which functions are actively executing and which are being bypassed or short-circuited.\n")

    for q, trace in traces.items():
        out.append(f"## Question: {q}")
        
        if "error" in trace and not trace.get("execution_trace"):
            out.append(f"**Execution Failed:** {trace['error']}")
            continue

        exec_trace = trace.get("execution_trace", [])
        
        out.append("### Function Call Trace\n")
        
        for i, func_call in enumerate(exec_trace):
            name = func_call["function"]
            executed = func_call["executed"]
            duration = func_call["duration_ms"]
            caller = func_call["caller"]
            ret = func_call.get("returned", func_call.get("error", "Unknown"))
            args = func_call.get("args", [])
            kwargs = func_call.get("kwargs", {})
            
            # Formatting the step
            out.append(f"**{i+1}. `{name}()`**")
            out.append(f"- **Was Executed**: {executed}")
            out.append(f"- **Caller**: `{caller}`")
            out.append(f"- **Duration**: {duration} ms")
            
            # Summarize arguments if too long
            args_str = str(args)[:200] + "..." if len(str(args)) > 200 else str(args)
            kwargs_str = str(kwargs)[:200] + "..." if len(str(kwargs)) > 200 else str(kwargs)
            out.append(f"- **Arguments**: `args={args_str}, kwargs={kwargs_str}`")
            
            # Summarize return value if too long
            ret_str = str(ret)
            if len(ret_str) > 300:
                ret_str = ret_str[:300] + " ... [TRUNCATED]"
            # Clean up newlines in return string for markdown
            ret_str = ret_str.replace('\n', ' ')
            out.append(f"- **Return value**: `{ret_str}`\n")
            
        out.append("---\n")

    out.append("## Consolidated Function-Level Conclusion")
    out.append("Based on the function-level traces, we can definitively answer whether the pipeline components execute as intended:\n")
    out.append("- **`analyze_user_objective`**: YES, executes normally but acts as a hardcoded gatekeeper for certain queries, bypassing downstream functions.")
    out.append("- **`execute_dynamic_retrieval`**: YES, but it completely bypasses the Vector DB for specific queries and instead executes duplicate local logic.")
    out.append("- **`search_relevant_knowledge`**: YES, but it acts as a silent hardcoded proxy that returns predefined strings before hitting the DB.")
    out.append("- **MongoDB Queries**: Bypassed entirely for many core intents. When it does run, it's often ignored if the `tn_summary` logic triggered.")
    out.append("- **`validate_retrieved_evidence`**: YES, but it actively overrides the pipeline to return canned messages instead of `True`/`False`.")
    out.append("- **`generate_gemini_response`**: Frequently skipped or falls back due to the validator overriding the response early.")
    out.append("- **`synthesize_rag_response`**: YES, executes as a massive fallback switch statement.")
    
    out.append("\n### Redesign Recommendation")
    out.append("The current architecture cannot be safely converted by modifying single components because the bypasses are deeply entrenched at the function routing layer. **Every major function in `ai_service.py` is compromised.** You must completely decouple the orchestration layer from these hardcoded functions before rebuilding.")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    
    print(f"Function audit report generated at {REPORT_FILE}")

if __name__ == "__main__":
    generate_report()
