from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from models.example import fetch_all_from_table

app = FastAPI()
templates = Jinja2Templates(directory="./templates")


@app.get("/")
def get_root():
    return f"Hello!"


@app.get("/{name}")
def get_root_param(name: str | None = "World"):
    return f"Hello, {name}!"


@app.get("/test/{name}")
def get_test_param(request: Request, name: str):
    data = fetch_all_from_table(name)

    print(f"Fetched data from table '{name}': {data}")

    return templates.TemplateResponse(
        request,
        name="table.html",
        context={"request": request, "name": name, "data": data},
    )
