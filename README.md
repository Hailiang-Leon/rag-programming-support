# RAG Programming Support System

## Project Title

Designing and Evaluating a Source-Grounded AI Support System for Introductory Programming Learners: A Retrieval-Augmented Generation Approach

## Project Overview

This project develops a web-based source-grounded AI support system for introductory programming learners. The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from programming learning materials and technical documentation before generating responses.

The system is designed to support novice learners by providing citation-supported explanations, staged hints, and uncertainty-aware responses. Instead of acting as a general-purpose chatbot, the system grounds answers in retrieved sources and makes answer limitations visible to the learner.

## Main Features

- Learner-facing programming question interface
- Document ingestion pipeline for programming materials
- Vector-based document retrieval
- RAG-based answer generation
- Citation-supported explanations
- Learner-facing web interface with citation and source evidence display
- Uncertainty and refusal handling when source evidence is insufficient
- Persistent query, answer status, generated answer, and retrieved source metadata logging using SQLite

## Planned Technology Stack

- Backend: Python, FastAPI
- Frontend: JavaScript / React or simple web interface
- Retrieval: ChromaDB
- Embeddings: Sentence Transformers
- LLM: Ollama local model
- Testing: pytest
- Version control: Git and GitHub

## Project Structure

```text
docs/
  proposal/
  srs/
  interim-report/
  diagrams/

data/
  raw/
  processed/
  evaluation/

src/
  backend/
    api/
    rag/
    ingestion/
    storage/
  frontend/

tests/
  unit/
  integration/

notebooks/
```

## Evaluation Plan

The system will be evaluated using technical and learner-facing criteria, including:

- Retrieval relevance
- Citation accuracy
- Answer faithfulness
- Unsupported claim reduction
- Refusal appropriateness
- Novice readability
- Learner perceptions of usefulness, clarity, and trustworthiness

## Status

Core RAG prototype completed. The system currently includes document ingestion, ChromaDB retrieval, source-grounded answer generation, citation display, SQLite logging, a learner-facing frontend, automated tests, and a baseline technical evaluation.

## Running the Backend API

Activate the Python virtual environment:

```bash
source .venv/bin/activate
```

Start the FastAPI backend from the project root:

```bash
python -m uvicorn src.backend.api.main:app --reload --reload-dir src --host 127.0.0.1 --port 8000
```

Available local endpoints:

- Root endpoint: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health
- API documentation: http://127.0.0.1:8000/docs

---

## Local Development

### 1. Activate the virtual environment

```bash
source .venv/bin/activate
```

### 2. Confirm the local Ollama model

This project uses a local Ollama model for answer generation. Set `OLLAMA_MODEL` to a model installed on the local machine. The current baseline technical evaluation used `qwen3:4b-thinking`.

Example:

```env
OLLAMA_MODEL=qwen3:4b-instruct
OLLAMA_BASE_URL=http://localhost:11434
```

Check available local models:

```bash
ollama list
```

Check that the Ollama API is running:

```bash
curl http://localhost:11434/api/tags
```

If Ollama is not running, start it with:

```bash
ollama serve
```

### 3. Start the FastAPI backend

```bash
uvicorn src.backend.api.main:app --reload
```

The API documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### GET `/health`

Checks whether the backend is running.

Example:

```bash
curl http://127.0.0.1:8000/health
```

Example response:

```json
{
  "status": "ok",
  "app_name": "RAG Programming Support System",
  "environment": "development"
}
```

---

### POST `/retrieve`

Retrieves relevant source chunks from the ChromaDB vector store for a learner programming question.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is a variable in Python?",
    "top_k": 3
  }'
```

Example response format:

```json
{
  "query": "What is a variable in Python?",
  "chunks_returned": 3,
  "results": [
    {
      "rank": 1,
      "chunk_id": "python_variables.txt_chunk_001",
      "source": "python_variables.txt",
      "text_preview": "Python Variables...",
      "distance": 0.2402,
      "similarity_score": 0.7598
    }
  ]
}
```

---

### POST `/ask`

Generates a source-grounded answer using retrieved chunks and the local Ollama model.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is a variable in Python?",
    "top_k": 3
  }'
```

Example response format:

```json
{
  "query": "What is a variable in Python?",
  "answer_status": "answered",
  "answer": "A variable in Python is a name used to store a value in a program [S1].",
  "sources": [
    {
      "source_id": "S1",
      "chunk_id": "python_variables.txt_chunk_001",
      "source": "python_variables.txt",
      "similarity_score": 0.7598,
      "text_preview": "Python Variables..."
    }
  ]
}
```

---

## Insufficient Evidence Handling

The `/ask` endpoint supports insufficient evidence handling. If retrieved chunks do not meet the required similarity threshold, the system returns an uncertainty response instead of generating an unsupported answer.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What will be on my final exam?",
    "top_k": 3,
    "min_similarity_score": 0.75
  }'
```

Example response:

```json
{
  "query": "What will be on my final exam?",
  "answer_status": "insufficient_evidence",
  "answer": "I do not have enough source evidence to answer this question reliably.",
  "sources": []
}
```

---

## Current Project Status

The current software prototype supports:

- Document ingestion and chunking
- Sentence-transformer embeddings
- ChromaDB vector storage and retrieval
- POST `/retrieve` endpoint
- Local Ollama source-grounded answer generation
- POST `/ask` endpoint
- Citation markers and retrieved source evidence
- Insufficient-evidence handling
- Learner-facing HTML, CSS, and JavaScript frontend
- Citation badges and source cards in the frontend
- Persistent SQLite query and answer logging
- Automated unit and integration tests
- A completed 12-question baseline technical evaluation

The baseline evaluation achieved a 10/12 overall pass result, with an
83.3% pass rate. Current improvement work focuses on true staged hint
delivery, scope-aware refusal, response quality, and final evaluation.

## Final Technical Evaluation

The optimized system was evaluated using the same 12-question technical
evaluation set as the baseline system.

- Baseline behavioural pass rate: **10/12 (83.3%)**
- Final behavioural pass rate: **12/12 (100.0%)**
- Baseline average recorded latency: **69.12 seconds**
- Final average recorded latency: **28.97 seconds**
- Staged hint quality improved from **0% to 100%**
- Refusal appropriateness improved from **75% to 100%**

The baseline used `qwen3:4b-thinking`, while the optimized configuration
used `qwen3:4b-instruct` together with deterministic level-1 hints,
scope-aware refusal, and updated runtime settings.

Remaining limitations include citation-source alignment, retrieval ranking,
responses reaching the configured output-token limit, and local runtime
performance.

See the
[Final Technical Evaluation Summary](docs/evaluation/final_technical_evaluation_summary.md)
for the complete results and interpretation.
