import json
import os
import requests
from datetime import datetime

FOG_BASE_URL = "http://<FOG_IP>:8000"

DEVICE_ID = "jetson_edge_1"
ROOM_ID = "classroom_101"

def log_event(event_type, data):
    data.update({
        "event_type": event_type,
        "timestamp": datetime.now().isoformat()
    })

    os.makedirs("logs", exist_ok=True)
    with open("logs/events.json", "a") as f:
        f.write(json.dumps(data) + "\n")

    send_to_fog(event_type, data)

def send_to_fog(event_type, data):
    if event_type == "occupancy":
        payload = {
            "device_id": DEVICE_ID,
            "room_id": ROOM_ID,
            "person_count": data.get("count", 0)
        }
        response = requests.post(f"{FOG_BASE_URL}/occupancy", json=payload, timeout=3)
    elif event_type == "intrusion":
        payload = {
            "device_id": DEVICE_ID,
            "room_id": ROOM_ID,
            "alert_type": "unauthorized_access",
            "description": data.get("alert", "")
        }
        response = requests.post(f"{FOG_BASE_URL}/intrusion", json=payload, timeout=3)
    else:
        print(f"Unknown event type: {event_type}")
        return

def is_school_hour():
    hour = datetime.now().hour
    return True 
