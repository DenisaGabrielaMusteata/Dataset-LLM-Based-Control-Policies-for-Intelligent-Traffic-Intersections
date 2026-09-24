
import csv
from itertools import combinations, product

APPROACHES = ["N", "E", "S", "W"]           
MANEUVERS  = ["right", "straight", "left"]  

MAX_SCENARIOS_PER_K = {1: 12, 2: 64, 3: 96, 4: 96}

WIDE_PATH = "intersectie_scenarii_wide.csv"
LONG_PATH = "intersectie_scenarii_long.csv"

def edge_to_from(approach, maneuver):
    mapping = {
        ("N","right"): ("N_in","E_out"),
        ("N","straight"): ("N_in","S_out"),
        ("N","left"): ("N_in","W_out"),
        ("E","right"): ("E_in","S_out"),
        ("E","straight"): ("E_in","W_out"),
        ("E","left"): ("E_in","N_out"),
        ("S","right"): ("S_in","W_out"),
        ("S","straight"): ("S_in","N_out"),
        ("S","left"): ("S_in","E_out"),
        ("W","right"): ("W_in","N_out"),
        ("W","straight"): ("W_in","E_out"),
        ("W","left"): ("W_in","S_out"),
    }
    return mapping[(approach, maneuver)]

right_of = {"N":"E", "E":"S", "S":"W", "W":"N"}   
opposite = {"N":"S", "E":"W", "S":"N", "W":"E"}   

def blockers_for(vehicle, others):
    vid, v_appr, v_man = vehicle["id"], vehicle["approach"], vehicle["maneuver"]
    r_appr = right_of[v_appr]
    o_appr = opposite[v_appr]
    blockers = []
    for o in others:
        if o["id"] == vid:
            continue
        if o["approach"] == r_appr:
            blockers.append(o["id"])
            continue
        if v_man == "left" and o["approach"] == o_appr and o["maneuver"] in ("straight", "right"):
            blockers.append(o["id"])
    # unicizare păstrând ordinea
    seen = set()
    out = []
    for b in blockers:
        if b not in seen:
            out.append(b)
            seen.add(b)
    return out

def decision_for_reference(vehicles, ref_id="masina_referinta"):
    id2veh = {v["id"]: v for v in vehicles}
    all_blockers = {v["id"]: blockers_for(v, vehicles) for v in vehicles}
    ref_blockers = all_blockers[ref_id]

    if not ref_blockers:
        return ("GO", "", "Nu ai vehicule cu prioritate în fața ta → poți trece.")

    everyone_blocked = all(bool(lst) for lst in all_blockers.values())
    if everyone_blocked:
        return ("WAIT_ALL", ",".join(ref_blockers),
                "Blocaj circular (toți se cedează reciproc). Aștepți o rezolvare implicită.")

    ref = id2veh[ref_id]
    reasons = []
    r_appr = right_of[ref["approach"]]
    o_appr = opposite[ref["approach"]]
    for bid in ref_blockers:
        b = id2veh[bid]
        if b["approach"] == r_appr:
            reasons.append(f"{bid} vine din dreapta (din {r_appr})")
        if ref["maneuver"] == "left" and b["approach"] == o_appr and b["maneuver"] in ("straight","right"):
            reasons.append(f"{bid} este din sens opus și are prioritate față de virajul la stânga")
    expl = " ; ".join(dict.fromkeys(reasons)) if reasons else "Ai vehicule cu prioritate în fața ta."
    return ("YIELD", ",".join(ref_blockers), expl)

def build_vehicle(vid, approach, maneuver, arrival_time_s=0):
    fr, to = edge_to_from(approach, maneuver)
    return {
        "id": vid,
        "approach": approach,
        "maneuver": maneuver,
        "from_edge": fr,
        "to_edge": to,
        "arrival_time_s": arrival_time_s
    }

def generate_and_write():
    wide_fields = [
        "scenario_id",
        "masina_referinta_id", "masina_referinta_action", "masina_referinta_yield_to", "masina_referinta_explanation",
        "v1_id","v1_approach","v1_maneuver","v1_from_edge","v1_to_edge","v1_arrival_time_s",
        "v2_id","v2_approach","v2_maneuver","v2_from_edge","v2_to_edge","v2_arrival_time_s",
        "v3_id","v3_approach","v3_maneuver","v3_from_edge","v3_to_edge","v3_arrival_time_s",
        "v4_id","v4_approach","v4_maneuver","v4_from_edge","v4_to_edge","v4_arrival_time_s",
    ]
    wide_rows = []

    long_fields = [
        "scenario_id", "vehicle_id", "approach", "maneuver", "from_edge", "to_edge", "arrival_time_s",
        "referinta_id", "referinta_action", "referinta_yield_to", "referinta_explanation"
    ]
    long_rows = []

    sid_counter = 1
    for k in range(1, 5):
        for approaches in combinations(APPROACHES, k):
            maneuvers_product = list(product(MANEUVERS, repeat=k))
            cap = MAX_SCENARIOS_PER_K.get(k, len(maneuvers_product))
            count = 0

            for mans in maneuvers_product:
                if count >= cap:
                    break

                vehicles = []
                for i, (appr, man) in enumerate(zip(approaches, mans)):
                    vid = "masina_referinta" if i == 0 else f"veh{i}"
                    vehicles.append(build_vehicle(vid, appr, man, arrival_time_s=0))

                action, yield_to, explanation = decision_for_reference(vehicles, ref_id="masina_referinta")

                base = {
                    "scenario_id": f"S{sid_counter}",
                    "masina_referinta_id": "masina_referinta",
                    "masina_referinta_action": action,
                    "masina_referinta_yield_to": yield_to,
                    "masina_referinta_explanation": explanation,
                }
                for idx in range(1, 5):
                    base[f"v{idx}_id"] = ""
                    base[f"v{idx}_approach"] = ""
                    base[f"v{idx}_maneuver"] = ""
                    base[f"v{idx}_from_edge"] = ""
                    base[f"v{idx}_to_edge"] = ""
                    base[f"v{idx}_arrival_time_s"] = ""

                for idx, v in enumerate(vehicles, start=1):
                    base[f"v{idx}_id"] = v["id"]
                    base[f"v{idx}_approach"] = v["approach"]
                    base[f"v{idx}_maneuver"] = v["maneuver"]
                    base[f"v{idx}_from_edge"] = v["from_edge"]
                    base[f"v{idx}_to_edge"] = v["to_edge"]
                    base[f"v{idx}_arrival_time_s"] = v["arrival_time_s"]

                wide_rows.append(base)

                for v in vehicles:
                    long_rows.append({
                        "scenario_id": f"S{sid_counter}",
                        "vehicle_id": v["id"],
                        "approach": v["approach"],
                        "maneuver": v["maneuver"],
                        "from_edge": v["from_edge"],
                        "to_edge": v["to_edge"],
                        "arrival_time_s": v["arrival_time_s"],
                        "referinta_id": "masina_referinta",
                        "referinta_action": action,
                        "referinta_yield_to": yield_to,
                        "referinta_explanation": explanation,
                    })

                sid_counter += 1
                count += 1

    with open(WIDE_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=wide_fields)
        w.writeheader()
        w.writerows(wide_rows)

    with open(LONG_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=long_fields)
        w.writeheader()
        w.writerows(long_rows)

    print(f"OK: {len(wide_rows)} scenarii în {WIDE_PATH}")
    print(f"OK: {len(long_rows)} rânduri (vehicule) în {LONG_PATH}")

if __name__ == "__main__":
    generate_and_write()
