# llm_server.py

import json
from typing import Dict, Any

import torch
from fastapi import FastAPI, Body
from pydantic import BaseModel
import uvicorn

from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


BASE_MODEL_DIR = r"C:\Users\Denisa\Desktop\ACCS\Smart-Intersections-with-LLM\outputs\models\Qwen2.5-1.5B-Instruct"
ADAPTER_DIR    = r"C:\Users\Denisa\Desktop\ACCS\Smart-Intersections-with-LLM\models\qwen2_1_5b_lora_finetuned\checkpoint-12000"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_DIR, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_DIR,
    torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
    low_cpu_mem_usage=True,
    trust_remote_code=True,
)
base_model.to(device)

print("Loading LoRA adapter...")
model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
model.to(device)
model.eval()

print("Model + LoRA ready.")

class VehicleState(BaseModel):
    vehicle_id: int
    time: float
    speed: float
    position: Dict[str, float]
    lane_id: str
    speed_limit: float


class ControlAction(BaseModel):
    next_phase: int
    phase_duration: float
    accel: float


app = FastAPI()

def build_prompt_from_state(state: VehicleState) -> str:
    instr_dict = {
        "vehicle_id": state.vehicle_id,
        "time": state.time,
        "speed": state.speed,
        "position": state.position,
        "lane_id": state.lane_id,
        "speed_limit": state.speed_limit,
    }
    instr_json = json.dumps(instr_dict, ensure_ascii=False)
    prompt = f"State:\n{instr_json}\n\nAction:\n"
    return prompt



def run_llm(prompt: str) -> Dict[str, Any]:
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=False,      
            num_beams=1,
            pad_token_id=tokenizer.eos_token_id,
        )

    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)


    if "Action:" in full_text:
        action_part = full_text.split("Action:", 1)[1].strip()
    else:
        action_part = full_text

    start = action_part.find("{")
    end   = action_part.rfind("}")
    if start != -1 and end != -1 and end > start:
        json_str = action_part[start:end+1]
        try:
            action = json.loads(json_str)
            return action
        except json.JSONDecodeError:
            pass

    return {
        "next_phase": 0,
        "phase_duration": 10.0,
    }



@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/decide", response_model=ControlAction)
def decide(state: VehicleState):
    prompt = build_prompt_from_state(state)
    action_dict = run_llm(prompt)

    next_phase = int(action_dict.get("next_phase", 0))
    phase_duration = float(action_dict.get("phase_duration", 10.0))

    accel = float(action_dict.get("accel", 0.0))

    if "accel" not in action_dict:
        ratio = state.speed / max(state.speed_limit, 0.1)
        if ratio < 0.7:
            accel = 1.0       
        elif ratio < 1.0:
            accel = 0.2    
        else:
            accel = -1.0    

    print("[LLM_SERVER] state=", state.dict())
    print("[LLM_SERVER] action_dict=", action_dict)
    print("[LLM_SERVER] final accel=", accel)

    return ControlAction(
        next_phase=next_phase,
        phase_duration=phase_duration,
        accel=accel,
    )


if __name__ == "__main__":
    # host și port trebuie (127.0.0.1:8000)
    uvicorn.run(app, host="127.0.0.1", port=8000)
