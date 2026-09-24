
import sys
import subprocess
from pathlib import Path
from sumo_env import ensure_tools_in_path


def generate_random_routes(
    outdir: Path,
    net: Path,
    flows: int = 900,
    end_time: int = 1800,
    seed: int = 42,
    min_distance: float = 150.0
) -> tuple[Path, Path]:
    tools = ensure_tools_in_path()
    randomTrips = tools / "randomTrips.py"

    trips = outdir / "trips.trips.xml"
    rou   = outdir / "routes.rou.xml"

    period = max(0.5, end_time / max(1, flows))
    cmd = [
        sys.executable, str(randomTrips),
        "--net-file", str(net),
        "--end", str(end_time),
        "--period", str(period),
        "--seed", str(seed),
        "--min-distance", str(min_distance),
        "--validate", 
        "--trip-attributes", 'departLane="best" departSpeed="max" departPos="base"',
        "--route-file", str(rou),
        "--output-trip-file", str(trips)
    ]

    print(f"[routes] Generating random trips/routes:\n  {' '.join(cmd)}")
    subprocess.check_call(cmd)
    return trips, rou

def routes_from_csv(outdir: Path, csv_path: Path) -> Path:
    out_path = outdir / "routes_from_csv.rou.xml"
    out_path.write_text(
        "<routes>\n"
        "  <!-- TODO: implement CSV-to-rou conversion -->\n"
        "</routes>\n",
        encoding="utf-8"
    )
    print(f"[routes] Placeholder written to {out_path}")
    return out_path