# netgen.py
import subprocess
from pathlib import Path
from sumo_env import find_sumo

def _run(cmd: list[str]) -> None:
    res = subprocess.run(cmd, text=True, capture_output=True)
    if res.returncode != 0:
        print("\n[netgen] Command failed:")
        print("CMD:", " ".join(cmd))
        if res.stdout.strip():
            print("\n--- STDOUT ---\n", res.stdout)
        if res.stderr.strip():
            print("\n--- STDERR ---\n", res.stderr)
        raise RuntimeError(f"netgenerate/netconvert failed with exit code {res.returncode}")

def generate_grid_network(
    outdir: Path,
    size: int = 4,
    length: float = 180.0,
    speed: float = 13.9,
    lanes: int = 2,
    turn_lanes: bool = False
) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    net_path = outdir / "net.net.xml"

    netgenerate = find_sumo("netgenerate")
    cmd = [
        netgenerate, "--grid",
        f"--grid.number={size}",
        f"--grid.length={int(length)}",
        f"--default.speed={speed}",      # <— DOT, not hyphen
        f"--default.lanenumber={lanes}",
        "--tls.guess",
        "--no-turnarounds",
        "--output-file", str(net_path),
    ]
    if turn_lanes:
        cmd += ["--turn-lanes"]

    print("[netgen]", " ".join(cmd))
    _run(cmd)                          # <— use _run, not check_call
    return net_path
