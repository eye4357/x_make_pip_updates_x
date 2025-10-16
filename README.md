# x_make_pip_updates_x — Control Room Lab Notes

> "Dependencies age fast. I keep them fresh, verified, and logged before they ever touch production."

## Manifesto
x_make_pip_updates_x automates package audits and upgrades. It compares installed versus requested versions, enforces hash verification, and surfaces dependency graphs so the Road to 0.20.4 stack never goes stale.

## 0.20.4 Command Sequence
Version 0.20.4 feeds the propagation column in the new Kanban layout. Upgrade runs now register their JSON ledgers with the orchestrator summary so the Pip Package Propagation checkpoint reports the exact batches, retries, and failures without an operator lifting a finger.

## Ingredients
- Python 3.11+
- Ruff, Black, MyPy, and Pyright
- Optional: `pip-audit`, `pip-tools`, and graph visualization extras when you enable advanced checks

## Cook Instructions
1. `python -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1`
3. `python -m pip install --upgrade pip`
4. `pip install -r requirements.txt`
5. `python x_cls_make_pip_updates_x.py --help` to plan your next upgrade wave

## Quality Assurance
| Check | Command |
| --- | --- |
| Formatting sweep | `python -m black .`
| Lint interrogation | `python -m ruff check .`
| Type audit | `python -m mypy .`
| Static contract scan | `python -m pyright`
| Functional verification | `pytest`

## Distribution Chain
- [Changelog](./CHANGELOG.md)
- [Road to 0.20.4 Engineering Proposal](../x_0_make_all_x/Change%20Control/0.20.4/Road%20to%200.20.4%20Engineering%20Proposal.md)
- [Road to 0.20.3 Engineering Proposal](../x_0_make_all_x/Change%20Control/0.20.3/Road%20to%200.20.3%20Engineering%20Proposal.md)

## Cross-Linked Intelligence
- [x_make_pypi_x](../x_make_pypi_x/README.md) — consumes upgrade plans before publishing
- [x_make_common_x](../x_make_common_x/README.md) — supplies logging and subprocess helpers for pip runs
- [x_make_github_visitor_x](../x_make_github_visitor_x/README.md) — validates the repos after upgrades land

## Lab Etiquette
Log every dependency shift in the Change Control index with before/after versions and verification evidence. If a hash mismatches or a license looks suspect, halt the pipeline—half measures invite collapse.
