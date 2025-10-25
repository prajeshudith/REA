from fastapi import FastAPI
import os
import json

app = FastAPI()

@app.get("/status")
def get_status():
    if os.path.exists("agent_started.txt"):
        return {"status": "running"}
    else:
        return {"status": "stopped"}

# To run: uvicorn main:app --reload
# Test: http://localhost:8000/search?path=/your/file/path

json_paths = {
    "product owner": "product owner_agent_steps.json"
}

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