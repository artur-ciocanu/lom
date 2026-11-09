"""Reject common credential paths even if they are forcibly added to Git."""

import argparse
import os
import subprocess
import sys
from pathlib import PurePosixPath


def is_sensitive_path(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    if name == ".env.example":
        return False
    return (
        name == ".env"
        or name.startswith(".env.")
        or name in {".envrc", ".netrc", ".pypirc", "id_rsa", "id_ed25519"}
        or name.endswith((".key", ".pem", ".p12", ".pfx"))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tracked", action="store_true", help="Check all tracked paths"
    )
    args = parser.parse_args()
    command = (
        ["git", "ls-files", "-z"]
        if args.tracked
        else ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"]
    )
    output = subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout
    paths = [os.fsdecode(path) for path in output.split(b"\0") if path]
    blocked = [path for path in paths if is_sensitive_path(path)]
    if blocked:
        print("Refusing to include sensitive paths:", file=sys.stderr)
        for path in blocked:
            print(f"  {path!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
