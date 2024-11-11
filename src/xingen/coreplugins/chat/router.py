from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sse_starlette.sse import EventSourceResponse
from .models import MessageParts
from .services import init_chat_session, send_message_to_agent, subscribe_to_agent_messages, get_chat_history
from lib.templates import render
from lib.plugins import list_enabled
import nanoid
from lib.providers.commands import *
import asyncio
from typing import List


router = APIRouter()

# Global dictionary to store tasks
tasks = {}


# need to serve persona images from ./personas/local/[persona_name]/avatar.png
@router.get("/chat/personas/{persona_name}/avatar.png")
async def get_persona_avatar(persona_name: str):
    # need to serve the image from the persona
    # just read in the file and return it
    with open(f"personas/local/{persona_name}/avatar.png", "rb") as f:
        return f.read()
    

@router.get("/chat/{log_id}/events")
async def chat_events(log_id: str):
    return EventSourceResponse(await subscribe_to_agent_messages(log_id))

@router.post("/chat/{log_id}/{task_id}/cancel")
async def cancel_chat(log_id: str, task_id: str):
    if task_id in tasks:
        task = tasks[task_id]
        task.cancel()
        del tasks[task_id]
        return {"status": "ok", "message": "Task cancelled successfully"}
    else:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/chat/{log_id}/send")
async def send_message(request: Request, log_id: str, message_parts: List[MessageParts] ):
    user = request.state.user

    task = asyncio.create_task(send_message_to_agent(log_id, message_parts, user=user))
    
    task_id = nanoid.generate()
    
    tasks[task_id] = task
    
    return {"status": "ok", "task_id": task_id}

@router.get("/agent/{agent_name}", response_class=HTMLResponse)
async def get_chat_html(agent_name: str):
    log_id = nanoid.generate()
    plugins = list_enabled()
    print(f"Init chat with {agent_name}")
    await init_chat_session(agent_name, log_id)
    return RedirectResponse(f"/session/{agent_name}/{log_id}")

@router.get("/history/{log_id}")
async def chat_history(log_id: str):
    history = await get_chat_history(log_id)
    return history

@router.get("/session/{agent_name}/{log_id}")
async def chat_history(request: Request, agent_name: str, log_id: str):
    plugins = list_enabled()
    user = request.state.user
    html = await render('chat', {"log_id": log_id, "agent_name": agent_name, "user": user})
    return HTMLResponse(html)


