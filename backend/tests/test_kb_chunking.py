"""Chunker behaviour — paragraph-aware splitting + max-tokens enforcement."""
from __future__ import annotations

import pytest
import tiktoken

from app.services.kb_ingest import _split_text_to_chunks


_enc = tiktoken.get_encoding("cl100k_base")


class TestSplitter:
    def test_empty_returns_no_chunks(self):
        assert _split_text_to_chunks("") == []
        assert _split_text_to_chunks("   ") == []

    def test_short_text_one_chunk(self):
        text = "Voucher WPRZ-184220 jest aktywny."
        chunks = _split_text_to_chunks(text, max_tokens=500)
        assert len(chunks) == 1
        assert chunks[0].index == 0
        assert chunks[0].content == text

    def test_paragraphs_grouped_under_max(self):
        # Two short paragraphs should fit in a single chunk.
        text = "Pierwszy paragraf o voucherze.\n\nDrugi paragraf o regulaminie."
        chunks = _split_text_to_chunks(text, max_tokens=500)
        assert len(chunks) == 1
        assert "Pierwszy paragraf" in chunks[0].content
        assert "Drugi paragraf" in chunks[0].content

    def test_long_text_split_into_multiple(self):
        # ~ 1500-token text built from a repeating Polish sentence.
        unit = "Voucher Wyjątkowy Prezent ważny 36 miesięcy od daty zakupu zgodnie z regulaminem. "
        # ~12 tokens per unit, so 200 repetitions ≈ 2400 tokens, well above 500.
        body = (unit * 200).strip()
        chunks = _split_text_to_chunks(body, max_tokens=500, overlap_tokens=50)
        assert len(chunks) > 1
        for c in chunks:
            assert c.token_count > 0

    def test_chunk_indices_are_sequential(self):
        body = ("Para %d.\n\n" * 50) % tuple(range(50))
        chunks = _split_text_to_chunks(body, max_tokens=80)
        for i, c in enumerate(chunks):
            assert c.index == i


class TestRealKbDocument:
    def test_regulamin_sample(self):
        # Snippet from KB-001 — verifies chunker handles a real frontmatter-stripped doc.
        body = (
            "## 1. Ważność Vouchera\n\n"
            "- 12 miesięcy realizacji rekomendowanego przeżycia, liczone od daty zakupu.\n"
            "- +24 miesiące ochrony środków na Gift Card po wygaśnięciu okresu realizacji.\n"
            "- Łącznie 36 miesięcy od zakupu.\n"
            "- Po 36 miesiącach środki przepadają bezpowrotnie.\n\n"
            "## 2. Wymiana Vouchera\n\n"
            "- Klient może wymienić Voucher na inne przeżycie z aktualnej oferty.\n"
        )
        chunks = _split_text_to_chunks(body, max_tokens=500, overlap_tokens=50)
        assert len(chunks) >= 1
        joined = "\n\n".join(c.content for c in chunks)
        assert "36 miesięcy" in joined
        assert "Gift Card" in joined
