# DAOS Branch Rollout Checklist

## Pre-Merge Checks (per branch)

- [ ] Code is scoped to branch objective.
- [ ] Targeted tests pass locally.
- [ ] Error handling and logging are present for new operational paths.
- [ ] API/schema changes include compatibility considerations.
- [ ] Documentation is updated if behavior changed.

## Merge Control

- [ ] Merge branches in planned sequence.
- [ ] Run smoke tests after each merge.
- [ ] Track regressions by branch commit hash.

## Post-Merge Validation

- [ ] Ingestion workflow remains operational end-to-end.
- [ ] Metadata events are queryable for ingested datasets.
- [ ] Observability endpoint returns request/error signals.
- [ ] Frontend app boots with routed shell.
- [ ] AI-generated plans include confidence and trace metadata.
- [ ] Reliability tests continue to pass.
