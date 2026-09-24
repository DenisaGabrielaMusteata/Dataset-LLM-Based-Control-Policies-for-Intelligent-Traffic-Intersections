# process_dataset.py
from pathlib import Path
import json, csv
import xml.etree.ElementTree as ET

def _safe_int(x, default=0):
    try:
        return int(x)
    except:
        return default

def _safe_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default

def summarize_sumo_scenario(scen_dir: Path) -> dict:
    scen_dir = Path(scen_dir)
    net_path   = scen_dir / "net.net.xml"
    rou_path   = scen_dir / "routes.rou.xml"
    trips_path = scen_dir / "trips.trips.xml"
    cfg_path   = scen_dir / "scenario.sumocfg"
    met_path   = scen_dir / "metrics.csv"
    met_det    = scen_dir / "metrics_detailed.csv"

    net_info = {"edges":0, "lanes":0, "junctions":0, "tls":0, "lane_speeds_mps_stats":{}}
    if net_path.exists():
        root = ET.parse(net_path).getroot()
        edges = [e for e in root.findall(".//edge") if not e.get("id","").startswith(":")]
        net_info["edges"] = len(edges)
        lanes = root.findall(".//lane")
        net_info["lanes"] = len(lanes)
        net_info["junctions"] = len(root.findall(".//junction"))
        net_info["tls"] = sum(1 for j in root.findall(".//junction") if j.get("type") == "traffic_light")
        speeds = []
        for ln in lanes:
            sp = _safe_float(ln.get("speed"))
            if sp > 0:
                speeds.append(sp)
        if speeds:
            speeds.sort()
            n = len(speeds)
            net_info["lane_speeds_mps_stats"] = {
                "min": speeds[0],
                "p50": speeds[n//2],
                "max": speeds[-1],
                "avg": sum(speeds)/n
            }

    trips_info = {"trips": 0}
    if trips_path.exists():
        root = ET.parse(trips_path).getroot()
        trips_info["trips"] = len(root.findall(".//trip"))

    routes_info = {"vehicles":0}
    if rou_path.exists():
        root = ET.parse(rou_path).getroot()
        routes_info["vehicles"] = len(root.findall(".//vehicle"))

    metrics = {"departed": None, "arrived": None}
    if met_path.exists():
        try:
            with met_path.open("r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("metric") == "departed_total":
                        metrics["departed"] = _safe_int(row.get("value"))
                    if row.get("metric") == "arrived_total":
                        metrics["arrived"] = _safe_int(row.get("value"))
        except:
            pass

    detail = {}
    if met_det.exists():
        times = []
        try:
            with met_det.open("r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    times.append(_safe_int(row.get("travel_time_steps")))
            if times:
                times.sort()
                n = len(times)
                detail = {
                    "avg_travel_time_steps": sum(times)/n,
                    "median_travel_time_steps": times[n//2],
                    "min_travel_time_steps": times[0],
                    "max_travel_time_steps": times[-1],
                    "count_arrived": n
                }
        except:
            pass

    instruction = (
        "Given a SUMO scenario described by: "
        f"{net_info['edges']} edges, {net_info['lanes']} lanes, {net_info['junctions']} junctions, "
        f"{net_info['tls']} signalized junctions; {routes_info['vehicles']} vehicles with {trips_info['trips']} trips. "
        "Summarize the simulation outcome."
    )

    summary_parts = []
    if metrics["departed"] is not None:
        summary_parts.append(f"Departed={metrics['departed']}")
    if metrics["arrived"] is not None:
        summary_parts.append(f"Arrived={metrics['arrived']}")
    if detail:
        summary_parts.append(f"AvgTravelTimeSteps={detail['avg_travel_time_steps']:.2f}")
        summary_parts.append(f"Median={detail['median_travel_time_steps']}")
        summary_parts.append(f"Min={detail['min_travel_time_steps']}")
        summary_parts.append(f"Max={detail['max_travel_time_steps']}")
        summary_parts.append(f"CountArrived={detail['count_arrived']}")

    target = ", ".join(summary_parts) if summary_parts else "No metrics available."

    return {
        "scenario_path": str(scen_dir.resolve()),
        "network": net_info,
        "trips": trips_info,
        "routes": routes_info,
        "metrics": metrics,
        "metrics_detailed": detail,
        "llm_sample": {
            "instruction": instruction,
            "output": target
        }
    }

def write_jsonl_from_scenarios(root: Path, out_path: Path):
    root = Path(root)
    out_path = Path(out_path)
    samples = []
    scen_dirs = [p.parent for p in root.rglob("scenario.sumocfg")]
    if not scen_dirs and (root / "scenario.sumocfg").exists():
        scen_dirs = [root]
    for d in sorted(set(scen_dirs)):
        samples.append(summarize_sumo_scenario(d))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False))
            f.write("\n")
    return out_path, len(samples)
