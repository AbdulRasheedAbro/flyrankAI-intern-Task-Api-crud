"""
Task API — a small in-memory CRUD API built with FastAPI.

Run with:  uvicorn main:app --reload --port 8000
Docs at:   http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A small in-memory to-do list API — the four CRUD operations over HTTP.",
)


# ---------- Data models ----------

class Task(BaseModel):
    id: int
    title: str
    done: bool = False


class TaskCreate(BaseModel):
    title: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


# ---------- In-memory "database" ----------
# Data lives only in this list. It resets every time the server restarts —
# that's expected at this stage (see the mortality experiment in the brief).

tasks: List[dict] = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Write README", "done": False},
    {"id": 3, "title": "Push to GitHub", "done": True},
]
next_id = 4


def find_task(task_id: int):
    return next((t for t in tasks if t["id"] == task_id), None)


# ---------- Stage 1: root and health ----------

@app.get("/", summary="API info")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


# ---------- Stage 2: read ----------

@app.get("/tasks", summary="List all tasks", response_model=List[Task])
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}", summary="Get a single task")
def get_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


# ---------- Stage 3: create ----------

@app.post("/tasks", status_code=201, summary="Create a task")
def create_task(payload: TaskCreate):
    global next_id
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="title is required and cannot be empty")

    task = {"id": next_id, "title": payload.title.strip(), "done": False}
    tasks.append(task)
    next_id += 1
    return task


# ---------- Stage 4: update & delete ----------

@app.put("/tasks/{task_id}", summary="Replace a task's title/done")
def update_task(task_id: int, payload: TaskUpdate):
    task = find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="Provide at least title or done to update")

    if payload.title is not None:
        if not payload.title.strip():
            raise HTTPException(status_code=400, detail="title cannot be empty")
        task["title"] = payload.title.strip()

    if payload.done is not None:
        task["done"] = payload.done

    return task


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    tasks.remove(task)
    return None


# ---------- Extras (optional, bonus) ----------

@app.get("/stats", summary="Task counts")
def stats():
    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    return {"total": total, "done": done, "open": total - done}


@app.post("/reset", summary="Reset to the 3 example tasks")
def reset():
    global tasks, next_id
    tasks = [
        {"id": 1, "title": "Buy milk", "done": False},
        {"id": 2, "title": "Write README", "done": False},
        {"id": 3, "title": "Push to GitHub", "done": True},
    ]
    next_id = 4
    return {"status": "reset"}
