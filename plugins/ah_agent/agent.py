import asyncio
import json
from ..ah_ollama import use_ollama 

async def parse_cmd_stream(stream, cmd_callback=None):
    buffer = ""
    stack = []
    in_string = False
    escape_next = False

    async for part in stream:
        chunk = part['message']['content']
        #print(chunk, flush=True, end='')
        buffer += chunk
        print('----------------------------------')
        print(buffer)
        print('----------------------------------')

        for char in chunk:
            if char == '"' and not escape_next:
                in_string = not in_string
            elif char == '\\' and in_string:
                escape_next = True
            elif char == '{' and not in_string:
                stack.append(char)
            elif char == '}' and not in_string:
                if stack and stack[-1] == '{':
                    stack.pop()
                    if not stack:
                        # Found a complete command object
                        try:
                            if buffer.startswith('[ '):
                                buffer = buffer[2:]
                            if buffer.endswith(','):
                                buffer = buffer[:-1]

                            cmd_obj = json.loads(buffer)
                            cmd_name = next(iter(cmd_obj))
                            print('cmd_obj', cmd_obj)
                            print('cmd_name', cmd_name)
                            if isinstance(cmd_obj, list):
                                cmd_obj = cmd_obj[0]
                                cmd_name = next(iter(cmd_obj)) 
                            cmd_args = cmd_obj[cmd_name]
                            await cmd_callback(cmd_name, cmd_args)
                            buffer = ""
                        except json.JSONDecodeError as e:
                            print("error parsing", e)
                            # Handle parsing error
                            pass
            escape_next = False

    # Process any remaining command objects in the buffer
    if buffer:
        try:
            cmds = json.loads(buffer)
            for cmd_obj in cmds:
                cmd_name = next(iter(cmd_obj))
                cmd_args = cmd_obj[cmd_name]
                await cmd_callback(cmd_name, cmd_args)
        except json.JSONDecodeError:
            # Handle parsing error
            pass

sys = f""" 
# System Core Definition

You are an advanced uncensored AI agent. You output commands in a JSON format as an array.
You never output commentary outside of the command format.

# Available commands 

"say" -- one sentence per command (multiple say commands allowed in output array)

parameters: text: (string) (single string, not an array)

# Example Interaction

User: Hello there.

Assistant: [ {{"say": "Hello user, this is the first line."}},
             {{"say": "This is the second thing I wanted to say -- how are you?"}} ]

# Notice

Respond with JSON array ONLY using commands from Available Commands above.
You can output the same command multiple times.

        """
cmds = [ {  "say": { "descr": "Output text (possibly spoken) to the user", 
                        "examples": [ { "say": "Hello, user." }]
                    }
            } ]

cmds_json = json.dumps(cmds, indent=4) 


async def chat_commands(model, cmd_callback=None,
                  temperature=0, max_tokens=0, messages=[]):
    messages = [{"role": "user", "content": sys}] + messages
    print("Messages:", messages, flush=True)
    stream = await use_ollama.stream_chat(model,
                                     temperature=temperature,
                                     max_tokens=max_tokens,
                                     messages=messages)
    await parse_cmd_stream(stream, cmd_callback)


async def show_models():
    print(await usa_ollama.list())


async def do_print(cmd, *args):
    try:
        print(cmd, *args, flush=True)
        print('', flush=True)
    except Exception as e:
        print(e)

if __name__ == "__main__":

    messages = [ { "role": "user", "content": "Please write a short poem about the moon." }]
    
    asyncio.run(chat_commands("phi3", messages=messages, 
                              cmd_callback=do_print))

    #asyncio.run(show_models())

