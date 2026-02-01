from PIL import Image, ImageDraw, ImageFont, ImageChops
import io
import os
import random

# Store font in assets if possible, for now default
# We'll assume a fonts directory or just fallback
FONT_PATH = "arial.ttf" 

def circle_crop(img):
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + img.size, fill=255)
    
    output = Image.new("RGBA", img.size, (0, 0, 0, 0))
    output.paste(img, (0, 0), mask=mask)
    return output

def generate_welcome_image(user_name, user_id, chat_title, profile_photo=None):
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
        # Try to find a system font or use default if file not found
        # In a docker container, paths might differ.
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except IOError:
        try:
             # Try common linux path
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 60)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 30)
        except IOError:
            # Fallback
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

    draw.text((400, 250), f"WELCOME TO", fill="white", font=font_small, anchor="mm")
    draw.text((400, 300), f"{chat_title}", fill=accent, font=font_large, anchor="mm")
    
    # User info
    draw.text((400, 360), f"{user_name} (ID: {user_id})", fill="gray", font=font_small, anchor="mm")

    # Placeholder for Avatar (center top)
    # If we had the photo, we would paste it here. 
    draw.ellipse([325, 50, 475, 200], fill=accent)
    draw.text((400, 125), user_name[0].upper(), fill="white", font=font_large, anchor="mm")

    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio
