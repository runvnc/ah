from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path
from .lib import plugins
import asyncio
import uvicorn
from termcolor import colored

def get_project_root():
    return Path(__file__).parent

def create_directories():
    root = get_project_root()
    directories = [
        "imgs",
        "data/chat",
        "models",
        "models/face",
        "models/llm",
        "static/personas",
        "personas",
        "personas/local",
        "personas/shared",
    ]
    for directory in directories:
        (root / directory).mkdir(parents=True, exist_ok=True)

create_directories()

import mimetypes
mimetypes.add_type("application/javascript", ".js", True)

app = None
templates = None

async def setup_app():
    global app, templates
    app = FastAPI()
    
    
    root = get_project_root()
    app.mount("/static", StaticFiles(directory=str(root / "static"), follow_symlink=True), name="static")
    app.mount("/imgs", StaticFiles(directory=str(root / "imgs")), name="imgs")

    await plugins.load(app=app)

    return app

def main():
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(setup_app())
    uvicorn.run(app, host="0.0.0.0", port=8010, lifespan="on")

if __name__ == "__main__":
    main()
