import os
from pathlib import Path
from sumo_env import ensure_tools_in_path, find_sumo


def run_sumo(outdir: Path, cfg: Path, gui: bool = False) -> dict:
    ensure_tools_in_path()
    import traci  

    binary = find_sumo("sumo-gui" if gui else "sumo")

    cwd = os.getcwd()
    os.chdir(outdir)

    departed = 0
    arrived = 0

    try:
        cmd = [binary, "-c", cfg.name, "--no-step-log", "true"]
        print(f"[runner] Starting SUMO {'(GUI)' if gui else '(CLI)'} with {cfg.name}")
        traci.start(cmd)

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            departed += traci.simulation.getDepartedNumber()
            arrived += traci.simulation.getArrivedNumber()

        traci.close()
        print(f"[runner] Simulation finished: departed={departed}, arrived={arrived}")

    finally:
        os.chdir(cwd)

    return {"departed": departed, "arrived": arrived}

