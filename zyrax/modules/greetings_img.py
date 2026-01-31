from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont, ImageChops
import io
import os
import random

__mod_name__ = "Welcome Images"
__help__ = """
Automatic visual welcomes. 
I will generate a custom image when a new user joins.
No commands needed.
"""

# Store font in assets if possible, for now default
FONT_PATH = "arial.ttf" # Fallback to default if not found

def circle_crop(img):
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + img.size, fill=255)
    result = ImageChops.screen(img, img) 
    # Actually simpler:
    output = Image.new("RGBA", img.size, (0, 0, 0, 0))
    output.paste(img, (0, 0), mask=mask)
    return output

def generate_welcome_image(user_name, user_id, profile_photo=None):
    # Base Image (Dark Gradient)
    width, height = 800, 400
    img = Image.new('RGB', (width, height), color=(20, 20, 30))
    draw = ImageDraw.Draw(img)
    
    # Random Accent Color
    accent = random.choice([(138, 43, 226), (0, 255, 127), (30, 144, 255), (255, 105, 180)])
    
    # Draw Background Pattern (Simple dots)
    for _ in range(50):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.ellipse([x, y, x+3, y+3], fill=(50, 50, 60))

    # Border
    draw.rectangle([0, 0, width-1, height-1], outline=accent, width=10)
    
    # Text
    try:
        font_large = ImageFont.truetype(FONT_PATH, 60)
        font_small = ImageFont.truetype(FONT_PATH, 30)
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((400, 250), f"WELCOME", fill="white", font=font_large, anchor="mm")
    draw.text((400, 320), f"{user_name}", fill=accent, font=font_large, anchor="mm")
    draw.text((400, 370), f"ID: {user_id}", fill="gray", font=font_small, anchor="mm")

    # Placeholder for Avatar (center top)
    # If we had the photo, we would paste it here. 
    # Since downloading avatars adds complexity (async/io), we use a placeholder circle.
    draw.ellipse([325, 50, 475, 200], fill=accent)
    draw.text((400, 125), user_name[0].upper(), fill="white", font=font_large, anchor="mm")

    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

@Client.on_message(filters.new_chat_members, group=2)
async def welcome_image_handler(client: Client, message: Message):
    for member in message.new_chat_members:
        if member.id == client.me.id:
            continue
            
        # Generate Image
        img_bio = generate_welcome_image(member.first_name, member.id)
        
        # Send
        await message.reply_photo(
            photo=img_bio,
            caption=f"Welcome {member.mention} to **{message.chat.title}**! 👋"
        )
