"""JSON contracts for x_make_pip_updates_x."""

from __future__ import annotations

import sys as _sys

_JSON_VALUE_TYPES: list[str] = [
    "object",
    "array",
    "string",
    "number",
    "boolean",
    "null",
]

_STRING_LIST_SCHEMA: dict[str, object] = {
    "type": "array",
    "items": {"type": "string", "minLength": 1},
}

_PACKAGES_SCHEMA: dict[str, object] = {
    "type": "array",
    "items": {"type": "string", "minLength": 1},
}

_PUBLISHED_VERSION_VALUE: dict[str, object] = {
    "oneOf": [
        {"type": "string", "minLength": 1},
        {"type": "null"},
    ]
}

_PUBLISHED_VERSIONS_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": _PUBLISHED_VERSION_VALUE,
}

_PUBLISHED_ARTIFACT_ENTRY_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "main": {"type": "string", "minLength": 1},
        "anc": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
    },
    "required": ["main"],
    "additionalProperties": True,
}

_PUBLISHED_ARTIFACTS_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": _PUBLISHED_ARTIFACT_ENTRY_SCHEMA,
}

_PUBLISH_OPTS_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "use_user": {"type": "boolean"},
    },
    "additionalProperties": True,
}

_CONTEXT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "dry_run": {"type": "boolean"},
        "verbose": {"type": "boolean"},
        "publish_opts": _PUBLISH_OPTS_SCHEMA,
    },
    "additionalProperties": True,
}

_CLONER_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "target_dir": {"type": "string", "minLength": 1},
    },
    "additionalProperties": True,
}

_PARAMETERS_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "packages": _PACKAGES_SCHEMA,
        "repo_parent_root": {"type": "string", "minLength": 1},
        "published_versions": _PUBLISHED_VERSIONS_SCHEMA,
        "published_artifacts": _PUBLISHED_ARTIFACTS_SCHEMA,
        "context": _CONTEXT_SCHEMA,
        "cloner": _CLONER_SCHEMA,
    },
    "required": [
        "packages",
        "repo_parent_root",
        "published_versions",
        "published_artifacts",
    ],
    "additionalProperties": False,
}

INPUT_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "x_make_pip_updates_x input",
    "type": "object",
    "properties": {
        "command": {"const": "x_make_pip_updates_x"},
        "parameters": _PARAMETERS_SCHEMA,
    },
    "required": ["command", "parameters"],
    "additionalProperties": False,
}

_SCRIPT_ATTEMPT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "invoked": {"type": "boolean"},
        "return_code": {"type": ["integer", "null"]},
    },
    "required": ["invoked", "return_code"],
    "additionalProperties": False,
}

_FALLBACK_DETAIL_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "invoked": {"type": "boolean"},
        "pinned": _STRING_LIST_SCHEMA,
        "loose": _STRING_LIST_SCHEMA,
    },
    "required": ["invoked", "pinned", "loose"],
    "additionalProperties": False,
}

_RETRY_DETAIL_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "mode": {"type": "string", "enum": ["script", "fallback"]},
        "return_code": {"type": ["integer", "null"]},
        "packages": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1,
        },
    },
    "required": ["mode", "return_code", "packages"],
    "additionalProperties": False,
}

_EXECUTION_DETAIL_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "script_path": {"type": "string", "minLength": 1},
        "script_available": {"type": "boolean"},
        "script_attempt": _SCRIPT_ATTEMPT_SCHEMA,
        "fallback": _FALLBACK_DETAIL_SCHEMA,
        "retry": _RETRY_DETAIL_SCHEMA,
    },
    "required": ["script_path", "script_available"],
    "additionalProperties": False,
}

_MISMATCH_ENTRY_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "package": {"type": "string", "minLength": 1},
        "expected": {"type": "string", "minLength": 1},
        "observed": {
            "oneOf": [
                {"type": "string", "minLength": 1},
                {"type": "null"},
            ]
        },
    },
    "required": ["package", "expected", "observed"],
    "additionalProperties": False,
}

_VERSION_MAPPING_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": {
        "oneOf": [
            {"type": "string", "minLength": 1},
            {"type": "null"},
        ]
    },
}

_VERIFICATION_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["performed", "skipped"],
        },
        "detail": {
            "oneOf": [
                {"type": "string", "minLength": 1},
                {"type": "null"},
            ]
        },
        "reason": {
            "oneOf": [
                {"type": "string", "minLength": 1},
                {"type": "null"},
            ]
        },
        "missing": _STRING_LIST_SCHEMA,
    },
    "required": ["status"],
    "additionalProperties": True,
}

_RESULT_COMPLETED_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["completed", "attention"]},
        "script_return_code": {"type": ["integer", "null"]},
        "used_script": {"type": "boolean"},
        "fallback_used": {"type": "boolean"},
        "retry_return_code": {"type": ["integer", "null"]},
        "any_failures": {"type": "boolean"},
        "initial_versions": _VERSION_MAPPING_SCHEMA,
        "final_versions": _VERSION_MAPPING_SCHEMA,
        "mismatches": {
            "type": "array",
            "items": _MISMATCH_ENTRY_SCHEMA,
        },
        "verification": _VERIFICATION_SCHEMA,
    },
    "required": [
        "status",
        "script_return_code",
        "used_script",
        "fallback_used",
        "retry_return_code",
        "any_failures",
        "initial_versions",
        "final_versions",
        "mismatches",
        "verification",
    ],
    "additionalProperties": False,
}

_RESULT_SKIPPED_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "status": {"const": "skipped"},
        "reason": {"type": "string", "minLength": 1},
    },
    "required": ["status", "reason"],
    "additionalProperties": True,
}

_RESULT_DETAIL_SCHEMA: dict[str, object] = {
    "oneOf": [
        _RESULT_COMPLETED_SCHEMA,
        _RESULT_SKIPPED_SCHEMA,
    ]
}

_INPUTS_DETAIL_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "requested_packages": _STRING_LIST_SCHEMA,
        "normalized_packages": _STRING_LIST_SCHEMA,
        "use_user_flag": {"type": "boolean"},
        "repo_parent_root": {"type": "string", "minLength": 1},
        "published_versions": _PUBLISHED_VERSIONS_SCHEMA,
        "published_artifacts": _PUBLISHED_ARTIFACTS_SCHEMA,
    },
    "required": [
        "requested_packages",
        "normalized_packages",
        "use_user_flag",
        "repo_parent_root",
        "published_versions",
        "published_artifacts",
    ],
    "additionalProperties": False,
}

_ERROR_ENTRY_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "minLength": 1},
        "message": {"type": "string", "minLength": 1},
    },
    "required": ["type", "message"],
    "additionalProperties": True,
}

OUTPUT_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "x_make_pip_updates_x output",
    "type": "object",
    "properties": {
        "run_id": {
            "type": "string",
            "pattern": "^[a-f0-9]{32}$",
        },
        "started_at": {"type": "string", "format": "date-time"},
        "inputs": _INPUTS_DETAIL_SCHEMA,
        "execution": _EXECUTION_DETAIL_SCHEMA,
        "result": _RESULT_DETAIL_SCHEMA,
        "status": {"type": "string", "enum": ["success", "error"]},
        "errors": {
            "type": "array",
            "items": _ERROR_ENTRY_SCHEMA,
        },
        "completed_at": {"type": "string", "format": "date-time"},
        "duration_seconds": {"type": "number", "minimum": 0},
        "tool": {"const": "x_make_pip_updates_x"},
        "generated_at": {"type": "string", "format": "date-time"},
    },
    "required": [
        "run_id",
        "started_at",
        "inputs",
        "execution",
        "result",
        "status",
        "completed_at",
        "duration_seconds",
        "tool",
        "generated_at",
    ],
    "additionalProperties": False,
}

ERROR_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "x_make_pip_updates_x error",
    "type": "object",
    "properties": {
        "status": {"const": "failure"},
        "message": {"type": "string", "minLength": 1},
        "details": {
            "type": "object",
            "additionalProperties": {"type": _JSON_VALUE_TYPES},
        },
    },
    "required": ["status", "message"],
    "additionalProperties": True,
}

# Preserve legacy import path "json_contracts" for downstream tooling.
_sys.modules.setdefault("json_contracts", _sys.modules[__name__])

__all__ = ["ERROR_SCHEMA", "INPUT_SCHEMA", "OUTPUT_SCHEMA"]
