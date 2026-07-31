import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger("ingres.compressor")

def compress_context(raw_context_blocks: List[str], query: str, max_tokens: int = 750) -> str:
    """
    Context Compressor Layer (Missing Component 5):
    Filters multi-source evidence (PDF chunks, MongoDB records, Weather, Maps)
    to preserve ONLY high-signal, relevant evidence matching the query within token budget limits.
    """
    if not raw_context_blocks:
        return ""

    keywords = [w.lower() for w in query.split() if len(w) > 3]
    high_signal_paragraphs = []

    for block in raw_context_blocks:
        lines = block.splitlines()
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            # Keep header lines, bullet points, numbers, or keyword matches
            if line_str.startswith("---") or line_str.startswith("•") or line_str.startswith("1.") or any(k in line_str.lower() for k in keywords):
                high_signal_paragraphs.append(line_str)

    compressed_text = "\n".join(high_signal_paragraphs)
    
    # Fallback to full blocks if filtering was too aggressive
    if len(compressed_text.strip()) < 50:
        compressed_text = "\n\n".join(raw_context_blocks)

    # Character count budget control (~4 chars per token)
    max_chars = max_tokens * 4
    if len(compressed_text) > max_chars:
        compressed_text = compressed_text[:max_chars] + "\n...[Context Compressed for Token Safety]"

    logger.info(f"Context compressed from {sum(len(b) for b in raw_context_blocks)} to {len(compressed_text)} chars.")
    return compressed_text
