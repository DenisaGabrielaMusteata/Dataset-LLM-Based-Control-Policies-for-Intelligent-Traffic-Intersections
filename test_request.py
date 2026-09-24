import requests

state = {
    "traffic_light": "red",
    "pedestrians_detected": True,
    "vehicle_speed": 30,
    "distance_to_intersection": 1
}

resp = requests.post(
    "http://127.0.0.1:8000/decide_action",
    json={"state": state}
)

print(resp.status_code)
print(resp.json())
