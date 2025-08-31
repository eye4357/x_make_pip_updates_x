from __future__ import annotations
import os
import sys
import subprocess
from typing import Optional, List, Dict, Any, cast
try:
    # Python 3.8+
    from importlib.metadata import version as _pkg_version, PackageNotFoundError
except Exception:  # pragma: no cover - fallback for very old Python
    from importlib_metadata import version as _pkg_version, PackageNotFoundError  # type: ignore

def get_installed_version(dist_name: str) -> Optional[str]:
    try:
        return cast(str, _pkg_version(dist_name))
    except PackageNotFoundError:
        return None
    except Exception:
        # On any unexpected error, treat as not installed for summary purposes
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
    proc = subprocess.run(cmd)
    return proc.returncode

if __name__ == "__main__":
    # Packages can be provided as CLI args (positional), e.g.:
    #   python install_foobar.py pkg1 pkg2 --user
    # If none provided, default to the two internal packages below.
    raw_args: List[str] = sys.argv[1:]
    use_user_flag = "--user" in raw_args
    args = [a for a in raw_args if not a.startswith("-")]
    packages = args if args else [
        "x_make_markdown_x",
        "x_make_pypi_x",
    ]

    results: List[Dict[str, Any]] = []
    any_fail = False
    for pkg in packages:
        prev = get_installed_version(pkg)
        code = main(pkg, use_user_flag)
        curr = get_installed_version(pkg)
        if code != 0:
            any_fail = True
        results.append({
            "name": pkg,
            "prev": prev,
            "curr": curr,
            "code": code,
        })

    # Print summary
    print("\nSummary:")
    for r in results:
        prev = r["prev"] or "not installed"
        curr = r["curr"] or "not installed"
        status = "OK" if r["code"] == 0 else f"FAIL (code {r['code']})"
        print(f"- {r['name']}: {status} | previous: {prev} -> current: {curr}")

    sys.exit(1 if any_fail else 0)
