from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from importlib.metadata import version as _version
from typing import cast

"""red rabbit 2025_0902_0944"""
# No-op logging shim (tools.logging_helper removed)
class _NoopLogger:
    def debug(self, *a, **k):
        return None

    def info(self, *a, **k):
        return None

    def warning(self, *a, **k):
        return None

    def error(self, *a, **k):
        return None

    def exception(self, *a, **k):
        return None


_SILENT_LOGGER = _NoopLogger()


def setup_basic_logger(name: str = "x_make", *, file_path: str | None = None):
    return _SILENT_LOGGER

logger = setup_basic_logger("x_make_pip_updates")


class x_cls_make_pip_updates_x:
    def batch_install(self, packages: list[str], use_user: bool = False) -> int:
        # Force pip upgrade first
        logger.info("Upgrading pip itself...")
        pip_upgrade_cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
        code, out, err = self._run(pip_upgrade_cmd)
        if out:
            logger.info(out.strip())
        if err and code != 0:
            logger.error(err.strip())
        if code != 0:
            logger.warning("Failed to upgrade pip. Continuing anyway.")

        # After publishing, upgrade all published packages
        logger.info(
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
                logger.info(out.strip())
            if err and code != 0:
                logger.error(err.strip())

        results = []
        any_fail = False
        for pkg in packages:
            prev: str | None = self.get_installed_version(pkg)
            self.user = use_user
            curr: str | None = self.get_installed_version(pkg)
            code = 0 if curr else 1
            if code != 0:
                any_fail = True
            results.append(
                {
                    "name": pkg,
                    "prev": prev,
                    "curr": curr,
                    "code": code,
                }
            )
        logger.info("\nSummary:")
        for r in results:
            prev_val = r.get("prev")
            prev = prev_val if isinstance(prev_val, str) and prev_val else "not installed"
            curr_val = r.get("curr")
            curr = curr_val if isinstance(curr_val, str) and curr_val else "not installed"
            status = "OK" if r["code"] == 0 else f"FAIL (code {r['code']})"
            logger.info("- %s: %s | current: %s", r["name"], status, curr)
        return 1 if any_fail else 0

    """
    Ensure a Python package is installed and up-to-date in the current interpreter.

    - Installs the package if missing.
    - Upgrades only when the installed version is outdated.
    - Uses the same Python executable (sys.executable -m pip).
    """

    def __init__(self, user: bool = False) -> None:
        self.user = user

    @staticmethod
    def _run(cmd: list[str]) -> tuple[int, str, str]:
        cp = subprocess.run(cmd, text=True, capture_output=True, check=False)
        stdout = cp.stdout or ""
        stderr = cp.stderr or ""
        return cp.returncode, stdout, stderr

    @staticmethod
    def get_installed_version(dist_name: str) -> str | None:
        try:
            _ver: Callable[[str], str] = cast(Callable[[str], str], _version)
            res = _ver(dist_name)
            # Coerce to str in case metadata returns a non-str representation
            return str(res) if res is not None else None
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
            logger.error("pip list failed (%d): %s", code, err.strip())
            return False
        try:
            for item in json.loads(out or "[]"):
                if item.get("name", "").lower() == dist_name.lower():
                    return True
        except json.JSONDecodeError:
            pass
        return False

    def pip_install(self, dist_name: str, upgrade: bool = False) -> int:
        cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
        if upgrade:
            cmd.append("--upgrade")
        if self.user:
            cmd.append("--user")
        cmd.append(dist_name)
        code, out, err = self._run(cmd)
        if out:
            logger.info(out.strip())
        if err and code != 0:
            logger.error(err.strip())
        return code

    def ensure(self, dist_name: str) -> None:
        installed = self.get_installed_version(dist_name)
        if installed is None:
            logger.info("%s not installed. Installing...", dist_name)
            code = self.pip_install(dist_name, upgrade=False)
            if code != 0:
                logger.error("Failed to install %s (exit %s).", dist_name, code)
            return
        logger.info("%s installed (version %s). Checking for updates...", dist_name, installed)
        if self.is_outdated(dist_name):
            logger.info("%s is outdated. Upgrading...", dist_name)
            code = self.pip_install(dist_name, upgrade=True)
            if code != 0:
                logger.error("Failed to upgrade %s (exit %s).", dist_name, code)
        else:
            logger.info("%s is up to date.", dist_name)


if __name__ == "__main__":
    raw_args = sys.argv[1:]
    use_user_flag = "--user" in raw_args
    args = [a for a in raw_args if not a.startswith("-")]
    packages = (
        args
        if args
        else [
            "x_make_markdown_x",
            "x_make_pypi_x",
            "x_make_github_clones_x",
            "x_make_pip_updates_x",
        ]
    )
    exit_code = x_cls_make_pip_updates_x(user=use_user_flag).batch_install(packages, use_user_flag)
    sys.exit(exit_code)
