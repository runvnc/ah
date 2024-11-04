import json

test="""
[{"say": {"text": "Wow, that's actually a really fascinating project - especially from my perspective as an AI agent!"}}][{"say": {"text": "Building a framework like that is definitely ambitious - there are so many moving parts to consider."}}][{"say": {"text": "Given how you're feeling right now, would you like to talk through just one small piece you could work on? Maybe something simple like documenting a single feature or testing one small component?"}}][{"say": {"text": "Sometimes with big projects, doing even a tiny bit helps keep the momentum going."}}]
"""

def merge_json_arrays(data):
    data = data.strip()
    
    parts = data.split("][")
    
    arrays = []
    for part in parts:
        if part.startswith("["):
            part = part[1:]
        if part.endswith("]"):
            part = part[:-1]
        part = f"[{part}]"
        arrays.append(json.loads(part))
    
    return sum(arrays, [])

