from __future__ import annotations
import os, json, time, uuid
from pathlib import Path
from typing import Dict, Any, Optional

def _safe(v, alt=None): return v if v is not None else alt

def _speed_action(prev_speed: float, speed: float, th_up=0.3, th_dn=-0.3) -> str:
    dv = speed - prev_speed
    if dv > th_up: return "accelerate"
    if dv < th_dn: return "brake"
    return "keep_speed"

def _lane_action(prev_lane: Optional[int], lane: Optional[int]) -> str:
    if prev_lane is None or lane is None: return "keep_lane"
    if lane > prev_lane:  return "lane_right"
    if lane < prev_lane:  return "lane_left"
    return "keep_lane"

def _flatten_next_tls(next_tls: list) -> Dict[str, Any]:

    if not next_tls:
        return {"tls_id": "", "tls_dist": None, "tls_state": "", "tls_next_switch": None}

    t = next_tls[0]
    if not isinstance(t, (list, tuple)) or len(t) < 3:
        return {"tls_id": "", "tls_dist": None, "tls_state": "", "tls_next_switch": None}

    tls_id = str(t[0])

    def _num(x):
        try:
            return float(x)
        except Exception:
            return None

    dist = _num(t[1])

    if len(t) == 3:
        state = str(t[2])
        next_sw = None
        return {"tls_id": tls_id, "tls_dist": dist, "tls_state": state, "tls_next_switch": next_sw}

    c, d = t[2], t[3]

    def _looks_like_state(x):
        return isinstance(x, str) and len(x) <= 3

    if _looks_like_state(c) and not _looks_like_state(d):
        state = str(c)
        try:
            next_sw = int(d)
        except Exception:
            next_sw = None
    elif _looks_like_state(d) and not _looks_like_state(c):
        state = str(d)
        try:
            next_sw = int(c)
        except Exception:
            next_sw = None
    else:
        state = str(c) if _looks_like_state(c) else (str(d) if _looks_like_state(d) else "")
        next_sw = None
        for x in (c, d):
            try:
                next_sw = int(x)  
                break
            except Exception:
                continue

    return {"tls_id": tls_id, "tls_dist": dist, "tls_state": state, "tls_next_switch": next_sw}


def _leader_tuple(leader) -> tuple[str, Optional[float]]:
    if not leader: return ("", None)
    vid, gap = leader
    return (str(vid), float(gap))

def _force_close_all_traci():
    try:
        import traci
        for lab in list(traci.getConnectionLabels()):
            try:
                traci.switch(lab); traci.close(False)
            except Exception:
                pass
    except Exception:
        pass

def log_rollout_jsonl(
    outdir: Path,
    cfg_path: Path,
    jsonl_path: Path,
    gui: bool = False,
    sample_every: int = 1,
    max_steps: Optional[int] = None,
    include_route: bool = True,
    label: Optional[str] = None,
    retries: int = 3,
) -> Dict[str, Any]:
    from sumo_env import ensure_tools_in_path, find_sumo
    ensure_tools_in_path()
    import traci

    outdir     = Path(outdir)
    cfg_path   = Path(cfg_path)
    jsonl_path = Path(jsonl_path)
    binary     = find_sumo("sumo-gui" if gui else "sumo")

    base_label = label or f"run-{outdir.name}-{os.getpid()}"
    attempt = 0
    connected = False
    actual_label = base_label

    cwd = os.getcwd()
    os.chdir(outdir)
    out_file = Path(jsonl_path.name)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        while attempt <= retries and not connected:
            try:
                if actual_label in traci.getConnectionLabels():
                    traci.switch(actual_label)
                    traci.close(False)
                    time.sleep(0.05)
            except Exception:
                pass

            try:
                traci.start([binary, "-c", cfg_path.name, "--no-step-log", "true"], label=actual_label)
                traci.switch(actual_label)
                connected = True
            except Exception:
                attempt += 1
                actual_label = f"{base_label}-{uuid.uuid4().hex[:6]}"
                time.sleep(0.05)

        if not connected:
            _force_close_all_traci()
            traci.start([binary, "-c", cfg_path.name, "--no-step-log", "true"], label=actual_label)
            traci.switch(actual_label)

        prev_speed: Dict[str, float] = {}
        prev_lane_idx: Dict[str, int] = {}
        step = 0
        written = 0

        with out_file.open("w", encoding="utf-8") as f:
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                step += 1
                if max_steps and step > max_steps:
                    break

                veh_ids_now = list(traci.vehicle.getIDList())
                for vid in veh_ids_now:
                    if vid not in prev_speed:
                        prev_speed[vid] = float(_safe(traci.vehicle.getSpeed(vid), 0.0))
                    if vid not in prev_lane_idx:
                        prev_lane_idx[vid] = _safe(traci.vehicle.getLaneIndex(vid))

                if (step % sample_every) != 0:
                    for vid in veh_ids_now:
                        prev_speed[vid] = float(_safe(traci.vehicle.getSpeed(vid), 0.0))
                        prev_lane_idx[vid] = _safe(traci.vehicle.getLaneIndex(vid))
                    continue

                for vid in veh_ids_now:
                    speed    = float(_safe(traci.vehicle.getSpeed(vid), 0.0))
                    accel    = float(_safe(traci.vehicle.getAcceleration(vid), 0.0))
                    angle    = float(_safe(traci.vehicle.getAngle(vid), 0.0))
                    wait     = float(_safe(traci.vehicle.getWaitingTime(vid), 0.0))
                    edge_id  = str(_safe(traci.vehicle.getRoadID(vid), ""))
                    lane_id  = str(_safe(traci.vehicle.getLaneID(vid), ""))
                    lane_ix  = _safe(traci.vehicle.getLaneIndex(vid))
                    lane_pos = float(_safe(traci.vehicle.getLanePosition(vid), 0.0))

                    route_idx = _safe(traci.vehicle.getRouteIndex(vid), None)
                    route = traci.vehicle.getRoute(vid) if include_route else []
                    route_len = len(route) if route else None
                    dest_edge = route[-1] if route else ""

                    tls_obj  = _flatten_next_tls(traci.vehicle.getNextTLS(vid))
                    leader_id, leader_gap = _leader_tuple(traci.vehicle.getLeader(vid, dist=60.0))

                    act_speed = _speed_action(prev_speed.get(vid, speed), speed)
                    act_lane  = _lane_action(prev_lane_idx.get(vid), lane_ix)

                    rec = {
                        "scenario": str(outdir.resolve()),
                        "step": step,
                        "veh_id": vid,
                        "edge_id": edge_id,
                        "lane_id": lane_id,
                        "lane_index": lane_ix,
                        "lane_pos": lane_pos,
                        "speed": speed,
                        "accel": accel,
                        "angle": angle,
                        "waiting_time": wait,
                        "route_index": route_idx,
                        "route_len": route_len,
                        "dest_edge": dest_edge,
                        "leader_id": leader_id,
                        "leader_gap": leader_gap,
                        "next_tls": tls_obj,
                        "action_speed": act_speed,
                        "action_lane": act_lane,
                    }
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    written += 1

                    prev_speed[vid] = speed
                    prev_lane_idx[vid] = lane_ix

        try:
            traci.switch(actual_label); traci.close(False)
        except Exception:
            pass

    finally:
        try:
            import traci as _t
            if actual_label in _t.getConnectionLabels():
                _t.switch(actual_label); _t.close(False)
        except Exception:
            pass
        os.chdir(cwd)

    return {"steps_written": written, "jsonl": str(out_file), "label": actual_label}
