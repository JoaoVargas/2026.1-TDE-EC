from fastapi import FastAPI

from models.example import fetch_all_from_table

app = FastAPI()


@app.get("/")
def get_root():
    return f"Hello!"

@app.get("/{name}")
def get_root_param(name: str | None = "World"):
    return f"Hello, {name}!"

@app.get("/test/{name}")
def get_test_param(name: str):
    print(fetch_all_from_table(name))    

    return {}
