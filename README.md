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
- Staged hint generation
- Uncertainty and refusal handling when source evidence is insufficient
- Query, retrieval, answer, and feedback logging for evaluation

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

Initial project structure created.

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
- Configuration check: http://127.0.0.1:8000/config-check
- API documentation: http://127.0.0.1:8000/docs
