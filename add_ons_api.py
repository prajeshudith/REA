from fastapi import FastAPI
import os
import json

app = FastAPI()

json_paths = {
    "product owner": "product owner_agent_steps.json"
}

status_paths = {
    "product owner": "agent_started.txt"
}

@app.get("/status")
def get_status(agent_name: str):
    try:
        path = status_paths[agent_name]
        if os.path.exists(path):
            return {"status": "running"}
        else:
            return {"status": "stopped"}
    except:
        return {"status": "stopped"}

# To run: uvicorn main:app --reload
# Test: http://localhost:8000/search?path=/your/file/path


@app.get("/json")
def steps(agent_name: str):
    try:
        path = json_paths[agent_name]
        print(path)
        if os.path.exists(path):
            print("File exists!")
            with open(path, 'r', encoding="utf-8") as f:
                data = json.load(f)
            return {"data": data}
        else:
            {"data": {}}
    except:
        {"data": {}}