import os, sys, shutil, subprocess
from pathlib import Path
import traci

def ensure_tools_in_path() -> Path:
    home = os.environ.get("SUMO_HOME")
    if not home:
        raise RuntimeError(
            "The environment variable SUMO_HOME is not set.\n"
            "Please set it to your main SUMO installation folder (the one containing /bin and /tools)."
        )

    tools = Path(home) / "tools"
    if not tools.exists():
        raise RuntimeError(f"Could not find the folder {tools}. Check your SUMO installation.")

    if str(tools) not in sys.path:
        sys.path.append(str(tools))
        print(f"[env] Added to sys.path: {tools}")
    return tools


def find_sumo(binary: str) -> str:
    p = shutil.which(binary)
    if p:
        return p

    home = os.environ.get("SUMO_HOME")
    if home:
        candidate = Path(home) / "bin" / binary
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(
        f" Executable '{binary}' not found in PATH or $SUMO_HOME/bin.\n"
        "Make sure SUMO is installed and SUMO_HOME is set correctly."
    )
