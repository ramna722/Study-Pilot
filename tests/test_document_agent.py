"""Tests for the Document Agent. No API key is needed."""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from agents.document_agent import document_agent_node, extract_chunks


def test_text_is_split_and_metadata_is_preserved():
    chunks = extract_chunks("First paragraph.\n\nSecond paragraph.", max_chars=100)

    assert [chunk["text"] for chunk in chunks] == ["First paragraph.", "Second paragraph."]
    assert all(chunk["source"] == "uploaded-text" for chunk in chunks)


def test_long_paragraphs_are_bounded():
    chunks = extract_chunks("one two three four five six", max_chars=10)

    assert all(len(chunk["text"]) <= 10 for chunk in chunks)
    assert " ".join(chunk["text"] for chunk in chunks) == "one two three four five six"


def test_file_like_input_and_shared_state():
    state = document_agent_node({"document": io.BytesIO(b"Uploaded notes")})

    assert state["chunks"] == [{"text": "Uploaded notes", "source": "uploaded-text"}]


@pytest.mark.parametrize("bad_size", [0, -1])
def test_invalid_chunk_size_is_rejected(bad_size):
    with pytest.raises(ValueError, match="max_chars"):
        extract_chunks("notes", max_chars=bad_size)