import pytest

from app.question_parser import parse_questions


def test_parse_string_questions():
    content = b'["What is AWS?", "Where is the service hosted?"]'

    result = parse_questions(content)

    assert result == [
        "What is AWS?",
        "Where is the service hosted?",
    ]


def test_parse_question_objects():
    content = b'[{"question": "What is AWS?"}]'

    result = parse_questions(content)

    assert result == ["What is AWS?"]


def test_invalid_json():
    with pytest.raises(ValueError, match="Invalid questions JSON file"):
        parse_questions(b"{invalid json}")


def test_questions_must_be_list():
    with pytest.raises(ValueError, match="Questions JSON must contain a list"):
        parse_questions(b'{"question": "What is AWS?"}')


def test_empty_question_rejected():
    with pytest.raises(ValueError, match="Questions cannot be empty"):
        parse_questions(b'["   "]')