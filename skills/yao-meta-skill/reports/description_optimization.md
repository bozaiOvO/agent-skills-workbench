# Root Description Optimization

Winner: `Current`

- current tokens: `17`
- winner tokens: `17`
- baseline tokens: `8`

## Winner

创建、重构、评测和打包 Agent Skill。用于把工作流、文档或提示词做成可复用 Skill，并运行 `evals/` 质量验证。.

## Candidate Ranking

| Candidate | Tokens | Dev FP | Dev FN | Dev Near | Holdout FP | Holdout FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `Current` | 17 | 0 | 1 | 1.0 | 0 | 0 |
| `Minimal` | 41 | 1 | 1 | 1.0 | 0 | 0 |
| `Guardrail` | 56 | 1 | 1 | 1.0 | 0 | 0 |
| `Balanced` | 60 | 1 | 1 | 1.0 | 0 | 0 |
| `Artifact Aware` | 77 | 1 | 1 | 1.0 | 0 | 0 |
| `Boundary` | 83 | 1 | 1 | 1.0 | 0 | 0 |

## Acceptance Gates

| Gate | Winner FP | Winner FN | Current FP | Current FN | Baseline FP | Baseline FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Holdout | 0 | 0 | 0 | 0 | 0 | 0 |
| Blind Holdout | 0 | 0 | 0 | 0 | 0 | 0 |
| Judge Blind Holdout | 0 | 0 | 0 | 0 | 0 | 0 |
| Adversarial Holdout | 0 | 0 | 0 | 0 | 0 | 0 |

## Calibration

| Gate | Winner Gap | Winner Risk | Winner Boundary Rate | Current Gap | Baseline Gap |
| --- | ---: | --- | ---: | ---: | ---: |
| Holdout | 0.491 | healthy | 0.0 | 0.491 | 0.416 |
| Blind Holdout | 0.307 | healthy | 0.0 | 0.307 | 0.368 |
| Adversarial Holdout | 0.923 | healthy | 0.0 | 0.923 | 0.845 |

## Judge Blind Summary

| Gate | Winner Agreement | Winner Mean Confidence | Current Agreement | Baseline Agreement |
| --- | ---: | ---: | ---: | ---: |
| Judge Blind Holdout | 1.0 | 0.66 | 1.0 | 1.0 |

## Family Health

| Gate | Winner Clean Families | Winner Weakest Family | Current Clean Families | Baseline Clean Families |
| --- | --- | --- | --- | --- |
| Holdout | 12/12 | workflow_to_skill (0 errors) | 12/12 | 12/12 |
| Blind Holdout | 6/6 | blind_operationalize (0 errors) | 6/6 | 6/6 |
| Judge Blind Holdout | 6/6 | blind_operationalize (0 errors) | 6/6 | 6/6 |
| Adversarial Holdout | 6/6 | adversarial_summary_translation_collision (0 errors) | 6/6 | 6/6 |

## Selection Logic

Ordered by:
- fewest false positives
- fewest false negatives
- highest near-neighbor pass rate
- highest negative pass rate
- highest precision
- highest recall
- shortest description
