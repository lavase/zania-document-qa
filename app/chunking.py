def chunk_documents(
    documents: list[dict],
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[dict]:
    chunks = []

    for document in documents:
        text = document["text"]

        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    {
                        "text": chunk_text,
                        "source": document["source"],
                        "page": document.get("page"),
                    }
                )

            if end >= len(text):
                break

            start = end - overlap

    return chunks