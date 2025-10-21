from __future__ import annotations

# ruff: noqa: S101 - assertions express expectations in test cases
import copy
import json
from pathlib import Path

import pytest
from x_make_common_x.json_contracts import validate_payload, validate_schema

from x_make_pip_updates_x.json_contracts import (
    ERROR_SCHEMA,
    INPUT_SCHEMA,
    OUTPUT_SCHEMA,
)
from x_make_pip_updates_x.update_flow import main_json

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "json_contracts"
REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"


@pytest.fixture(scope="module")
def sample_input() -> dict[str, object]:
    with (FIXTURE_DIR / "input.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def sample_output() -> dict[str, object]:
    with (FIXTURE_DIR / "output.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def sample_error() -> dict[str, object]:
    with (FIXTURE_DIR / "error.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_schemas_are_valid() -> None:
    for schema in (INPUT_SCHEMA, OUTPUT_SCHEMA, ERROR_SCHEMA):
        validate_schema(schema)


def test_sample_payloads_match_schema(
    sample_input: dict[str, object],
    sample_output: dict[str, object],
    sample_error: dict[str, object],
) -> None:
    validate_payload(sample_input, INPUT_SCHEMA)
    validate_payload(sample_output, OUTPUT_SCHEMA)
    validate_payload(sample_error, ERROR_SCHEMA)


def test_existing_reports_align_with_schema() -> None:
    report_files = sorted(REPORTS_DIR.glob("x_make_pip_updates_x_run_*.json"))
    assert report_files, "expected at least one pip-updates run report to validate"
    for report_file in report_files:
        with report_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        validate_payload(payload, OUTPUT_SCHEMA)


def test_main_json_executes_happy_path(sample_input: dict[str, object]) -> None:
    result = main_json(sample_input)
    validate_payload(result, OUTPUT_SCHEMA)
    assert result["status"] in {"success", "error"}


def test_main_json_returns_error_for_invalid_payload(
    sample_input: dict[str, object],
) -> None:
    invalid = copy.deepcopy(sample_input)
    parameters = invalid.get("parameters")
    if isinstance(parameters, dict):
        parameters.pop("repo_parent_root", None)
    result = main_json(invalid)
    validate_payload(result, ERROR_SCHEMA)
    assert result["status"] == "failure"
