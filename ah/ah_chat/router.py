from fastapi import APIRouter
import traceback
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from ..chatlog import ChatLog
from ..ah_agent import agent
from ..commands import command, command_manager
from ..services import service, service_manager
from ..hooks import hook, hook_manager
from ..chatcontext import ChatContext
from ..ah_templates import render_combined_template
from ..plugins import list_enabled
import asyncio
import os
import json
import nanoid
from termcolor import colored


router = APIRouter()

if os.environ.get('AH_DEFAULT_LLM'):
    current_model = os.environ.get('AH_DEFAULT_LLM')
else:
    current_model = 'llama3'


class Message(BaseModel):
    message: str

sse_clients = {}


@router.get("/chat/{log_id}/events")
async def chat_events(log_id: str):
    print("chat_log = ", log_id)
    context = ChatContext(command_manager, service_manager)
    await context.load_context(log_id)
    agent_ = agent.Agent(agent=context.agent, clear_model=True)
    await asyncio.sleep(0.15)
    asyncio.create_task(hook_manager.warmup())

    async def event_generator():
        queue = asyncio.Queue()
        if log_id not in sse_clients:
            sse_clients[log_id] = set()
        sse_clients[log_id].add(queue)
        try:
            while True:
                data = await queue.get()
                yield data
        except asyncio.CancelledError:
            sse_clients[log_id].remove(queue)
            if not sse_clients[log_id]:
                del sse_clients[log_id]

    return EventSourceResponse(event_generator())


@service()
async def agent_output(event: str, data: dict, context=None):
    log_id = context.log_id
    #print("Try to send event: ", event, data)
    if log_id in sse_clients:
        for queue in sse_clients[log_id]:
            #print("sending to sse client!")
            await queue.put({"event": event, "data": json.dumps(data)})

@service()
async def partial_command(command: str, chunk: str, params, context=None):
    agent_ = context.agent
    await context.agent_output("partial_command", { "command": command, "chunk": chunk, "params": params,
                                                    "persona": agent_['persona']['name'] })

@service()
async def running_command(command: str, context=None):
    print("*** running_command service call ***")
    agent_ = context.agent
    print("ok")
    await context.agent_output("running_command", { "command": command, "persona": agent_['persona']['name'] })

@service()
async def command_result(command: str, result, context=None):
    print("*** command_result service call ***")
    agent_ = context.agent
    print("ok")
    await context.agent_output("command_result", { "command": command, "result": result, "persona": agent_['persona']['name'] })


@router.put("/chat/{log_id}/{agent_name}")
async def init_chat(log_id: str, agent_name: str):
    context = ChatContext(command_manager, service_manager)
    context.log_id = log_id    
    context.agent = await service_manager.get_agent_data(agent_name)

    context.chat_log = ChatLog(log_id=log_id, agent=agent_name)
    context.save_context()
    agent_ = await service_manager.get_agent_data(agent_name)


@service()
async def insert_image(image_url, context=None):
    await context.agent_output("image", {"url": image_url})


@router.post("/chat/{log_id}/send")
async def send_message(log_id: str, message_data: Message):
    print("log_id = ", log_id)
    context = ChatContext(command_manager, service_manager)
    await context.load_context(log_id)
    # form_data = await request.form()
    user_avatar = 'static/user.png'
    assistant_avatar = f"static/agents/{context.agent['name']}/avatar.png"
    user_name = os.environ.get("AH_USER_NAME")
    message = message_data.message
    agent_ = agent.Agent(agent=context.agent)
    print('loaded context. data is: ', context.data)
    context.chat_log.add_message({"role": "user", "content": f"({user_name}): {message}"})

    @command()
    async def say(text="", done=True, context=None):
        """
        Say something to the user or chat room.
        One sentence per command. If you want to say multiple sentences, use multiple commands.

        Parameters:
        text - String. The text to say.
        done - Boolean. If true, the system will stop and wait for the user to reply.
                        If false, the system will expect more commands.
                        IMPORTANT: specify 'done: true' unless you have more SAY commands to run.
        
        IMPORTANT: if you have additional commands to run, return "done": false!
                   otherwise the user will have to ask you to just continue.

        ## Example 1
       
       (in this example we issue multiple 'say' commands, but are finished with commands after that,
        so use "done": true )

        [
            { "say": { "text": "Hello, user.", "done": true } },
            { "say": { "text": "How can I help you today?", "done": true } }
        ]

        (The system waits for the user reply)
       

        ## Example 2

        (In this example we want to acknowledge a request, but then issue another command,
         so we use "done": false )

        [
            { "say": { "text": "Sure, I can run that command", "done": false } }
        ]

        (The system replies with "continue" and expects more commands)

        [  { "some_command": {"arg1": "[some param]"  }  }]

        (The system now waits for the user reply)

        """
        print("say command called, text = ", text, "done = ", done)
        await context.agent_output("new_message", {"content": text,
                                   "agent": context.agent['name'] })
        #json_cmd = { "say": {"text": text } }

        #context.chat_log.add_message({"role": "assistant", "content": json.dumps(json_cmd)})
        if done:
            return "stop"
        else:
            return "continue"
            
    context.save_context()

    continue_processing = True
    iterations = 0
    while continue_processing and iterations < 3:
        iterations += 1
        continue_processing = False
        try:
            results = await agent_.chat_commands(current_model, context=context, messages=context.chat_log.get_recent())
            print("results from chat commands: ", colored(results, 'cyan'))
            out_results = []
            actual_results = False

            for result in results:
                if result['result'] is not None:
                    if result['result'] == 'continue':
                        out_results.append(result)
                        continue_processing = True
                    elif result['result'] == 'stop':
                        continue_processing = False
                    else:
                        out_results.append(result)
                        actual_results = True
                        continue_processing = True
                else:
                    continue_processing = False

            if actual_results:
                continue_processing = True

            if len(out_results) > 0:
                print("Processing iteration: ", iterations, "adding message")
                context.chat_log.add_message({"role": "user", "content": "[SYSTEM]:\n\n" + json.dumps(out_results, indent=4)})
        except Exception as e:
            print("Found an error in agent output: ")
            print(e)
            print(traceback.format_exc())
            continue_processing = False

    return {"status": "ok"}


@command()
async def json_encoded_md(markdown="", context=None):
    """
    Output some markdown text to the user or chat room.
    Use this for any somewhat longer text that the user can read and
    and doesn't necessarily need to be spoken out loud.

    You can write as much text/sentences etc. as you need.

    IMPORTANT: make sure everything is properly encoded as this is a JSON 
    command (such as escaping double quotes, escaping newlines, etc.)

    Parameters:

    markdown - String.  MUST BE PROPERLY JSON-encoded string! E.g. escape all double quotes, newlines, etc.

# Example

    [
        { "json_encoded_md": { "markdown": "## Section 1\\n\\n- item 1\\n- item 2" } }
    ]

# Example

    [
        { "json_encoded_md": { "markdown": "Here is a list:\\n\\n- item 1\\n- item 2\\n- line 3" }} 
    ]

    """
    await context.agent_output("new_message", {"content": markdown,
                                            "agent": context.agent['name'] })
    json_cmd = { "json_encoded_md": { "markdown": markdown } }

    #context.chat_log.add_message({"role": "assistant", "content": json.dumps(json_cmd)})


@router.get("/admin", response_class=HTMLResponse)
async def get_admin_html():
    log_id = nanoid.generate()
    context = ChatContext(command_manager, service_manager)
    context.log_id = log_id
    #agent_ = await service_manager.get_agent_data(agent_name)

    context.agent = {} #agent_
    context.chat_log = ChatLog(log_id=log_id, agent='admin')
    context.save_context()
    
    plugins = list_enabled()
    html = await render_combined_template('admin', plugins, context.data)
 
    #with open("static/admin.html", "r") as file:
    #    admin_html = file.read()
    #    admin_html = admin_html.replace("{{CHAT_ID}}", log_id)
    return html

@router.get("/{agent_name}", response_class=HTMLResponse)
async def get_chat_html(agent_name: str):
    log_id = nanoid.generate()
    context = ChatContext(command_manager, service_manager)
    context.log_id = log_id
    agent_ = await service_manager.get_agent_data(agent_name)
    print(colored(agent_, 'red'))

    if agent_ is None or agent_ == {}:
        return JSONResponse({"error": f"agent {agent_name} not found."}, status_code=404)

    context.agent = agent_
    context.chat_log = ChatLog(log_id=log_id, agent=agent_name)
    context.save_context()

    plugins = list_enabled()
    html = await render_combined_template('chat', plugins, context.data)
 
    return html


