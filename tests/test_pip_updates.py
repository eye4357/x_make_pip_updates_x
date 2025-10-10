"""Tests for the pip updates runner."""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

from pytest import fixture

from x_make_pip_updates_x import x_cls_make_pip_updates_x as pip_module
from x_make_pip_updates_x.x_cls_make_pip_updates_x import PipUpdatesRunner

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


@fixture
def runner() -> PipUpdatesRunner:
    return PipUpdatesRunner(user=False)


def test_ctx_flag_supports_multiple_types() -> None:
    """_ctx_flag should handle mappings, objects, and scalars."""
    ctx_mapping: dict[str, object] = {"dry_run": "true", "verbose": 1}

    class CtxObj:
        dry_run = 0
        verbose = "yes"

    assert (
        PipUpdatesRunner._ctx_flag(ctx_mapping, "dry_run") is True
    )  # pyright: ignore[reportPrivateUsage]
    assert (
        PipUpdatesRunner._ctx_flag(ctx_mapping, "verbose") is True
    )  # pyright: ignore[reportPrivateUsage]
    assert (
        PipUpdatesRunner._ctx_flag(CtxObj(), "dry_run") is False
    )  # pyright: ignore[reportPrivateUsage]
    assert (
        PipUpdatesRunner._ctx_flag(CtxObj(), "verbose") is True
    )  # pyright: ignore[reportPrivateUsage]
    assert (
        PipUpdatesRunner._ctx_flag(None, "dry_run") is False
    )  # pyright: ignore[reportPrivateUsage]


def test_get_installed_version_handles_missing_package(
    monkeypatch: MonkeyPatch,
) -> None:
    def fake_version(name: str) -> str:
        raise pip_module.PackageNotFoundError(name)

    monkeypatch.setattr(pip_module, "_version", fake_version)

    assert PipUpdatesRunner.get_installed_version("missing") is None


def test_is_outdated_returns_true_when_package_listed(monkeypatch: MonkeyPatch) -> None:
    payload = json.dumps(
        [
            {
                "name": "SomePkg",
                "version": "1.0",
                "latest_version": "2.0",
            }
        ]
    )

    def fake_run(cmd: list[str]) -> tuple[int, str, str]:
        return 0, payload, ""

    monkeypatch.setattr(PipUpdatesRunner, "_run", staticmethod(fake_run))

    assert PipUpdatesRunner().is_outdated("somepkg") is True


def test_is_outdated_handles_non_json_response(monkeypatch: MonkeyPatch) -> None:
    def fake_run(cmd: list[str]) -> tuple[int, str, str]:
        return 0, "not json", ""

    monkeypatch.setattr(PipUpdatesRunner, "_run", staticmethod(fake_run))

    assert PipUpdatesRunner().is_outdated("pkg") is False


def test_batch_install_deduplicates_packages(
    monkeypatch: MonkeyPatch, runner: PipUpdatesRunner
) -> None:
    pip_calls: list[list[str]] = []

    def fake_refresh(
        self: PipUpdatesRunner, package: str, *, use_user: bool
    ) -> pip_module.InstallResult:
        pip_calls.append([package, str(use_user)])
        return pip_module.InstallResult(package, "1.0", "2.0", 0)

    def fake_run_report(self: PipUpdatesRunner, cmd: list[str]) -> tuple[int, str, str]:
        return 0, "", ""

    monkeypatch.setattr(PipUpdatesRunner, "_refresh_package", fake_refresh)
    monkeypatch.setattr(PipUpdatesRunner, "_run_and_report", fake_run_report)

    exit_code = runner.batch_install(["foo", "bar", "foo"], use_user=False)

    assert exit_code == 0
    assert pip_calls == [["foo", "False"], ["bar", "False"]]


def test_summarize_reports_failures(monkeypatch: MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_info(msg: str) -> None:
        calls.append(msg)

    monkeypatch.setattr(pip_module, "_info", fake_info)

    results = [
        pip_module.InstallResult("foo", "1.0", "2.0", 0),
        pip_module.InstallResult("bar", "1.0", "2.0", 2),
    ]

    exit_code = PipUpdatesRunner()._summarize(
        results
    )  # pyright: ignore[reportPrivateUsage]

    assert exit_code == 1
    assert any("bar" in line for line in calls)


def test_run_executes_pip_and_returns_result(monkeypatch: MonkeyPatch) -> None:
    completed = subprocess.CompletedProcess(
        args=["python"], returncode=0, stdout="ok", stderr=""
    )

    def fake_run(
        cmd: list[str], text: bool, capture_output: bool, check: bool
    ) -> subprocess.CompletedProcess[str]:
        return completed

    monkeypatch.setattr(subprocess, "run", fake_run)

    code, out, err = PipUpdatesRunner._run(
        ["python", "--version"]
    )  # pyright: ignore[reportPrivateUsage]

    assert (code, out, err) == (0, "ok", "")


def test_refresh_package_uses_install_result(monkeypatch: MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_version(name: str) -> str | None:
        return "1.0" if name == "foo" else "2.0"

    def fake_run_report(self: PipUpdatesRunner, cmd: list[str]) -> tuple[int, str, str]:
        calls.append(list(cmd))
        return 0, "", ""

    monkeypatch.setattr(
        PipUpdatesRunner, "get_installed_version", staticmethod(fake_version)
    )
    monkeypatch.setattr(PipUpdatesRunner, "_run_and_report", fake_run_report)

    result = PipUpdatesRunner()._refresh_package(
        "foo", use_user=True
    )  # pyright: ignore[reportPrivateUsage]

    assert isinstance(result, pip_module.InstallResult)
    assert result.prev == "1.0"
    assert result.curr == "1.0"
    assert calls and "--user" in calls[0]
