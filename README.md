# Zania Document QA

A document question-answering service built for the Zania coding challenge.

The application accepts:

- A JSON file containing a list of questions
- A PDF or JSON source document

It retrieves the most relevant document content and uses `gpt-4o-mini` to generate grounded answers with source citations.

## Features

- FastAPI backend
- PDF and JSON document support
- Multiple questions per request
- OpenAI embeddings for semantic retrieval
- In-memory cosine-similarity search using NumPy
- Grounded answers using `gpt-4o-mini`
- Source citations
- Explicit `Not found in the provided document.` behavior for unsupported answers
- Concurrent question processing with bounded concurrency
- Input validation and request limits
- Unit and integration tests
- Structured JSON logging
- Dockerfile for containerized execution

## Architecture

```text
Questions JSON + PDF/JSON Document
                |
                v
          FastAPI /qa
                |
                v
         Input Validation
                |
                v
        Document Parsing
          /           \
        PDF           JSON
          \           /
           Normalized Text
                |
                v
         Text Chunking
                |
                v
       OpenAI Embeddings
                |
                v
    In-Memory Vector Retrieval
       (Cosine Similarity)
                |
                v
       Relevant Context
                |
                v
         gpt-4o-mini
                |
                v
   Answers + Source Citations
```

## Requirements

- Python 3.11+
- OpenAI API key

## Setup

Clone the repository:

```bash
git clone <YOUR_REPOSITORY_URL>
cd zania-document-qa
```

Create a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file:

```text
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

The `.env` file is excluded from Git and must not be committed.

## Run the API

```bash
python -m uvicorn app.main:app --reload
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

## QA API

### Endpoint

```text
POST /qa
```

The request expects two multipart file uploads:

- `questions_file`: JSON
- `document_file`: PDF or JSON

### Example questions file

```json
[
  "Which cloud providers do you rely on?",
  "Where is the service hosted?",
  "What is the annual revenue?"
]
```

### Example JSON document

```json
{
  "company": "Example Corp",
  "cloud_provider": "AWS",
  "hosting": {
    "primary_region": "us-west-2",
    "backup_region": "us-east-1"
  }
}
```

### Example response

```json
{
  "results": [
    {
      "question": "Which cloud providers do you rely on?",
      "answer": "AWS",
      "sources": [
        {
          "source": "root.cloud_provider",
          "page": null,
          "score": 0.4763,
          "text": "root.cloud_provider: AWS"
        }
      ]
    },
    {
      "question": "What is the annual revenue?",
      "answer": "Not found in the provided document.",
      "sources": []
    }
  ]
}
```

## Retrieval Strategy

The application:

1. Parses the source document
2. Splits the content into overlapping chunks
3. Generates embeddings using `text-embedding-3-small`
4. Stores embeddings in memory for the lifetime of the request
5. Embeds each question
6. Computes cosine similarity using NumPy
7. Retrieves the top relevant chunks
8. Sends only those chunks to `gpt-4o-mini`

The document embeddings are generated once per request and reused for all questions.

For this challenge, an in-memory similarity search was chosen instead of an external vector database because documents are processed per request and the expected scale is small. This keeps the service easy to run and reduces operational complexity while preserving the retrieval behavior expected from a RAG system.

## Grounding

The model is instructed to answer only from the retrieved document context.

If the provided document does not contain enough information to support an answer, the API returns:

```text
Not found in the provided document.
```

This reduces hallucination and makes unsupported answers explicit.

## Concurrency

Questions within the same request are processed concurrently.

Blocking embedding and LLM operations are moved to worker threads using `asyncio.to_thread`.

A semaphore limits the number of concurrently processed questions to avoid excessive API calls.

## Validation and Limits

The API validates:

- Questions file must be JSON
- Document file must be PDF or JSON
- Malformed JSON
- Empty question lists
- Empty questions
- Excessive question counts
- Excessive upload size
- Documents with no readable content

These limits help prevent unexpectedly expensive or resource-heavy requests.

## Tests

Run:

```bash
pytest -v
```

The test suite includes:

- Question parser unit tests
- Invalid input tests
- Health endpoint test
- Backend integration test with mocked retrieval and LLM dependencies

The integration test avoids making real OpenAI API calls.

## Docker

Build:

```bash
docker build -t zania-document-qa .
```

Run:

```bash
docker run --env-file .env -p 8000:8000 zania-document-qa
```

Then open:

```text
http://127.0.0.1:8000/docs
```

The Docker configuration is included for reproducible execution. It was not locally exercised on the development machine because Docker was not installed there.

## Observability

Completed QA requests produce structured JSON logs including:

- Number of questions
- Document name
- Number of chunks
- Request latency

Example:

```json
{
  "event": "qa_request_completed",
  "questions_count": 3,
  "document": "sample_document.json",
  "chunks_count": 4,
  "latency_ms": 1820.41
}
```

## Design Decisions

### Why FastAPI?

FastAPI provides:

- Async request handling
- File upload support
- Built-in request validation
- Automatic OpenAPI documentation
- Simple integration testing

### Why request-scoped retrieval?

Documents are indexed only for the lifetime of each request.

This avoids introducing unnecessary persistence, document lifecycle management, cleanup, or stale indexes for a coding challenge centered on uploaded documents.

### Why NumPy instead of an external VectorDB?

For the expected document sizes in this challenge, in-memory cosine similarity is sufficient and simpler to operate.

At larger scale, the retrieval layer could be replaced by FAISS, Pinecone, pgvector, OpenSearch, or another vector database without changing the API contract.

## Possible Future Improvements

- Persistent document indexing
- Hybrid semantic + keyword retrieval
- More precise citation selection
- Token-aware chunking
- Streaming responses
- Request authentication
- Metrics export
- Larger-scale vector database
- Minimal web client for file upload and result display