from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_qa_endpoint_with_mocked_dependencies(monkeypatch):
    # Avoid real embedding/API calls.
    monkeypatch.setattr(
        "app.main.build_index",
        lambda chunks: [[0.1, 0.2] for _ in chunks],
    )

    monkeypatch.setattr(
        "app.main.retrieve",
        lambda question, chunks, index: [
            {
                "text": "root.cloud_provider: AWS",
                "source": "root.cloud_provider",
                "page": None,
                "score": 0.9,
            }
        ],
    )

    monkeypatch.setattr(
        "app.main.answer_question",
        lambda question, context_chunks: {
            "question": question,
            "answer": "AWS",
            "sources": context_chunks,
        },
    )

    questions_file = (
        "questions.json",
        b'["Which cloud providers do you rely on?"]',
        "application/json",
    )

    document_file = (
        "document.json",
        b'{"cloud_provider": "AWS"}',
        "application/json",
    )

    response = client.post(
        "/qa",
        files={
            "questions_file": questions_file,
            "document_file": document_file,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["results"]) == 1
    assert data["results"][0]["answer"] == "AWS"