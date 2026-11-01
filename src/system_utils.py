"""Small helpers for running operating-system commands safely."""
import os
import subprocess
from typing import List


def run_command(cmd: List[str], timeout: float = 10.0) -> str:
    """Run a command (no shell) and return its text output, or "" if it fails."""
    kwargs = dict(capture_output=True, text=True, errors="replace", timeout=timeout)
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        proc = subprocess.run(cmd, **kwargs)
    except (OSError, subprocess.SubprocessError):
        return ""
    return (proc.stdout or "") + (proc.stderr or "")
