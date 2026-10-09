import io
import json
from typing import Any

from pypdf import PdfReader


def parse_pdf(content: bytes) -> list[dict]:
    reader = PdfReader(io.BytesIO(content))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        text = text.strip()

        if text:
            pages.append(
                {
                    "text": text,
                    "source": f"page {page_number}",
                    "page": page_number,
                }
            )

    if not pages:
        raise ValueError("No readable text found in PDF.")

    return pages


def _flatten_json(value: Any, path: str = "root") -> list[dict]:
    results = []

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            results.extend(_flatten_json(child, child_path))

    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            results.extend(_flatten_json(child, child_path))

    else:
        results.append(
            {
                "text": f"{path}: {value}",
                "source": path,
                "page": None,
            }
        )

    return results


def parse_json_document(content: bytes) -> list[dict]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid document JSON file.") from exc

    chunks = _flatten_json(data)

    if not chunks:
        raise ValueError("JSON document is empty.")

    return chunks