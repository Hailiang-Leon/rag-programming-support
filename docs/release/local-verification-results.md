# RC1 Local Verification Results

## Verification identity

| Field | Value |
|---|---|
| Verification date | 2026-07-22 |
| Source branch | `chore/release-readiness` |
| Product commit tested by clean clone | `91552e96f86eb3042f05ba3e9fed4b584851e0b9` |
| Product commit subject | `Prepare RC1 and record release evaluation` |
| Source repository | `/Users/liuhailiang/Desktop/NCI/Project/rag-programming-support` |
| Clean-clone location | `/Users/liuhailiang/Desktop/NCI/Project/rag-programming-support-rc-clean` |
| Clone method | `git clone --no-local` |
| Push or tag performed | No |

The clean clone resolved to the exact product commit shown above and initially had a clean tracked working tree. This document was added afterward as verification evidence; its documentation commit is not the commit that underwent the clean-clone exercise.

## Clean environment and dependency installation

A new virtual environment was created in the clean clone with Python 3.14.5. The environment was not copied from the source repository.

```text
python3 -m venv .venv
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pip check
```

Result:

```text
Dependency installation: PASS
pip check: No broken requirements found.
```

The first installation was unusually slow because package downloads were bandwidth-limited. The largest individual package was the 111.2 MB PyTorch wheel, which took 59 minutes 15 seconds at an average reported rate of 16.7 kB/s. Installation nevertheless completed successfully with compatible macOS arm64 / Python 3.14 wheels. No requirements change or reuse of the source repository's `.venv` was needed.

## Ollama model

`ollama list` confirmed that the configured local model was available:

```text
qwen3:4b-instruct    0edcdef34593    2.5 GB
```

## Ingestion and vector-store reconstruction

The clean clone began without generated `chunks.json`, ChromaDB files, or a query-log database. The tracked `data/raw` directory contained six programming source documents.

Commands:

```text
python -m src.backend.ingestion.document_loader
python -m src.backend.rag.vector_store
```

Results:

```text
Document ingestion completed.
Documents processed: 6
Chunks created: 29
Output file: data/processed/chunks.json

Vector store build completed.
Collection: programming_sources
Chunks stored: 29
Persist directory: data/processed/chroma_db
Embedding model: all-MiniLM-L6-v2
```

The vector-store command's test query, `What is a variable in Python?`, retrieved `python_variables.txt_chunk_001` at rank 1.

## Automated regression

The full test suite was run with the clean clone's Python environment and newly reconstructed data:

```text
41 passed
0 failed
2 third-party warnings
```

The warnings were the existing Starlette TestClient deprecation warning and the ChromaDB `asyncio.iscoroutinefunction` deprecation warning.

## API and frontend smoke test

The clean-clone service was started independently on port 8002:

```text
python -m uvicorn src.backend.api.main:app --port 8002
```

Observed responses:

| Request | Result |
|---|---|
| `GET http://127.0.0.1:8002/health` | HTTP 200; `status: ok` |
| `GET http://127.0.0.1:8002/` | HTTP 200; `text/html; charset=utf-8` |
| `GET http://127.0.0.1:8002/static/app.js` | HTTP 200; `text/javascript; charset=utf-8` |
| `HEAD http://127.0.0.1:8002/` | HTTP 405; `Allow: GET` |
| `HEAD http://127.0.0.1:8002/static/app.js` | HTTP 200 |

The root HEAD response is explained by the application declaring a GET route rather than a HEAD route. The browser-relevant GET request returned the frontend successfully, so this did not prevent static frontend serving.

## Real Ollama request

The following request was made against the clean clone:

```text
POST http://127.0.0.1:8002/ask
query: What is a variable in Python?
top_k: 3
response_mode: answer
hint_level: 1
```

Result:

```text
HTTP status: 200
answer_status: answered
answer completion: PASS
citation markers: [S1], [S2]
returned sources: 3
source-card data: PASS
```

The answer correctly explained variables, assignment, common value types, and displaying a variable. It was complete and not truncated. Returned sources included the relevant `python_variables.txt` chunks.

## Database and repository isolation

The smoke request created a query-log database inside the clean clone. The generated database files were compared with the source repository files:

| File | Clean-clone inode | Source-repository inode | Isolation result |
|---|---:|---:|---|
| `data/processed/chroma_db/chroma.sqlite3` | 67623467 | 65395176 | PASS |
| `data/evaluation/query_logs.sqlite3` | 67624234 | 66271347 | PASS |

The clean-clone files also had different sizes from the source-repository files. All generated data, `.env`, and `.venv` paths were ignored by Git, and the clean clone retained a clean tracked working tree at the tested commit.

## Cleanup and remaining manual check

The port 8002 service was stopped after smoke testing and a follow-up connection attempt failed as expected. The original repository's port 8000 health endpoint remained available and returned `status: ok`.

Static implementation safety is covered by the automated test that verifies `textContent` and `createTextNode()` are used and `innerHTML` is absent. The following execution check remains pending because no interactive browser session was available:

```html
<script>alert("test")</script>
```

The browser test must confirm that no alert appears, the page is not modified, the input is displayed only as text, and no injected script executes. No product change is required for this pending manual evidence item.
