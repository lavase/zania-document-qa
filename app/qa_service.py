from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL


client = OpenAI(api_key=OPENAI_API_KEY)


def answer_question(
    question: str,
    context_chunks: list[dict],
) -> dict:
    context = "\n\n".join(
        f"[Source: {chunk['source']}]\n{chunk['text']}"
        for chunk in context_chunks
    )

    prompt = f"""
You are answering questions using only the provided document context.

Rules:
- Use only the supplied context.
- Do not use outside knowledge.
- If the answer is not supported by the context, respond exactly:
  "Not found in the provided document."
- Keep the answer concise and factual.

Question:
{question}

Context:
{context}
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content.strip()

    sources = []

    if answer != "Not found in the provided document.":
        sources = [
            {
                "source": chunk["source"],
                "page": chunk.get("page"),
                "score": chunk.get("score"),
                "text": chunk["text"][:300],
            }
            for chunk in context_chunks
        ]

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
    }