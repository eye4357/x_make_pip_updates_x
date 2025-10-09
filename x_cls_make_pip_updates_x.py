from __future__ import annotations

import json
import logging
import subprocess
import sys
import sys as _sys
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import version as _version
from typing import cast

_LOGGER = logging.getLogger("x_make")


def _info(*args: object) -> None:
    msg = " ".join(str(a) for a in args)
    try:
        _LOGGER.info("%s", msg)
    except Exception:
        pass
    try:
        print(msg)
    except Exception:
        try:
            _sys.stdout.write(msg + "\n")
        except Exception:
            pass


def _error(*args: object) -> None:
    msg = " ".join(str(a) for a in args)
    try:
        _LOGGER.error("%s", msg)
    except Exception:
        pass
    try:
        print(msg, file=_sys.stderr)
    except Exception:
        try:
            _sys.stderr.write(msg + "\n")
        except Exception:
            try:
                print(msg)
            except Exception:
                pass


"""red rabbit 2025_0902_0944"""


# use shared helpers from x_make_common_x.helpers


RunResult = tuple[int, str, str]


@dataclass(slots=True)
class InstallResult:
    name: str
    prev: str | None
    curr: str | None
    code: int


class x_cls_make_pip_updates_x:
    # ...existing code...

    def batch_install(self, packages: list[str], *, use_user: bool = False) -> int:
        # Force pip upgrade first
        _info("Upgrading pip itself...")
        pip_upgrade_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
        ]
        code, out, err = self._run(pip_upgrade_cmd)
        if out:
            _info(out.strip())
        if err and code != 0:
            _error(err.strip())
        if code != 0:
            _info("Failed to upgrade pip. Continuing anyway.")

        # After publishing, upgrade all published packages
        _info(
            "Upgrading all published packages with --upgrade --force-reinstall --no-cache-dir..."
        )
        for pkg in packages:
            cmd = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--force-reinstall",
                "--no-cache-dir",
            ]
            if use_user:
                cmd.append("--user")
            cmd.append(pkg)
            code, out, err = self._run(cmd)
            if out:
                _info(out.strip())
            if err and code != 0:
                _error(err.strip())

        results: list[InstallResult] = []
        any_fail = False
        for pkg in packages:
            prev: str | None = self.get_installed_version(pkg)
            self.user = use_user
            curr: str | None = self.get_installed_version(pkg)
            code = 0 if curr else 1
            if code != 0:
                any_fail = True
            results.append(InstallResult(pkg, prev, curr, code))

        _info("\nSummary:")
        for r in results:
            prev = r.prev or "not installed"
            curr = r.curr or "not installed"
            status = "OK" if r.code == 0 else f"FAIL (code {r.code})"
            _info(f"- {r.name}: {status} | current: {curr}")
        return 1 if any_fail else 0

    """
    Ensure a Python package is installed and up-to-date in the current interpreter.

    - Installs the package if missing.
    - Upgrades only when the installed version is outdated.
    - Uses the same Python executable (sys.executable -m pip).
    """

    def __init__(self, user: bool = False, ctx: object | None = None) -> None:
        """Primary constructor: preserve previous 'user' flag and accept ctx.

        Dry-run is now sourced from the orchestrator context when provided.
        If no context is provided, default to False.
        """
        self.user = user
        self._ctx = ctx
        try:
            self.dry_run = bool(getattr(self._ctx, "dry_run", False))
        except Exception:
            self.dry_run = False

        if getattr(self._ctx, "verbose", False):
            _info(f"[pip_updates] initialized user={self.user}")

    @staticmethod
    def _run(cmd: list[str]) -> RunResult:
        cp = subprocess.run(cmd, text=True, capture_output=True, check=False)
        stdout = cp.stdout or ""
        stderr = cp.stderr or ""
        return cp.returncode, stdout, stderr

    @staticmethod
    def get_installed_version(dist_name: str) -> str | None:
        try:
            _ver = cast("Callable[[str], str]", _version)
            res = _ver(dist_name)
            return str(res)
        except Exception:
            return None

    def is_outdated(self, dist_name: str) -> bool:
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "list",
            "--outdated",
            "--format=json",
            "--disable-pip-version-check",
        ]
        code, out, err = self._run(cmd)
        if code != 0:
            _error(f"pip list failed ({code}): {err.strip()}")
            return False
        try:
            loaded_obj: object = json.loads(out or "[]")
        except json.JSONDecodeError:
            return False

        if not isinstance(loaded_obj, list):
            return False

        for entry_obj in loaded_obj:
            if not isinstance(entry_obj, dict):
                continue
            entry = cast("dict[str, object]", entry_obj)
            name = entry.get("name")
            if isinstance(name, str) and name.lower() == dist_name.lower():
                return True
        return False

    def pip_install(self, dist_name: str, upgrade: bool = False) -> int:
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
        ]
        if upgrade:
            cmd.append("--upgrade")
        if self.user:
            cmd.append("--user")
        cmd.append(dist_name)
        code, out, err = self._run(cmd)
        if out:
            _info(out.strip())
        if err and code != 0:
            _error(err.strip())
        return code

    def ensure(self, dist_name: str) -> None:
        installed = self.get_installed_version(dist_name)
        if installed is None:
            _info(f"{dist_name} not installed. Installing...")
            code = self.pip_install(dist_name, upgrade=False)
            if code != 0:
                _error(f"Failed to install {dist_name} (exit {code}).")
            return
        _info(f"{dist_name} installed (version {installed}). Checking for updates...")
        if self.is_outdated(dist_name):
            _info(f"{dist_name} is outdated. Upgrading...")
            code = self.pip_install(dist_name, upgrade=True)
            if code != 0:
                _error(f"Failed to upgrade {dist_name} (exit {code}).")
        else:
            _info(f"{dist_name} is up to date.")


if __name__ == "__main__":
    raw_args = sys.argv[1:]
    use_user_flag = "--user" in raw_args
    args = [a for a in raw_args if not a.startswith("-")]
    packages = (
        args
        if args
        else [
            "x_4357_make_markdown_x",
            "x_4357_make_pypi_x",
            "x_4357_make_github_clones_x",
            "x_4357_make_pip_updates_x",
        ]
    )
    exit_code = x_cls_make_pip_updates_x(user=use_user_flag).batch_install(
        packages,
        use_user=use_user_flag,
    )
    sys.exit(exit_code)
