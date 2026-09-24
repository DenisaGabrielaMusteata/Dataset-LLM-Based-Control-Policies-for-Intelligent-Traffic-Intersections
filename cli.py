import csv
from pathlib import Path
import argparse

from netgen import generate_grid_network, generate_osm_network
from routes import generate_random_routes
from config import write_sumocfg
from runner import run_sumo


def append_dataset_row(manifest_path: Path, params: dict, metrics: dict):
    """Append one scenario row to dataset.csv (create with header if missing)."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not manifest_path.exists()

    fields = [
        "scenario_path", "kind",
        "grid_size", "edge_length", "speed", "lanes", "turn_lanes",
        "osm_file",
        "flows", "end", "seed", "min_distance",
        "step_length", "gui",
        "departed", "arrived",
    ]

    with manifest_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if is_new:
            w.writeheader()
        row = {
            "scenario_path": str(params["outdir"]),
            "kind": params["kind"],
            "grid_size": params.get("grid_size", ""),
            "edge_length": params.get("edge_length", ""),
            "speed": params.get("speed", ""),
            "lanes": params.get("lanes", ""),
            "turn_lanes": params.get("turn_lanes", False),
            "osm_file": str(params.get("osm_file", "") or ""),
            "flows": params["flows"],
            "end": params["end"],
            "seed": params["seed"],
            "min_distance": params["min_distance"],
            "step_length": params["step_length"],
            "gui": params["gui"],
            "departed": metrics.get("departed", ""),
            "arrived": metrics.get("arrived", ""),
        }
        w.writerow(row)