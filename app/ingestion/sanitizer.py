"""Prompt injection guard — strip adversarial LLM instructions from untrusted content."""
from __future__ import annotations

import re

INJECTION_PATTERNS = re.compile(
    r"(?i)("
    r"ignore\s+(all\s+)?previous\s+instructions|"
    r"you\s+are\s+now\s+|"
    r"system\s*:\s*|"
    r"act\s+as\s+(a\s+)?|"
    r"pretend\s+(you\s+are|to\s+be)|"
    r"jailbreak|"
    r"DAN\s+mode|"
    r"do\s+anything\s+now|"
    r"\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>"
    r")"
)


def sanitize_content(text: str) -> str:
    """Strip known prompt injection patterns from untrusted content."""
    cleaned = INJECTION_PATTERNS.sub("[REDACTED]", text)
    return cleaned.strip()


def contains_injection(text: str) -> bool:
    """Check if text contains prompt injection patterns."""
    return bool(INJECTION_PATTERNS.search(text))
