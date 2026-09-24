from __future__ import annotations
from pathlib import Path
import json, random

def ensure_rollouts(root: Path, log_fn, *, sample_every=1, max_steps=None, gui=False) -> int:
    root = Path(root)
    total = 0
    cfgs = list(root.rglob("scenario.sumocfg"))
    if not cfgs:
        print(f"[warn] no scenario.sumocfg under {root.resolve()}")
        return 0

    for cfg in cfgs:
        scen = cfg.parent
        out_jsonl = scen / "vehicle_steps.jsonl"
        if out_jsonl.exists():
            print(f"[skip] {scen.name}: {out_jsonl.name} already present")
            continue
        print(f"[run]  {scen.name}")
        res = log_fn(
            outdir=scen,
            cfg_path=cfg,
            jsonl_path=out_jsonl,
            gui=gui,
            sample_every=sample_every,
            max_steps=max_steps,
            include_route=True,
        )
        print(f"[ok]  {res['steps_written']} step-records → {out_jsonl}")
        total += int(res.get("steps_written", 0))
    return total

def concat_rollouts(root: Path, out_path: Path) -> int:
    root = Path(root)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open("w", encoding="utf-8") as out_f:
        for js in root.rglob("vehicle_steps.jsonl"):
            with js.open("r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not s: 
                        continue
                    out_f.write(s + "\n")
                    count += 1
    print(f"[OK] concatenated {count} step-records → {out_path}")
    return count

def to_instruction_output(src_jsonl: Path, train_out: Path, val_out: Path, *, val_ratio=0.1, seed=42) -> tuple[int,int]:
    src_jsonl = Path(src_jsonl)
    samples = []
    with src_jsonl.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s: 
                continue
            rec = json.loads(s)
            obs = {
                "step": rec["step"],
                "veh_id": rec["veh_id"],
                "edge_id": rec["edge_id"],
                "lane_index": rec["lane_index"],
                "lane_pos": rec["lane_pos"],
                "speed": rec["speed"],
                "accel": rec["accel"],
                "waiting_time": rec["waiting_time"],
                "leader_gap": rec.get("leader_gap"),
                "tls_id": rec["next_tls"].get("tls_id",""),
                "tls_dist": rec["next_tls"].get("tls_dist"),
                "tls_state": rec["next_tls"].get("tls_state",""),
                "dest_edge": rec.get("dest_edge",""),
            }
            tgt = {
                "action_speed": rec["action_speed"],
                "action_lane":  rec["action_lane"],
            }
            samples.append({"instruction": json.dumps(obs), "output": json.dumps(tgt)})

    rnd = random.Random(seed)
    rnd.shuffle(samples)
    k = max(1, int(val_ratio * len(samples)))
    val, train = samples[:k], samples[k:]

    train_out = Path(train_out); val_out = Path(val_out)
    train_out.parent.mkdir(parents=True, exist_ok=True)
    with train_out.open("w", encoding="utf-8") as f:
        for it in train:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    with val_out.open("w", encoding="utf-8") as f:
        for it in val:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print(f"[OK] train={len(train)} → {train_out}")
    print(f"[OK] val={len(val)}   → {val_out}")
    return len(train), len(val)

def preview_jsonl(path: Path, n=3):
    import itertools
    path = Path(path)
    print(f"\n== {path} ==")
    with path.open("r", encoding="utf-8") as f:
        for line in itertools.islice(f, n):
            print(json.loads(line))

def count_scenarios(root: Path) -> int:
    return len(list(Path(root).rglob("scenario.sumocfg")))
