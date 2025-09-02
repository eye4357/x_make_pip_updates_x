from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from importlib.metadata import version as _version
from typing import cast


class x_cls_make_pip_x:
    def batch_install(self, packages: list[str], use_user: bool = False) -> int:
        results = []
        any_fail = False
        for pkg in packages:
            prev = self.get_installed_version(pkg)
            self.user = use_user
            self.ensure(pkg)
            curr = self.get_installed_version(pkg)
            code = 0 if curr else 1
            if code != 0:
                any_fail = True
            results.append({
                "name": pkg,
                "prev": prev,
                "curr": curr,
                "code": code,
            })
        print("\nSummary:")
        for r in results:
            prev = r["prev"] or "not installed"
            curr = r["curr"] or "not installed"
            status = "OK" if r["code"] == 0 else f"FAIL (code {r['code']})"
            print(f"- {r['name']}: {status} | previous: {prev} -> current: {curr}")
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
            return _ver(dist_name)
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
    raw_args = sys.argv[1:]
    use_user_flag = "--user" in raw_args
    args = [a for a in raw_args if not a.startswith("-")]
    packages = args if args else [
        "x_make_markdown_x",
        "x_make_pypi_x",
        "x_make_github_clones_x"
    ]
    exit_code = x_cls_make_pip_x(user=use_user_flag).batch_install(packages, use_user_flag)
    sys.exit(exit_code)
