from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from importlib.metadata import version as _pkg_version
from typing import Any, cast

_VERSION: Callable[[str], str] = cast(Callable[[str], str], _pkg_version)


def get_installed_version(dist_name: str) -> str | None:
    try:
        return _VERSION(dist_name)
    except Exception:
        # Treat as not installed if metadata cannot be resolved
        return None


def main(x_lib_x: str, use_user: bool) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(here, "x_cls_make_pip_x.py")
    if not os.path.exists(target):
        print(f"Cannot find installer script at: {target}")
        return 2

    # Build command: use the current Python to run the installer for the given package
    cmd = [sys.executable, target, x_lib_x]
    # Allow optional --user flag pass-through
    if use_user:
        cmd.append("--user")

    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd, check=False)
    return proc.returncode


if __name__ == "__main__":
    # Packages can be provided as CLI args (positional), e.g.:
    #   python install_foobar.py pkg1 pkg2 --user
    # If none provided, default to the two internal packages below.
    raw_args: list[str] = sys.argv[1:]
    use_user_flag = "--user" in raw_args
    args = [a for a in raw_args if not a.startswith("-")]
    packages = (
        args
        if args
        else [
            "x_make_markdown_x",
            "x_make_pypi_x",
            "x_make_github_clones_x"
        ]
    )

    results: list[dict[str, Any]] = []
    any_fail = False
    for pkg in packages:
        prev = get_installed_version(pkg)
        code = main(pkg, use_user_flag)
        curr = get_installed_version(pkg)
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

    # Print summary
    print("\nSummary:")
    for r in results:
        prev = r["prev"] or "not installed"
        curr = r["curr"] or "not installed"
        status = "OK" if r["code"] == 0 else f"FAIL (code {r['code']})"
        print(f"- {r['name']}: {status} | previous: {prev} -> current: {curr}")

    sys.exit(1 if any_fail else 0)
