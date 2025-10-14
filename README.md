# x_make_pip_updates_x — Control Room Lab Notes

> "Dependencies age fast. I keep them fresh, verified, and logged before they ever touch production."

## Manifesto
x_make_pip_updates_x automates package audits and upgrades. It compares installed versus requested versions, enforces hash verification, and surfaces dependency graphs so the Road to 0.20.2 stack never goes stale.

## 0.20.2 Command Sequence
Version 0.20.2 reaffirms the upgrade cadence for this lab. Every checklist in this README mirrors the Road to 0.20.2 control brief, so when dependencies move, I know exactly why and where the blast radius lands.

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
- [Road to 0.20.2 Control Room Ledger](../x_0_make_all_x/Change%20Control/0.20.2/Road%20to%200.20.2%20Engineering%20Proposal.md)
- [Road to 0.20.2 Engineering Proposal](../x_0_make_all_x/Change%20Control/0.20.2/Road%20to%200.20.2%20Engineering%20Proposal.md)

## Cross-Linked Intelligence
- [x_make_pypi_x](../x_make_pypi_x/README.md) — consumes upgrade plans before publishing
- [x_make_common_x](../x_make_common_x/README.md) — supplies logging and subprocess helpers for pip runs
- [x_make_github_visitor_x](../x_make_github_visitor_x/README.md) — validates the repos after upgrades land

## Lab Etiquette
Log every dependency shift in the Change Control index with before/after versions and verification evidence. If a hash mismatches or a license looks suspect, halt the pipeline—half measures invite collapse.
