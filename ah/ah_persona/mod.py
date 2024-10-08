from ..commands import command
from ..services import service
import os

@service()
async def get_persona_data(persona_name, context=None):
    import os
    import json
    import sys

    print("persona name is", persona_name, file=sys.stderr)

    persona_path = os.path.join('personas', 'local', persona_name)
    if not os.path.exists(persona_path):
        persona_path = os.path.join('personas', 'shared', persona_name)
        if not os.path.exists(persona_path):
            return {}
    # read the persona data
    persona_file = os.path.join(persona_path, 'persona.json')
    if not os.path.exists(persona_file):
        return {}
    with open(persona_file, 'r') as f:
        persona_data = json.load(f)

    persona_data['avatar_image_path'] = os.path.join(persona_path, 'avatar.png')
    persona_data['face_ref_image_path'] = os.path.join(persona_path, 'faceref.png')

    # if faceref image does not exist, use the avatar image
    if not os.path.exists(persona_data['face_ref_image_path']):
        persona_data['face_ref_image_path'] = persona_data['avatar_image_path']
    
    persona_data['voice_samples'] = []
    for file in os.listdir(persona_path):
        if file.endswith(".wav"):
            persona_data['voice_samples'].append(os.path.join(persona_path, file))

    return persona_data


@command()
async def pic_of_me(prompt, context=None):
    """pic_of_me(prompt)

    Generate a picture of the persona given a detailed description of what they 
    they look like and what are doing. Use your knowledge of Stable Diffusion,
    including common keywords appropriate for the picture. You will (usually) want to include
    the full text from the Appearance section of the Persona.
    The description should be very detailed and specific, and should include
    the persona's appearance such as what they are wearing, their expression, what they are doing.
    Also include details about the background or scene where they are as well as the pose they are in. 
    Remember that the image generator does not know what Persona looks like at all, so you must provide
    all details in every prompt.
    Always use this instead of 'image' when creating an image of the persona!

    Example (use even more details if possible, and fill in brackets with real information)
    (do not actually include brackets):

    { "pic_of_me": "a photo from []camera position] of [details from Appearance section of Persona definition] [what they are doing, pose, etc.]." }

    """
    persona = context.agent['persona']
    print("persona:", persona)
    img = await context.text_to_image(prompt + ', score_9, score_8_up', 'split-view, diptych, side-by-side, 2girl, 2boy')
    print("img = ", img)
    img_dir = os.path.dirname(persona['face_ref_image_path'])
    swapped = await context.swap_face(img_dir, img)
    await context.insert_image("/" + swapped)


