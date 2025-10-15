from __future__ import annotations

import importlib.metadata as importlib_metadata
import os
import subprocess
import sys
import uuid
from collections.abc import Iterable, Mapping, Sequence
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, cast

from x_make_common_x import (
    CommandError,
    isoformat_timestamp,
    log_error,
    log_info,
    run_command,
    write_run_report,
)


class PipUpdatesRunnerProtocol(Protocol):
    def batch_install(self, packages: Sequence[str], *, use_user: bool) -> int: ...


class PipUpdatesFactory(Protocol):
    def __call__(self, *args: object, **kwargs: object) -> PipUpdatesRunnerProtocol: ...


class PipUpdatesInstantiationError(RuntimeError):
    """Raised when the pip-updates factory cannot be constructed."""

    def __init__(self) -> None:
        super().__init__(
            "pip updates factory couldn't be instantiated with provided kwargs"
        )


PACKAGE_ROOT = Path(__file__).resolve().parent


def _info(*parts: object) -> None:
    log_info(*parts)


def _error(*parts: object) -> None:
    log_error(*parts)


def _json_ready(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        typed = cast("Mapping[object, object]", value)
        return {str(key): _json_ready(val) for key, val in typed.items()}
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        typed_seq = cast("Sequence[object]", value)
        return [_json_ready(entry) for entry in typed_seq]
    return str(value)


def _base_path_from_cloner(cloner: object, repo_parent_root: str) -> Path:
    base_path = Path(repo_parent_root)
    target_attr: object = getattr(cloner, "target_dir", None)
    if isinstance(target_attr, str):
        with suppress(TypeError, ValueError):
            return Path(target_attr)
    if isinstance(target_attr, os.PathLike):
        with suppress(TypeError, ValueError):
            return Path(os.fspath(cast("os.PathLike[str]", target_attr)))
    return base_path


def _resolve_script_path(base_path: Path) -> Path:
    candidates = (
        base_path / "x_4357_make_pip_updates_x" / "x_cls_make_pip_updates_x.py",
        base_path / "x_make_pip_updates_x" / "x_cls_make_pip_updates_x.py",
        Path.cwd() / "x_4357_make_pip_updates_x" / "x_cls_make_pip_updates_x.py",
        Path.cwd() / "x_make_pip_updates_x" / "x_cls_make_pip_updates_x.py",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


_DEFAULT_PACKAGES: tuple[str, ...] = (
    "x_4357_make_markdown_x",
    "x_4357_make_persistent_env_var_x",
    "x_4357_make_pypi_x",
    "x_4357_make_github_clones_x",
    "x_4357_make_pip_updates_x",
)


def _normalize_packages(packages: Sequence[str]) -> list[str]:
    normalized = [pkg for pkg in packages if pkg]
    if normalized:
        deduped: list[str] = []
        seen: set[str] = set()
        for pkg in normalized:
            if pkg not in seen:
                seen.add(pkg)
                deduped.append(pkg)
        return deduped
    return [candidate for candidate in _DEFAULT_PACKAGES if candidate.startswith("x_")]


def _override_use_user_flag(ctx: object | None, *, default: bool) -> bool:
    publish_opts: object | None = None
    if isinstance(ctx, Mapping):
        publish_opts = cast("Mapping[str, object]", ctx).get("publish_opts")
    elif ctx is not None:
        publish_opts = getattr(ctx, "publish_opts", None)

    if isinstance(publish_opts, Mapping):
        typed = cast("Mapping[str, object]", publish_opts)
        override = typed.get("use_user")
        if isinstance(override, bool):
            return override
        if isinstance(override, str):
            return override.strip().lower() in {"1", "true", "yes"}
    return default


def _instantiate_runner(
    pip_updates_cls: PipUpdatesFactory,
    *,
    ctx: object | None,
    use_user_flag: bool,
) -> PipUpdatesRunnerProtocol:
    attempt_kwargs: tuple[dict[str, object], ...] = (
        {"user": use_user_flag, "ctx": ctx},
        {"user": use_user_flag},
        {"ctx": ctx},
        {},
    )
    last_exc: TypeError | None = None
    for kwargs in attempt_kwargs:
        try:
            return pip_updates_cls(**kwargs)
        except TypeError as exc:
            last_exc = exc
            continue
    if last_exc is not None:
        raise last_exc
    raise PipUpdatesInstantiationError


def _try_run_updates_script(
    pip_updates_cls: PipUpdatesFactory,
    packages: Sequence[str],
    *,
    ctx: object | None,
    use_user_flag: bool,
) -> tuple[bool, int | None]:
    try:
        runner = _instantiate_runner(
            pip_updates_cls,
            ctx=ctx,
            use_user_flag=use_user_flag,
        )
    except (AttributeError, TypeError, ValueError, RuntimeError) as exc:
        _error(
            "pip-updates instantiation failed:",
            f"{exc}; switching to fallback pip install",
        )
        return False, None
    try:
        rc = runner.batch_install(list(packages), use_user=use_user_flag)
    except (
        RuntimeError,
        ValueError,
        subprocess.SubprocessError,
        OSError,
    ) as exc:
        _error(
            "pip-updates invocation failed:",
            f"{exc}; switching to fallback pip install",
        )
        return False, None
    if rc != 0:
        _error(
            "pip-updates reported non-zero exit; switching to fallback pip install",
        )
        return True, rc
    return True, rc


def _get_installed_versions(packages: Sequence[str]) -> dict[str, str | None]:
    installed: dict[str, str | None] = {}
    _info("\nInstalled package versions after first update attempt:")
    for pkg in packages:
        try:
            version = importlib_metadata.version(pkg)
            installed[pkg] = version
            _info(f"{pkg}: {version}")
        except importlib_metadata.PackageNotFoundError:
            installed[pkg] = None
            _info(f"{pkg}: not installed (package not found)")
        except ValueError as exc:
            installed[pkg] = None
            _info(f"{pkg}: not installed ({exc})")
    return installed


def _collect_mismatches(
    expected: Mapping[str, str | None],
    installed: Mapping[str, str | None],
) -> list[tuple[str, str, str | None]]:
    mismatches: list[tuple[str, str, str | None]] = []
    for pkg, version in expected.items():
        if not version:
            continue
        current = installed.get(pkg)
        if current != version:
            mismatches.append((pkg, version, current))
    return mismatches


def _retry_mismatches(
    mismatches: Sequence[tuple[str, str, str | None]],
    script_path: Path,
    *,
    use_user_flag: bool,
    final_installed: dict[str, str | None],
) -> int:
    pinned = [f"{pkg}=={version}" for pkg, version, _ in mismatches]
    retry_cmd = [sys.executable, str(script_path)]
    if use_user_flag:
        retry_cmd.append("--user")
    retry_cmd.extend(pinned)
    _info(f"Retrying install for pinned versions: {' '.join(retry_cmd)}")
    retry_proc = run_command(retry_cmd, check=False)
    if retry_proc.stdout:
        _info(retry_proc.stdout.strip())
    if retry_proc.stderr:
        _error(retry_proc.stderr.strip())
    for pkg_name, _, _ in mismatches:
        try:
            final_installed[pkg_name] = importlib_metadata.version(pkg_name)
        except importlib_metadata.PackageNotFoundError:
            final_installed[pkg_name] = None
    return retry_proc.returncode


def _fallback_pip_install(
    packages: Sequence[str],
    published_versions: Mapping[str, str | None],
    *,
    use_user_flag: bool,
) -> None:
    python = sys.executable
    base_cmd = [python, "-m", "pip", "install", "--upgrade"]
    if use_user_flag:
        base_cmd.append("--user")

    pinned = [
        f"{pkg}=={published_versions[pkg]}"
        for pkg in packages
        if published_versions.get(pkg)
    ]
    loose = [pkg for pkg in packages if not published_versions.get(pkg)]

    for batch in (pinned, loose):
        if not batch:
            continue
        cmd = base_cmd + batch
        _info("Fallback pip install:", " ".join(cmd))
        try:
            proc = run_command(cmd, check=True)
        except CommandError as exc:
            _error(str(exc))
            continue
        if proc.stdout:
            _info(proc.stdout.strip())
        if proc.stderr:
            _error(proc.stderr.strip())


def _print_summary(
    published_versions: Mapping[str, str | None],
    final_installed: Mapping[str, str | None],
    packages: Sequence[str],
    retry_rc: int | None,
) -> bool:
    _info("\nSummary:")
    any_failures = False
    iterable: Iterable[tuple[str, str | None]]
    if published_versions:
        iterable = published_versions.items()
    else:
        iterable = ((pkg, None) for pkg in packages)
    for pkg, expected in iterable:
        current = final_installed.get(pkg)
        if expected:
            if current == expected:
                _info(f"- {pkg}=={expected}: OK | current: {current}")
            else:
                any_failures = True
                _info(f"- {pkg}=={expected}: FAIL | current: {current}")
        else:
            _info(f"- {pkg}: current: {current}")
    if retry_rc is not None and retry_rc != 0 and any_failures:
        _error(f"Retry pip-updates failed with exit code {retry_rc}")
    return any_failures


def _perform_post_install_verification(
    packages: Sequence[str],
    published_artifacts: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    _info("Starting post-install verification (lightweight checks only)")
    if not packages:
        _info("No packages provided for verification; skipping")
        return {
            "status": "skipped",
            "reason": "no packages provided",
        }
    missing = [pkg for pkg in packages if pkg not in published_artifacts]
    if missing:
        joined = ", ".join(sorted(missing))
        _info(
            "Skipping detailed verification because artifact metadata is missing for:",
            joined,
        )
        return {
            "status": "skipped",
            "reason": "missing artifact metadata",
            "missing": sorted(missing),
        }
    _info(
        "Detailed file verification is not implemented in the typed orchestrator; "
        "skipping after validating artifact metadata presence",
    )
    return {
        "status": "performed",
        "detail": "metadata validated; deep verification not implemented",
    }


def run_updates_for_packages(  # noqa: PLR0913
    packages: Sequence[str],
    *,
    cloner: object,
    ctx: object | None,
    repo_parent_root: str,
    published_versions: Mapping[str, str | None],
    published_artifacts: Mapping[str, Mapping[str, object]],
    pip_updates_factory: PipUpdatesFactory,
) -> Path:
    start_time = datetime.now(UTC)
    run_id = uuid.uuid4().hex
    base_path = _base_path_from_cloner(cloner, repo_parent_root)
    script_path = _resolve_script_path(base_path)
    package_list = _normalize_packages(packages)
    use_user_flag = _override_use_user_flag(ctx, default=False)

    inputs_detail: dict[str, object] = {
        "requested_packages": list(packages),
        "normalized_packages": list(package_list),
        "use_user_flag": use_user_flag,
        "repo_parent_root": str(repo_parent_root),
        "published_versions": _json_ready(dict(published_versions)),
        "published_artifacts": _json_ready(dict(published_artifacts)),
    }
    execution_detail: dict[str, object] = {
        "script_path": str(script_path),
        "script_available": script_path.is_file(),
    }
    result_detail: dict[str, object] = {}
    report_payload: dict[str, object] = {
        "run_id": run_id,
        "started_at": isoformat_timestamp(start_time),
        "inputs": inputs_detail,
        "execution": execution_detail,
        "result": result_detail,
    }
    status = "success"
    report_path: Path | None = None
    caught_exc: Exception | None = None
    try:
        if not package_list:
            _info("No published packages to update; skipping pip-updates step")
            result_detail.update(
                {
                    "status": "skipped",
                    "reason": "no packages after normalization",
                }
            )
        else:
            used_script = False
            script_rc: int | None = None
            script_detail: dict[str, object] = {
                "invoked": False,
                "return_code": None,
            }
            if script_path.is_file():
                used_script, script_rc = _try_run_updates_script(
                    pip_updates_factory,
                    package_list,
                    ctx=ctx,
                    use_user_flag=use_user_flag,
                )
                script_detail = {
                    "invoked": used_script,
                    "return_code": script_rc,
                }
            else:
                _info("pip-updates script not found; using direct pip fallback installation")
            execution_detail["script_attempt"] = script_detail

            pinned = [
                f"{pkg}=={published_versions[pkg]}"
                for pkg in package_list
                if published_versions.get(pkg)
            ]
            loose = [pkg for pkg in package_list if not published_versions.get(pkg)]

            used_fallback = (not used_script) or (script_rc not in (None, 0))
            fallback_detail: dict[str, object] = {
                "invoked": used_fallback,
                "pinned": pinned,
                "loose": loose,
            }
            if used_fallback:
                _fallback_pip_install(
                    package_list,
                    published_versions,
                    use_user_flag=use_user_flag,
                )
            execution_detail["fallback"] = fallback_detail

            initial_installed = _get_installed_versions(package_list)
            mismatches = _collect_mismatches(published_versions, initial_installed)
            final_installed = dict(initial_installed)
            retry_rc: int | None = None
            mismatch_entries: list[dict[str, object]] = [
                {
                    "package": pkg,
                    "expected": expected,
                    "observed": observed,
                }
                for pkg, expected, observed in mismatches
            ]

            if mismatches:
                if used_script and not used_fallback and script_path.is_file():
                    retry_rc = _retry_mismatches(
                        mismatches,
                        script_path,
                        use_user_flag=use_user_flag,
                        final_installed=final_installed,
                    )
                    execution_detail["retry"] = {
                        "mode": "script",
                        "return_code": retry_rc,
                        "packages": [entry["package"] for entry in mismatch_entries],
                    }
                else:
                    _info("Retrying mismatches with pinned fallback pip install")
                    _fallback_pip_install(
                        [pkg for pkg, _, _ in mismatches],
                        published_versions,
                        use_user_flag=use_user_flag,
                    )
                    final_installed.update(_get_installed_versions(package_list))
                    retry_rc = 0
                    execution_detail["retry"] = {
                        "mode": "fallback",
                        "return_code": retry_rc,
                        "packages": [entry["package"] for entry in mismatch_entries],
                    }

            any_failures = _print_summary(
                published_versions,
                final_installed,
                package_list,
                retry_rc,
            )
            verification_detail = _perform_post_install_verification(
                package_list,
                published_artifacts,
            )

            result_detail.update(
                {
                    "status": "completed" if not any_failures else "attention",
                    "script_return_code": script_rc,
                    "used_script": used_script,
                    "fallback_used": used_fallback,
                    "retry_return_code": retry_rc,
                    "any_failures": any_failures,
                    "initial_versions": _json_ready(dict(initial_installed)),
                    "final_versions": _json_ready(dict(final_installed)),
                    "mismatches": mismatch_entries,
                    "verification": verification_detail,
                }
            )
    except Exception as exc:
        status = "error"
        report_payload.setdefault("errors", [])
        errors_list = cast("list[object]", report_payload["errors"])
        errors_list.append(
            {
                "type": type(exc).__name__,
                "message": str(exc),
            }
        )
        caught_exc = exc
        raise
    finally:
        end_time = datetime.now(UTC)
        report_payload["status"] = status
        report_payload["completed_at"] = isoformat_timestamp(end_time)
        report_payload["duration_seconds"] = round(
            (end_time - start_time).total_seconds(),
            3,
        )
        report_path = write_run_report(
            "x_make_pip_updates_x",
            report_payload,
            base_dir=PACKAGE_ROOT,
        )
        if caught_exc is not None:
            caught_exc.run_report_path = report_path
    return report_path


__all__ = [
    "PipUpdatesFactory",
    "PipUpdatesRunnerProtocol",
    "run_updates_for_packages",
]
