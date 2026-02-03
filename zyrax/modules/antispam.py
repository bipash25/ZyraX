"""
ZyraX Anti-Spam Module

Spam detection and prevention with configurable settings.
"""

import re
import time
from typing import Dict, Any, List, Optional

from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatMemberStatus

from zyrax.utils.decorators import require_admin, is_user_admin
from zyrax.utils.errors import error_handler
from zyrax.utils.users import extract_user
from zyrax.utils.time_parser import parse_duration
from zyrax.database.mongo import db
from zyrax.constants import Limits, AntiSpam, Timeouts


__mod_name__ = "AntiSpam"
__help__ = """
**Anti-Spam Commands:**
/antispam - Show current antispam settings
/antispam caps <on/off> - Toggle caps lock detection (70%+ caps)
/antispam links <on/off> - Toggle external link blocking
/antispam forwards <on/off> - Block forwarded messages from channels
/antispam media <limit> - Set media spam limit (0=off)
/antispam sticker <limit> - Set sticker spam limit (0=off)
/antispam mentions <limit> - Set mention spam limit (0=off)

**Silent Warnings:**
/swarn <user> <reason> - Warn user via DM only (silent)

**Anti-Raid:**
/raid on [duration] - Enable anti-raid mode (default: 1h)
/raid off - Disable anti-raid mode
/raidstatus - Check anti-raid status

**Link Whitelist:**
/whitelist add <domain> - Add domain to link whitelist
/whitelist remove <domain> - Remove domain from whitelist
/whitelist list - Show whitelisted domains
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def check_admin_status(message: Message) -> bool:
    """Check if message sender is an admin (cached)."""
    try:
        return await is_user_admin(
            message._client,
            message.chat.id,
            message.from_user.id
        )
    except Exception:
        return False


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    return url.replace("https://", "").replace("http://", "").split("/")[0]


def is_suspicious_url(url: str) -> bool:
    """Check if URL matches suspicious patterns."""
    for pattern in AntiSpam.SUSPICIOUS_PATTERNS:
        if re.search(pattern, url):
            return True
    
    domain = extract_domain(url).lower()
    for keyword in AntiSpam.PHISHING_KEYWORDS:
        if keyword in domain:
            return True
    
    return False


def format_raid_duration(seconds: int) -> str:
    """Format duration for display."""
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


# =============================================================================
# SETTINGS COMMANDS
# =============================================================================

@Client.on_message(filters.command("antispam") & filters.group)
@error_handler
@require_admin()
async def antispam_settings(client: Client, message: Message):
    """View or modify anti-spam settings."""
    args = message.command[1:] if len(message.command) > 1 else []
    chat_id = message.chat.id
    
    if not args:
        # Show current settings
        settings = await db.get_chat_settings(chat_id)
        antispam = settings.get("antispam", {})
        
        text = "**Anti-Spam Settings:**\n\n"
        text += f"Caps Detection: {'On' if antispam.get('caps', False) else 'Off'}\n"
        text += f"Link Blocking: {'On' if antispam.get('links', False) else 'Off'}\n"
        text += f"Forward Blocking: {'On' if antispam.get('forwards', False) else 'Off'}\n"
        text += f"Media Spam Limit: {antispam.get('media_limit', 0)} (0=off)\n"
        text += f"Sticker Spam Limit: {antispam.get('sticker_limit', 0)} (0=off)\n"
        text += f"Mention Spam Limit: {antispam.get('mention_limit', 0)} (0=off)\n"
        
        return await message.reply_text(text)
    
    setting = args[0].lower()
    value = args[1].lower() if len(args) > 1 else None
    
    if setting == "caps":
        enabled = value == "on" if value else True
        await db.set_antispam_setting(chat_id, "caps", enabled)
        await message.reply_text(f"Caps detection: {'Enabled' if enabled else 'Disabled'}")
        
    elif setting == "links":
        enabled = value == "on" if value else True
        await db.set_antispam_setting(chat_id, "links", enabled)
        await message.reply_text(f"Link blocking: {'Enabled' if enabled else 'Disabled'}")
        
    elif setting == "forwards":
        enabled = value == "on" if value else True
        await db.set_antispam_setting(chat_id, "forwards", enabled)
        await message.reply_text(f"Forward blocking: {'Enabled' if enabled else 'Disabled'}")
        
    elif setting in ["media", "sticker", "mentions"]:
        try:
            limit = int(value) if value else Limits.MAX_MENTIONS_DEFAULT
        except ValueError:
            return await message.reply_text("Please provide a valid number.")
        
        await db.set_antispam_setting(chat_id, f"{setting}_limit", limit)
        await message.reply_text(f"{setting.title()} spam limit set to: {limit}")
        
    else:
        await message.reply_text("Unknown setting. Use /antispam to see options.")


@Client.on_message(filters.command("swarn") & filters.group)
@error_handler
@require_admin()
async def silent_warn(client: Client, message: Message):
    """Silent warning - warns user via DM only."""
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text("Reply to a user or mention them to warn.")
    
    reason = "No reason"
    if message.reply_to_message:
        if len(message.command) > 1:
            reason = " ".join(message.command[1:])
    elif len(message.command) > 2:
        reason = " ".join(message.command[2:])
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)
    
    count = await db.add_warn(message.chat.id, user_id, f"[Silent] {reason}")
    
    # Try to send DM
    try:
        await client.send_message(
            user_id,
            f"You have been warned in **{message.chat.title}**.\n"
            f"Reason: {reason}\n"
            f"Warning count: {count}/{Limits.MAX_WARNS}"
        )
        await message.reply_text("User has been warned via DM.", quote=False)
    except Exception:
        await message.reply_text("Could not DM user. Warning recorded anyway.")
    
    await db.log_admin_action("silent_warn", message.from_user.id, message.chat.id, user_id, reason)
    
    # Check for max warns
    if count >= Limits.MAX_WARNS:
        try:
            await client.ban_chat_member(message.chat.id, user_id)
            await message.reply_text(f"{user_mention} has been banned ({Limits.MAX_WARNS}/{Limits.MAX_WARNS} warns).")
            await db.reset_warns(message.chat.id, user_id)
        except Exception:
            pass


# =============================================================================
# RAID MODE
# =============================================================================

@Client.on_message(filters.command("raid") & filters.group)
@error_handler
@require_admin()
async def raid_mode(client: Client, message: Message):
    """Toggle anti-raid mode."""
    args = message.command[1:] if len(message.command) > 1 else []
    chat_id = message.chat.id
    
    if not args:
        return await message.reply_text("Usage: /raid on [duration] or /raid off")
    
    action = args[0].lower()
    
    if action == "on":
        # Parse duration (default 1 hour)
        duration = Timeouts.RAID_DEFAULT_DURATION
        if len(args) > 1:
            try:
                parsed = parse_duration(args[1])
                if parsed:
                    duration = parsed
            except Exception:
                pass
        
        expire_time = time.time() + duration
        await db.set_raid_mode(chat_id, True, expire_time)
        
        await message.reply_text(
            f"**Anti-Raid Mode Activated!**\n\n"
            f"Duration: {format_raid_duration(duration)}\n"
            f"New members will be automatically muted until verified.\n"
            f"Use /raid off to disable."
        )
        
    elif action == "off":
        await db.set_raid_mode(chat_id, False, 0)
        await message.reply_text("Anti-raid mode disabled.")


@Client.on_message(filters.command("raidstatus") & filters.group)
@error_handler
async def raid_status(client: Client, message: Message):
    """Check anti-raid status."""
    status = await db.get_raid_mode(message.chat.id)
    
    if status.get("enabled") and status.get("expires", 0) > time.time():
        remaining = int(status["expires"] - time.time())
        mins = remaining // 60
        secs = remaining % 60
        await message.reply_text(f"Anti-raid is **ACTIVE**. Expires in {mins}m {secs}s.")
    else:
        await message.reply_text("Anti-raid is **OFF**.")


# =============================================================================
# WHITELIST
# =============================================================================

@Client.on_message(filters.command("whitelist") & filters.group)
@error_handler
@require_admin()
async def whitelist_handler(client: Client, message: Message):
    """Manage link whitelist."""
    args = message.command[1:] if len(message.command) > 1 else []
    chat_id = message.chat.id
    
    if not args:
        return await message.reply_text("Usage: /whitelist <add/remove/list> [domain]")
    
    action = args[0].lower()
    
    if action == "add":
        if len(args) < 2:
            return await message.reply_text("Usage: /whitelist add <domain>")
        domain = extract_domain(args[1].lower())
        await db.add_whitelist_domain(chat_id, domain)
        await message.reply_text(f"Added `{domain}` to whitelist.")
        
    elif action == "remove":
        if len(args) < 2:
            return await message.reply_text("Usage: /whitelist remove <domain>")
        domain = args[1].lower()
        await db.remove_whitelist_domain(chat_id, domain)
        await message.reply_text(f"Removed `{domain}` from whitelist.")
        
    elif action == "list":
        domains = await db.get_whitelist_domains(chat_id)
        if not domains:
            return await message.reply_text("No whitelisted domains.")
        text = "**Whitelisted Domains:**\n" + "\n".join(f"- {d}" for d in domains)
        await message.reply_text(text)


# =============================================================================
# MESSAGE HANDLERS
# =============================================================================

@Client.on_message(filters.text & filters.group, group=6)
async def antispam_check(client: Client, message: Message):
    """Check messages for spam patterns."""
    if not message.text or message.text.startswith("/"):
        return
    
    # Skip admins (cached check)
    if await check_admin_status(message):
        return
    
    chat_id = message.chat.id
    settings = await db.get_chat_settings(chat_id)
    antispam = settings.get("antispam", {})
    
    text = message.text
    
    # === CAPS DETECTION ===
    if antispam.get("caps", False):
        alpha_chars = [c for c in text if c.isalpha()]
        if len(alpha_chars) >= Limits.MIN_CAPS_CHARS:
            caps_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
            if caps_ratio >= Limits.CAPS_THRESHOLD:
                try:
                    await message.delete()
                    await client.send_message(
                        chat_id,
                        f"{message.from_user.mention}, please don't use excessive caps!"
                    )
                    return
                except Exception:
                    pass
    
    # === LINK DETECTION ===
    if antispam.get("links", False):
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text.lower())
        
        if urls:
            whitelist = await db.get_whitelist_domains(chat_id)
            
            for url in urls:
                domain = extract_domain(url)
                
                # Check whitelist
                if any(w in domain for w in whitelist):
                    continue
                
                # Check for suspicious URLs
                if is_suspicious_url(url) or not whitelist:
                    try:
                        await message.delete()
                        await client.send_message(
                            chat_id,
                            f"{message.from_user.mention}, external links are not allowed!"
                        )
                        return
                    except Exception:
                        pass
    
    # === MENTION SPAM ===
    mention_limit = antispam.get("mention_limit", 0)
    if mention_limit > 0 and message.entities:
        mentions = sum(1 for e in message.entities if e.type.name in ["MENTION", "TEXT_MENTION"])
        if mentions > mention_limit:
            try:
                await message.delete()
                await client.send_message(
                    chat_id,
                    f"{message.from_user.mention}, too many mentions! Max: {mention_limit}"
                )
                return
            except Exception:
                pass


@Client.on_message(filters.forwarded & filters.group, group=7)
async def check_forwards(client: Client, message: Message):
    """Block forwarded messages from channels."""
    if await check_admin_status(message):
        return
    
    settings = await db.get_chat_settings(message.chat.id)
    antispam = settings.get("antispam", {})
    
    if antispam.get("forwards", False) and message.forward_from_chat:
        try:
            await message.delete()
            await client.send_message(
                message.chat.id,
                f"{message.from_user.mention}, forwarding from channels is not allowed!"
            )
        except Exception:
            pass


@Client.on_message(
    (filters.sticker | filters.animation | filters.photo | filters.video) & filters.group,
    group=8
)
async def check_media_spam(client: Client, message: Message):
    """Check for media/sticker spam."""
    if await check_admin_status(message):
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    settings = await db.get_chat_settings(chat_id)
    antispam = settings.get("antispam", {})
    
    # Determine media type and limit
    if message.sticker:
        media_type = "sticker"
        limit = antispam.get("sticker_limit", 0)
    else:
        media_type = "media"
        limit = antispam.get("media_limit", 0)
    
    if limit <= 0:
        return
    
    # Track in Redis with sliding window
    cache_key = f"spam:{media_type}:{chat_id}:{user_id}"
    count = await db.cache.incr_with_ttl(cache_key, ttl=Limits.MEDIA_SPAM_WINDOW)
    
    if count > limit:
        try:
            await message.delete()
            if count == limit + 1:  # Only warn once
                await client.send_message(
                    chat_id,
                    f"{message.from_user.mention}, slow down with the {media_type}s! "
                    f"Max: {limit}/{Limits.MEDIA_SPAM_WINDOW}s"
                )
        except Exception:
            pass


@Client.on_message(filters.new_chat_members & filters.group, group=9)
async def raid_mode_handler(client: Client, message: Message):
    """Handle new members during raid mode."""
    chat_id = message.chat.id
    status = await db.get_raid_mode(chat_id)
    
    if not status.get("enabled") or status.get("expires", 0) <= time.time():
        return
    
    # Auto-mute new members during raid
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        
        try:
            await client.restrict_chat_member(
                chat_id,
                member.id,
                ChatPermissions(can_send_messages=False)
            )
            await client.send_message(
                chat_id,
                f"**Anti-Raid Active**\n{member.mention}, you've been temporarily muted. "
                f"Please wait for an admin to verify you."
            )
        except Exception:
            pass
