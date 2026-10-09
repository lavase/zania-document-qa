import numpy as np
from openai import OpenAI

from app.config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


def create_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )

    return response.data[0].embedding


def build_index(chunks: list[dict]) -> list[list[float]]:
    embeddings = []

    for chunk in chunks:
        embedding = create_embedding(chunk["text"])
        embeddings.append(embedding)

    return embeddings


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    a = np.array(vector_a, dtype=np.float32)
    b = np.array(vector_b, dtype=np.float32)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)


def retrieve(
    question: str,
    chunks: list[dict],
    index: list[list[float]],
    top_k: int = 4,
) -> list[dict]:
    question_embedding = create_embedding(question)

    scored_chunks = []

    for chunk, chunk_embedding in zip(chunks, index):
        score = cosine_similarity(
            question_embedding,
            chunk_embedding,
        )

        scored_chunks.append((score, chunk))

    scored_chunks.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    results = []

    for score, chunk in scored_chunks[:top_k]:
        result = chunk.copy()
        result["score"] = round(score, 4)
        results.append(result)

    return results
