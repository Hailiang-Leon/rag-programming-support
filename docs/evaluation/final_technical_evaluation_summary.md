# Final Technical Evaluation Summary

## Evaluation overview

The same 12-question technical evaluation set was used to evaluate the baseline and optimized system configurations. To support a fair comparison, the baseline responses were rescored using the same rubric and evaluator standard as the final responses.

| Configuration | Baseline | Final |
|---|---:|---:|
| Model | `qwen3:4b-thinking` | `qwen3:4b-instruct` |
| Evaluation type | `baseline_technical_evaluation` | `final_technical_evaluation` |
| Questions completed | 12 | 12 |
| Overall behavioural passes | 10/12 | 12/12 |
| Behavioural pass rate | 83.3% | 100.0% |
| Average recorded latency | 69.12s | 28.97s |
| Median recorded latency | 76.99s | 33.24s |
| Top K | 3 | 3 |
| Minimum similarity score | 0.35 | 0.35 |

## Manual scoring comparison

| Metric | Baseline score | Baseline % | Final score | Final % | Change |
|---|---:|---:|---:|---:|---:|
| Retrieval relevance | 18/20 | 90.0% | 19/20 | 95.0% | +5.0 pp |
| Answer faithfulness | 20/24 | 83.3% | 21/24 | 87.5% | +4.2 pp |
| Citation accuracy | 12/20 | 60.0% | 10/20 | 50.0% | -10.0 pp |
| Novice readability | 23/24 | 95.8% | 20/24 | 83.3% | -12.5 pp |
| Refusal appropriateness | 3/4 | 75.0% | 4/4 | 100.0% | +25.0 pp |
| Staged hint quality | 0/2 | 0.0% | 2/2 | 100.0% | +100.0 pp |

## Key behavioural outcomes

- Q007 changed from `answered` to `hint` and returned a deterministic level-1 hint without revealing the complete solution. The hint included a citation marker, although citation-source alignment remains a limitation.
- Q012 changed from `insufficient_evidence` to `out_of_scope` and explicitly identified the medical request as outside the introductory programming support scope.
- Q011 continued to avoid unsupported claims by returning `insufficient_evidence`.
- The final run completed all 12 questions with 0 runner errors.

## Interpretation

The optimized system achieved a 12/12 behavioural pass rate, compared with the baseline result. The most important improvements were staged-hint behaviour and explicit scope-aware refusal.

Not all manual quality dimensions improved. Citation accuracy and novice readability decreased because of citation-source mismatches and responses that reached the configured output-token limit.

The final result should be interpreted as a comparison between complete system configurations, not as a controlled prompt-only experiment. The baseline used `qwen3:4b-thinking`, while the final configuration used `qwen3:4b-instruct` together with updated hint, refusal, prompt, and runtime logic.

## Remaining limitations

- Several generated answers reached the configured `num_predict=256` limit and ended before completing the final sentence or Markdown structure.
- Citation precision remains inconsistent. In particular, Q006 and Q007 cited S1 even though another retrieved source more directly supported the accumulator or running-total claim.
- Q006 did not retrieve the strongest available accumulator-pattern chunk within the top three results.
- CLI latency includes repeated embedding-model initialization and therefore does not fully represent a persistent FastAPI service session.

## Conclusion

The final evaluation demonstrates that the system meets the expected behaviour for all 12 test cases, including normal explanations, debugging support, staged hints, insufficient-evidence handling, and out-of-scope refusal. However, citation alignment, retrieval ranking, response completion, and runtime performance remain areas for future improvement.
