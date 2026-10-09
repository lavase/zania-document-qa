import json
from typing import List


def parse_questions(content: bytes) -> List[str]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid questions JSON file.") from exc

    if not isinstance(data, list):
        raise ValueError("Questions JSON must contain a list.")

    questions = []

    for item in data:
        if isinstance(item, str):
            question = item.strip()

        elif isinstance(item, dict) and isinstance(item.get("question"), str):
            question = item["question"].strip()

        else:
            raise ValueError(
                "Each question must be a string or an object with a 'question' field."
            )

        if not question:
            raise ValueError("Questions cannot be empty.")

        questions.append(question)

    if not questions:
        raise ValueError("Questions file must contain at least one question.")

    return questions