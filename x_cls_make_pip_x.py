from __future__ import annotations

import json
import subprocess
import sys
from typing import cast

try:
    from importlib.metadata import PackageNotFoundError, version  # Python 3.8+
except ImportError:  # pragma: no cover
    from importlib_metadata import PackageNotFoundError, version  # type: ignore


class x_cls_make_pip_x:
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
            return cast(str, version(dist_name))
        except PackageNotFoundError:
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
            print(f"pip list failed ({code}): {err.strip()}")
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
            print(out.strip())
        if err and code != 0:
            print(err.strip())
        return code

    def ensure(self, dist_name: str) -> None:
        installed = self.get_installed_version(dist_name)
        if installed is None:
            print(f"{dist_name} not installed. Installing...")
            code = self.pip_install(dist_name, upgrade=False)
            if code != 0:
                print(f"Failed to install {dist_name} (exit {code}).")
            return

        print(f"{dist_name} installed (version {installed}). Checking for updates...")
        if self.is_outdated(dist_name):
            print(f"{dist_name} is outdated. Upgrading...")
            code = self.pip_install(dist_name, upgrade=True)
            if code != 0:
                print(f"Failed to upgrade {dist_name} (exit {code}).")
        else:
            print(f"{dist_name} is up to date.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m x_make_pip_x.x_cls_make_pip_x <package-name> [--user]")
        sys.exit(2)
    pkg = sys.argv[1]
    use_user = "--user" in sys.argv[2:]
    x_cls_make_pip_x(user=use_user).ensure(pkg)
