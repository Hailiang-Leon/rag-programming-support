# RC1 Acceptance Checklist

## Verification boundary

**Product commit tested by clean clone:**
`91552e96f86eb3042f05ba3e9fed4b584851e0b9`

This checklist was recorded after the clean-clone exercise. The later evidence-only documentation commit does not change product behaviour and must not be confused with the product commit identified above.

## Release-candidate checks

| Check | Result | Evidence |
|---|---|---|
| Product commit available locally | PASS | `91552e96f86eb3042f05ba3e9fed4b584851e0b9` (`Prepare RC1 and record release evaluation`) |
| Clean clone created with `--no-local` | PASS | `/Users/liuhailiang/Desktop/NCI/Project/rag-programming-support-rc-clean` resolved to the tested product commit |
| Clean virtual environment | PASS | A new Python 3.14.5 `.venv` was created inside the clean clone |
| Dependency installation | PASS | `pip install -r requirements.txt` completed and `pip check` reported no broken requirements |
| Source-document ingestion | PASS | 6 documents processed into 29 chunks |
| Vector-store reconstruction | PASS | 29 chunks stored in the `programming_sources` collection |
| Automated regression | PASS | 41 passed, 0 failed, 2 third-party warnings |
| API startup | PASS | Clean-clone service started on `127.0.0.1:8002` |
| Health endpoint | PASS | `GET /health` returned HTTP 200 and `status: ok` |
| Frontend root | PASS | `GET /` returned HTTP 200 with `text/html` |
| Frontend JavaScript | PASS | `GET /static/app.js` returned HTTP 200 with `text/javascript` |
| Real Ollama request | PASS | `POST /ask` returned HTTP 200, `answer_status=answered`, a complete answer, valid citations, and three sources |
| Local-data isolation | PASS | Clean-clone ChromaDB and query-log SQLite files had different inodes and sizes from the original repository files |
| Clean-clone shutdown | PASS | Port 8002 was stopped after verification |
| HTML/script static implementation | PASS | Automated test confirms use of `textContent` and `createTextNode()` and absence of `innerHTML` |
| HTML/script browser execution | PENDING | Manual browser entry of `<script>alert("test")</script>` has not yet been performed |

## Observations and accepted limitations

- First-time dependency installation succeeded but was slow because of network throughput and large ML wheels. The 111.2 MB PyTorch wheel alone took 59 minutes 15 seconds to download. This was an installation-time observation, not a dependency or product failure.
- `HEAD /` returned HTTP 405 with `Allow: GET` because the FastAPI root route only declares GET. The browser-relevant `GET /` request returned HTTP 200, so static frontend serving passed.
- When Ollama is unavailable, the system detects the model-service failure but currently returns HTTP 500 rather than a structured learner-friendly recovery response.
- The local model can occasionally reveal the essential solution in a Level-2 hint despite explicit staged-hint instructions. The deterministic Level-1 hint remains the final demonstration path.

## RC1 acceptance summary

The tested product commit passed clean installation, dependency validation, ingestion and vector-store reconstruction, automated regression, API startup, real local-model generation, static frontend serving, and local database-isolation checks. Product logic remains frozen. The only outstanding manual acceptance item is browser execution of the HTML/script-like input test.
