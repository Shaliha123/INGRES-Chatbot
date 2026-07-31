import logging
import re
from typing import Dict, Any, Tuple

logger = logging.getLogger("ingres.reflection")

def is_year(num_str: str) -> bool:
    """Helper to check if a numeric string is likely a year."""
    try:
        val = int(num_str.replace('%', '').replace(',', ''))
        return 1900 <= val <= 2100
    except ValueError:
        return False

def reflect_on_answer(query: str, generated_answer: str, context: str) -> Tuple[bool, str]:
    """
    Reflection Engine Layer:
    Self-checks the generated answer against the user question:
    - Did I answer the core question?
    - Did I regurgitate off-topic boilerplate?
    - Are there hallucinated numeric facts?
    Returns (is_passed, feedback_note).
    """
    clean_q = query.lower()
    clean_ans = generated_answer.lower()

    if "sufficient evidence" in clean_ans or "couldn't find evidence" in clean_ans or "not contain specific information" in clean_ans:
        return True, "Passed self-check"

    # 1. Numeric Hallucination Self-Check
    # Normalize spaces before percentage signs
    norm_ans = re.sub(r'\s+%', '%', generated_answer)
    norm_ctx = re.sub(r'\s+%', '%', context)
    
    ans_numbers = set(re.findall(r'\b\d+(?:\.\d+)?%?\b', norm_ans))
    context_numbers = set(re.findall(r'\b\d+(?:\.\d+)?%?\b', norm_ctx))
    
    unsupported_numbers = set()
    for num in ans_numbers:
        if num not in context_numbers:
            if is_year(num):
                continue
            # Ignore small single digits (often used for lists/formatting) unless it's a percentage
            if num.isdigit() and len(num) == 1 and '%' not in num:
                continue
            unsupported_numbers.add(num)
            
    if unsupported_numbers:
        return False, f"Answer failed self-check: Contains unsupported numeric values: {unsupported_numbers}. Do not generate factual numbers or percentages not present in the retrieved context. If evidence is missing, state that you cannot answer."

    # 2. Water Quality Self-Check
    if "safe for drinking" in clean_q or "quality" in clean_q:
        if "ph" not in clean_ans and "tds" not in clean_ans and "safe" not in clean_ans:
            return False, "Answer failed self-check: Water quality query must mention pH/TDS parameters."

    logger.info("Reflection self-check passed successfully.")
    return True, "Passed self-check"
