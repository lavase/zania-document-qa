from fastapi import FastAPI, File, HTTPException, UploadFile

from app.chunking import chunk_documents
from app.document_parser import parse_json_document, parse_pdf
from app.qa_service import answer_question
from app.question_parser import parse_questions
from app.retrieval import build_index, retrieve
import asyncio

import json
import logging
import time

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_QUESTIONS = 50
MAX_CONCURRENT_QUESTIONS = 5

app = FastAPI(
    title="Zania Document QA API",
    description="Answer questions using information from uploaded documents.",
    version="1.0.0",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

logger = logging.getLogger(__name__)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/qa")
async def answer_questions(
    questions_file: UploadFile = File(...),
    document_file: UploadFile = File(...),
):
    start_time = time.time()
    questions_filename = questions_file.filename.lower()
    document_filename = document_file.filename.lower()

    if not questions_filename.endswith(".json"):
        raise HTTPException(
            status_code=400,
            detail="Questions file must be a JSON file.",
        )

    if not document_filename.endswith((".pdf", ".json")):
        raise HTTPException(
            status_code=400,
            detail="Document file must be either PDF or JSON.",
        )

    questions_content = await questions_file.read()
    document_content = await document_file.read()

    if len(questions_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Questions file is too large.",
        )

    if len(document_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Document file is too large.",
        )

    try:
        questions = parse_questions(questions_content)

        if len(questions) > MAX_QUESTIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {MAX_QUESTIONS} questions are allowed per request.",
            )

        if document_filename.endswith(".pdf"):
            documents = parse_pdf(document_content)
        else:
            documents = parse_json_document(document_content)

        chunks = chunk_documents(documents)

        if not chunks:
            raise ValueError("No usable document content found.")

        index = build_index(chunks)

        semaphore = asyncio.Semaphore(MAX_CONCURRENT_QUESTIONS)

        async def process_question(question: str):
            async with semaphore:
                relevant_chunks = await asyncio.to_thread(
                    retrieve,
                    question,
                    chunks,
                    index,
                )

                return await asyncio.to_thread(
                    answer_question,
                    question,
                    relevant_chunks,
                )


        results = await asyncio.gather(
            *(process_question(question) for question in questions)
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        logger.info(
            json.dumps(
                {
                    "event": "qa_request_completed",
                    "questions_count": len(questions),
                    "document": document_file.filename,
                    "chunks_count": len(chunks),
                    "latency_ms": latency_ms,
                }
            )
        )

        return {
            "results": results,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print(f"Unexpected error: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Failed to process the request.",
        ) from exc