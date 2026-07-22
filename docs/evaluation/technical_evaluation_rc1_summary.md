# RC1 Technical Evaluation Summary

## Evaluation overview

The RC1 configuration was evaluated with the same 12-question test set and rubric used for the earlier technical evaluation. The run followed the product-freeze decision: no additional Level-2 prompt or recovery changes were made before evaluation.

| Configuration | RC1 result |
|---|---:|
| Model | `qwen3:4b-instruct` |
| Evaluation type | `rc1_technical_evaluation` |
| Questions completed | 12/12 |
| Runner errors | 0 |
| Overall behavioural passes | 12/12 |
| Behavioural pass rate | 100.0% |
| Average recorded latency | 27.42s |
| Median recorded latency | 30.49s |
| Top K | 3 |
| Minimum similarity score | 0.35 |
| `OLLAMA_NUM_PREDICT` | 384 |

The status distribution was nine `answered` responses, one `hint`, one `insufficient_evidence`, and one `out_of_scope` response.

## Manual rubric scores

| Metric | RC1 score | RC1 percentage |
|---|---:|---:|
| Retrieval relevance | 19/20 | 95.0% |
| Answer faithfulness | 23/24 | 95.8% |
| Citation accuracy | 17/20 | 85.0% |
| Novice readability | 23/24 | 95.8% |
| Refusal appropriateness | 4/4 | 100.0% |
| Staged hint quality | 2/2 | 100.0% |

## Key behavioural outcomes

- Q007 returned the deterministic Level-1 hint: one conceptual prompt and one guiding question, with no code or complete solution. Its `[S2]` citation directly mapped to the accumulator-pattern source.
- Q011 returned `insufficient_evidence` with no sources and did not guess about exam content.
- Q012 returned `out_of_scope` and redirected the medical request without offering medical advice.
- All 12 responses were complete; none showed the token truncation seen in the earlier 256-token run.
- Q006 correctly diagnosed overwriting and supplied `total = total + number`, but its retrieved top three did not contain the direct accumulator chunk. The answer cited S1 for the accumulator claim even though that retrieved chunk did not support it. This remains the main RC1 citation/retrieval weakness.
- Q003 was correct and complete, but its final S1 citation was less direct than the retrieved range source S2.

## E2E release-candidate checks

| Check | Result | Evidence |
|---|---|---|
| Automated test suite | PASS | 41 passed, 0 failed, 2 third-party warnings |
| Level-1 deterministic hint | PASS | `answer_status=hint`; one concept sentence plus one question; no code; `[S2]` exists in sources and directly supports the running-total concept |
| Debugging question | PASS | Correct colon and `SyntaxError` explanation; complete response; all citation IDs mapped to returned sources |
| Ollama unavailable | PARTIAL / FAIL | Failure detection passed, but the independent wrong-port instance returned HTTP 500 with `Internal Server Error`; graceful user-facing recovery failed |
| HTML/script-like browser input | NOT EXECUTED | No interactive browser session was available in the evaluation environment, so this check must not be reported as a browser PASS without manual verification |

The wrong-port test instance on port 8001 was stopped after the check. The normal port 8000 instance was left unaffected during the evaluation.

## Critical analysis

The automated tests show that the intended prompt boundaries, input validation, security rules, and deterministic hint behaviour are present in the implementation and have not introduced regressions. They do not prove that a local generative model will obey every pedagogical instruction on every request.

This distinction is visible in the separately observed Level-2 behaviour. The response had `answer_status=hint`, was complete, and used valid citation IDs, but its supposed incomplete example already contained the core solution `total = total + number`. The surrounding TODO comment contradicted the runnable code. Therefore the Level-2 technical pathway and citation-ID mapping passed, while pedagogical staging failed and citation semantic alignment was only partial.

The Level-2 result should be recorded as a known model-compliance limitation rather than hidden by the automated test result:

```text
RC-04 Level-2 generative hint

Technical status: PASS
Hint response status: PASS
Pedagogical staging: PARTIAL / FAIL
Citation-ID mapping: PASS
Citation semantic alignment: PARTIAL

Known limitation:
The local model occasionally returned a complete solution despite
explicit staged-hint instructions.
```

The release demo should therefore use the stable deterministic Level-1 hint and should not demonstrate Level-2.

## Conclusion

RC1 completed the full 12-question evaluation with no runner errors and a 12/12 behavioural pass rate. The increased output budget removed the observed answer truncation, and the Level-1 source-selection change corrected the staged-hint citation from S1 to the directly supporting S2. Remaining limitations are the generative Level-2 staging failure, Q006 retrieval/citation mismatch, HTTP 500 recovery when Ollama is unavailable, and the still-pending manual browser check for script-like input.
