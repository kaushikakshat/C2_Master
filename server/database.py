import sqlite3
from datetime import datetime
import uuid

DB_NAME = "agents.db"


# -----------------------
# Initialize Database
# -----------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            hostname TEXT,
            username TEXT,
            os TEXT,
            ip TEXT,
            last_seen TEXT
        )
    """)

    conn.commit()
    conn.close()


# -----------------------
# Register Agent
# -----------------------
def register_agent(agent_data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    agent_id = str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO agents VALUES (?, ?, ?, ?, ?, ?)
    """, (
        agent_id,
        agent_data.get("hostname"),
        agent_data.get("username"),
        agent_data.get("os"),
        agent_data.get("ip"),
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

    return agent_id


# -----------------------
# Update Beacon Time
# -----------------------
def update_last_seen(agent_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE agents
        SET last_seen = ?
        WHERE agent_id = ?
    """, (
        datetime.utcnow().isoformat(),
        agent_id
    ))

    conn.commit()
    conn.close()


# -----------------------
# Fetch Agents
# -----------------------
def get_all_agents():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM agents")
    rows = cursor.fetchall()

    conn.close()

    agents = []
    for row in rows:
        agents.append({
            "agent_id": row[0],
            "hostname": row[1],
            "username": row[2],
            "os": row[3],
            "ip": row[4],
            "last_seen": row[5]
        })

    return agents
