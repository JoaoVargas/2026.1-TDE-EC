from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return f"Hello!"

@app.get("/{name}")
def read_root_param(name: str | None = "World"):
    return f"Hello, {name}!"

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
