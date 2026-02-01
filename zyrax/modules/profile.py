import io
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler

__mod_name__ = "Profile"
__help__ = """
**Profile Commands:**
/profile - View your profile card
/profile @user - View someone's profile
/setbio <text> - Set your bio
/settitle <title> - Set your display title (requires purchase)
/inventory - View your items

**Stats shown:**
- Level & XP
- Balance
- Karma
- Messages sent
- Custom bio
"""


def create_profile_card(
    username: str,
    user_id: int,
    level: int,
    xp: int,
    balance: int,
    karma: int,
    msg_count: int,
    bio: str = None,
    title: str = None,
    rank: int = None
) -> io.BytesIO:
    """Generate a profile card image"""
    
    # Card dimensions
    width = 600
    height = 350
    
    # Create base image with gradient background
    card = Image.new('RGB', (width, height), color=(30, 30, 45))
    draw = ImageDraw.Draw(card)
    
    # Draw gradient background
    for i in range(height):
        r = int(30 + (i / height) * 20)
        g = int(30 + (i / height) * 15)
        b = int(45 + (i / height) * 25)
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    
    # Draw decorative elements
    draw.rectangle([(0, 0), (width, 8)], fill=(100, 150, 255))
    draw.rectangle([(0, height - 8), (width, height)], fill=(100, 150, 255))
    
    # Try to load a custom font, fallback to default
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw avatar placeholder (circle)
    avatar_x, avatar_y = 50, 50
    avatar_size = 80
    draw.ellipse(
        [(avatar_x, avatar_y), (avatar_x + avatar_size, avatar_y + avatar_size)],
        fill=(100, 150, 255),
        outline=(255, 255, 255),
        width=3
    )
    
    # Draw initials in avatar
    initials = username[0].upper() if username else "?"
    bbox = draw.textbbox((0, 0), initials, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text(
        (avatar_x + (avatar_size - text_width) // 2, avatar_y + (avatar_size - text_height) // 2 - 5),
        initials,
        fill=(255, 255, 255),
        font=font_large
    )
    
    # Username and title
    name_x = avatar_x + avatar_size + 20
    draw.text((name_x, 50), username[:20], fill=(255, 255, 255), font=font_large)
    
    if title:
        draw.text((name_x, 82), title, fill=(255, 215, 0), font=font_small)
    
    # Rank badge
    if rank and rank <= 10:
        rank_text = f"#{rank}"
        draw.rectangle([(width - 80, 20), (width - 20, 50)], fill=(255, 215, 0))
        draw.text((width - 70, 25), rank_text, fill=(30, 30, 45), font=font_medium)
    
    # Stats section
    stats_y = 150
    col1_x = 40
    col2_x = 220
    col3_x = 400
    
    # Level & XP
    draw.text((col1_x, stats_y), "LEVEL", fill=(150, 150, 150), font=font_small)
    draw.text((col1_x, stats_y + 20), str(level), fill=(255, 255, 255), font=font_large)
    
    # XP bar
    xp_needed = level * 100
    xp_progress = min(xp % xp_needed / xp_needed, 1.0) if xp_needed > 0 else 0
    bar_width = 120
    bar_height = 10
    draw.rectangle(
        [(col1_x, stats_y + 55), (col1_x + bar_width, stats_y + 55 + bar_height)],
        fill=(60, 60, 80)
    )
    draw.rectangle(
        [(col1_x, stats_y + 55), (col1_x + int(bar_width * xp_progress), stats_y + 55 + bar_height)],
        fill=(100, 150, 255)
    )
    draw.text((col1_x, stats_y + 70), f"{xp} XP", fill=(150, 150, 150), font=font_small)
    
    # Balance
    draw.text((col2_x, stats_y), "BALANCE", fill=(150, 150, 150), font=font_small)
    draw.text((col2_x, stats_y + 20), f"{balance:,}", fill=(255, 215, 0), font=font_large)
    
    # Karma
    karma_color = (100, 255, 100) if karma >= 0 else (255, 100, 100)
    draw.text((col3_x, stats_y), "KARMA", fill=(150, 150, 150), font=font_small)
    karma_display = f"+{karma}" if karma > 0 else str(karma)
    draw.text((col3_x, stats_y + 20), karma_display, fill=karma_color, font=font_large)
    
    # Messages
    draw.text((col2_x, stats_y + 70), "MESSAGES", fill=(150, 150, 150), font=font_small)
    draw.text((col2_x, stats_y + 90), f"{msg_count:,}", fill=(255, 255, 255), font=font_medium)
    
    # Bio section
    bio_y = 280
    draw.line([(40, bio_y - 15), (width - 40, bio_y - 15)], fill=(60, 60, 80), width=1)
    
    if bio:
        bio_text = bio[:80] + "..." if len(bio) > 80 else bio
        draw.text((40, bio_y), bio_text, fill=(200, 200, 200), font=font_small)
    else:
        draw.text((40, bio_y), "No bio set. Use /setbio to add one!", fill=(120, 120, 120), font=font_small)
    
    # User ID at bottom
    draw.text((40, height - 30), f"ID: {user_id}", fill=(100, 100, 100), font=font_small)
    
    # Convert to bytes
    output = io.BytesIO()
    card.save(output, format='PNG')
    output.seek(0)
    output.name = "profile.png"
    
    return output


@Client.on_message(filters.command("profile"))
@error_handler
async def profile_command(client: Client, message: Message):
    # Determine target user
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await client.get_users(message.command[1])
        except:
            return await message.reply_text("User not found.")
    else:
        target = message.from_user
    
    m = await message.reply_text("Generating profile card...")
    
    # Get user data from database
    user_data = await db.get_user_data(target.id)
    
    if not user_data:
        # Create default profile
        await db.register_user(target.id, target.username)
        user_data = await db.get_user_data(target.id) or {}
    
    # Get rank
    top_users = await db.get_top_users(limit=100, sort_by="xp")
    rank = None
    for i, u in enumerate(top_users, 1):
        if u.get("user_id") == target.id:
            rank = i
            break
    
    # Generate profile card
    card = create_profile_card(
        username=target.first_name or "User",
        user_id=target.id,
        level=user_data.get("level", 1),
        xp=user_data.get("xp", 0),
        balance=user_data.get("balance", 0),
        karma=user_data.get("karma", 0),
        msg_count=user_data.get("msg_count", 0),
        bio=user_data.get("bio"),
        title=user_data.get("title"),
        rank=rank
    )
    
    await m.delete()
    await message.reply_photo(photo=card, caption=f"Profile card for **{target.first_name}**")


@Client.on_message(filters.command("setbio"))
@error_handler
async def set_bio(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /setbio <your bio>")
    
    bio = message.text.split(None, 1)[1]
    
    if len(bio) > 150:
        return await message.reply_text("Bio must be 150 characters or less.")
    
    users = await db.get_collection("users")
    await users.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"bio": bio}},
        upsert=True
    )
    
    await message.reply_text("Bio updated!")


@Client.on_message(filters.command("inventory"))
@error_handler
async def inventory_command(client: Client, message: Message):
    user_data = await db.get_user_data(message.from_user.id)
    
    if not user_data or not user_data.get("inventory"):
        return await message.reply_text("Your inventory is empty!")
    
    inventory = user_data.get("inventory", [])
    
    # Item definitions
    ITEMS = {
        "vip_badge": {"name": "VIP Badge", "emoji": "", "desc": "Shows VIP status"},
        "custom_title": {"name": "Custom Title", "emoji": "", "desc": "Set a custom title"},
        "xp_boost": {"name": "XP Boost", "emoji": "", "desc": "2x XP for 24 hours"},
        "coin_boost": {"name": "Coin Boost", "emoji": "", "desc": "2x coins for 24 hours"},
        "profile_frame": {"name": "Profile Frame", "emoji": "", "desc": "Special profile border"},
    }
    
    text = f"**{message.from_user.first_name}'s Inventory**\n\n"
    
    for item_id in inventory:
        item = ITEMS.get(item_id, {"name": item_id, "emoji": "", "desc": "Unknown item"})
        text += f"{item['emoji']} **{item['name']}**\n"
        text += f"   {item['desc']}\n\n"
    
    await message.reply_text(text)


@Client.on_message(filters.command("settitle"))
@error_handler
async def set_title_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /settitle <title>")
    
    user_data = await db.get_user_data(message.from_user.id)
    inventory = user_data.get("inventory", []) if user_data else []
    
    if "custom_title" not in inventory:
        return await message.reply_text(
            "You need the **Custom Title** item to set a title!\n"
            "Purchase it from the shop with /shop"
        )
    
    title = message.text.split(None, 1)[1]
    
    if len(title) > 30:
        return await message.reply_text("Title must be 30 characters or less.")
    
    await db.set_title(message.from_user.id, title)
    await message.reply_text(f"Title set to: **{title}**")
