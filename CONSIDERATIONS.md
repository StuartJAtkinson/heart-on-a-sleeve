# Considerations

- PR #42 ("build(deps): bump actions/setup-node from 6 to 7"): "Lint backend (ruff)" check is FAILING against the current head commit (1de6901a747295a4aad537286e5cf458f2d2e040). Not fixed — out of scope for this merge run. Needs human review before merging.
- PR #41 ("build(deps): bump actions/setup-python from 6 to 7"): "Lint backend (ruff)" and "Smoke tests (pytest)" checks are FAILING against the current head commit (2012ff755a8a8d1a0d7ac49b20d89ade6fa3a002). Not fixed — out of scope for this merge run. Needs human review before merging.
- PR #40 (build(deps-dev): bump vite from 8.0.14 to 8.1.5 in /frontend/cesium) has a FAILING check "Smoke tests (pytest)" against current head cddeba8 — needs human investigation before merge.
- PR #39 (build(deps-dev): bump typescript from 5.9.3 to 7.0.2 in /frontend/cesium) has FAILING checks "Smoke tests (pytest)" and "Type-check frontend (tsc)" against current head a9ab395 — needs human investigation before merge.
- PR #37 (build(deps): update pytest requirement from >=8.0.0 to >=9.1.1 in /backend) has a FAILING check "Smoke tests (pytest)" against current head 0bf1b1925bf12b9457841e1591d96fe80f4af26a — needs human investigation before merge.
