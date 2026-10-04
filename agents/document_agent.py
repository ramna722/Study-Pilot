"""
agents/document_agent.py -- the DOCUMENT AGENT

Job: turn uploaded study material into text chunks for downstream agents.

Supported input:
  - plain text strings
  - paths to .txt/.md/.pdf files
  - file-like objects such as Streamlit uploads

Output chunks contain the extracted text plus source metadata. The Topic Agent
only needs the ``text`` field, while later agents can use page and source.
"""
from pathlib import Path
import io
import re


DEFAULT_CHUNK_SIZE = 1800


def _decode_text(data):
    """Decode text bytes without failing on a small amount of bad encoding."""
    return data.decode("utf-8-sig", errors="replace") if isinstance(data, bytes) else str(data)


def _read_text_source(source):
    """Return ``(text, source_name)`` for a text input or uploaded file."""
    if isinstance(source, str):
        possible_path = Path(source)
        if possible_path.is_file():
            return possible_path.read_text(encoding="utf-8-sig", errors="replace"), possible_path.name
        return source, "uploaded-text"

    if isinstance(source, Path):
        return source.read_text(encoding="utf-8-sig", errors="replace"), source.name

    if hasattr(source, "getvalue"):
        data = source.getvalue()
        name = getattr(source, "name", "uploaded-text")
    elif hasattr(source, "read"):
        data = source.read()
        name = getattr(source, "name", "uploaded-text")
    else:
        raise TypeError("source must be text, a file path, or a file-like object")
    return _decode_text(data), Path(name).name


def _extract_pdf(source):
    """Extract one text string per PDF page, preserving page boundaries."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ImportError("PDF support requires the 'pypdf' package") from exc

    if isinstance(source, (str, Path)):
        reader = PdfReader(str(source))
        source_name = Path(source).name
    else:
        if hasattr(source, "getvalue"):
            source = io.BytesIO(source.getvalue())
        reader = PdfReader(source)
        source_name = Path(getattr(source, "name", "uploaded.pdf")).name

    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((text, page_number, source_name))
    return pages


def _split_text(text, max_chars):
    """Split text on paragraph boundaries, then hard-wrap oversized paragraphs."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    for paragraph in paragraphs:
        while len(paragraph) > max_chars:
            cut = paragraph.rfind(" ", 0, max_chars + 1)
            cut = cut if cut > 0 else max_chars
            chunks.append(paragraph[:cut].strip())
            paragraph = paragraph[cut:].strip()
        if paragraph:
            chunks.append(paragraph)
    return chunks


def extract_chunks(source, max_chars=DEFAULT_CHUNK_SIZE):
    """Extract non-empty, bounded chunks from text or a PDF source."""
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1")

    name = getattr(source, "name", str(source))
    suffix = Path(name).suffix.lower()
    if suffix == ".pdf":
        pages = _extract_pdf(source)
    else:
        text, source_name = _read_text_source(source)
        pages = [(text, None, source_name)]

    chunks = []
    for page_text, page_number, source_name in pages:
        for text in _split_text(page_text, max_chars):
            chunk = {"text": text, "source": source_name}
            if page_number is not None:
                chunk["page"] = page_number
            chunks.append(chunk)
    if not chunks:
        raise ValueError("Document Agent found no readable text")
    return chunks


def document_agent_node(state, source=None, max_chars=DEFAULT_CHUNK_SIZE):
    """Read ``source`` and write chunks into the shared workflow state."""
    if source is None:
        source = state.get("document") or state.get("file")
    if source is None:
        raise ValueError("state has no document source")
    state["chunks"] = extract_chunks(source, max_chars=max_chars)
    return state