from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from ah import plugins
import asyncio
import uvicorn

def create_directories():
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
        Path(directory).mkdir(parents=True, exist_ok=True)

create_directories()

import mimetypes
mimetypes.add_type("application/javascript", ".js", True)

app = None

async def setup_app():
    global app
    app = FastAPI()
    app.mount("/static", StaticFiles(directory="static", follow_symlink=True), name="static")
    app.mount("/imgs", StaticFiles(directory="imgs"), name="imgs")

    from ah.log_router import router as log_router
    app.include_router(log_router)

    from routers.settings_router import router as settings_router
    app.include_router(settings_router)

    #from routers.command_router import router as command_router
    #app.include_router(command_router)

    from routers.plugin_router import router as plugin_router
    app.include_router(plugin_router)

    from routers.persona_router import router as persona_router
    app.include_router(persona_router)

    from routers.agent_router import router as agent_router
    app.include_router(agent_router)

    await plugins.load(app=app)

    return app

if __name__ == "__main__":
    #asyncio.run(plugins.load(app=app))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_app())
    uvicorn.run(app, host="0.0.0.0", port=8000, lifespan="on")
