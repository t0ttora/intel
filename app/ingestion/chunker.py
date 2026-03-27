"""Text chunking (300-500 tokens per chunk)."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class TextChunk:
    """A chunk of text with metadata about its position."""

    text: str
    chunk_index: int
    total_chunks: int


# Rough token count: ~4 characters per token for English
CHARS_PER_TOKEN = 4
MIN_CHUNK_TOKENS = 300
MAX_CHUNK_TOKENS = 500
MIN_CHUNK_CHARS = MIN_CHUNK_TOKENS * CHARS_PER_TOKEN  # 1200
MAX_CHUNK_CHARS = MAX_CHUNK_TOKENS * CHARS_PER_TOKEN  # 2000
OVERLAP_CHARS = 200  # ~50 tokens overlap between chunks


def _estimate_tokens(text: str) -> int:
    """Rough token estimate based on character count."""
    return len(text) // CHARS_PER_TOKEN


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(text: str) -> list[TextChunk]:
    """Split text into chunks of 300-500 tokens with sentence-boundary awareness.

    Short texts (< MIN_CHUNK_TOKENS) are returned as a single chunk.
    Longer texts are split at sentence boundaries with overlap.
    """
    text = text.strip()
    if not text:
        return []

    # Short text — single chunk
    if _estimate_tokens(text) <= MAX_CHUNK_TOKENS:
        return [TextChunk(text=text, chunk_index=0, total_chunks=1)]

    sentences = _split_sentences(text)
    chunks: list[TextChunk] = []
    current_chunk: list[str] = []
    current_chars = 0

    for sentence in sentences:
        sentence_chars = len(sentence)

        # If adding this sentence would exceed max, finalize current chunk
        if current_chars + sentence_chars > MAX_CHUNK_CHARS and current_chunk:
            chunk_text_str = " ".join(current_chunk)
            chunks.append(TextChunk(text=chunk_text_str, chunk_index=len(chunks), total_chunks=0))

            # Overlap: keep last sentences up to OVERLAP_CHARS
            overlap_chars = 0
            overlap_start = len(current_chunk)
            for j in range(len(current_chunk) - 1, -1, -1):
                overlap_chars += len(current_chunk[j])
                if overlap_chars >= OVERLAP_CHARS:
                    overlap_start = j
                    break
            current_chunk = current_chunk[overlap_start:]
            current_chars = sum(len(s) for s in current_chunk)

        current_chunk.append(sentence)
        current_chars += sentence_chars

    # Final chunk
    if current_chunk:
        chunk_text_str = " ".join(current_chunk)
        chunks.append(TextChunk(text=chunk_text_str, chunk_index=len(chunks), total_chunks=0))

    # Update total_chunks
    total = len(chunks)
    for chunk in chunks:
        chunk.total_chunks = total

    return chunks
