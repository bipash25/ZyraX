"""
Greetings Handler Middleware
Sends welcome messages when users join and goodbye messages when users leave
Priority: -7 (after captcha, before locks)
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.message_parser import parse_filling_variables, parse_buttons
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new member joins"""
    if not update.message or not update.message.new_chat_members:
        return
    
    chat_id = str(update.effective_chat.id)
    chat = update.effective_chat
    
    try:
        # Get database
        db = context.application.bot_data.get('database')
        if not db:
            return
        
        # Get chat settings
        chat_settings = await db.chats.find_one({"_id": chat_id})
        
        # Check if welcome is enabled
        if not chat_settings or not chat_settings.get("welcome_enabled", False):
            return
        
        # Get welcome message
        welcome_text = chat_settings.get("welcome_text", "Hey {mention}! Welcome to {chatname}.")
        welcome_file_id = chat_settings.get("welcome_file_id")
        welcome_file_type = chat_settings.get("welcome_file_type")
        clean_welcome = chat_settings.get("clean_welcome", False)
        
        # Send welcome for each new member
        for new_member in update.message.new_chat_members:
            # Skip bots
            if new_member.is_bot:
                continue
            
            # Check if user is in captcha pending (skip welcome if captcha enabled)
            captcha_settings = chat_settings.get("captcha_enabled", False)
            if captcha_settings:
                pending = await db.captcha_pending.find_one({
                    "chat_id": chat_id,
                    "user_id": str(new_member.id)
                })
                if pending:
                    # Skip welcome, captcha will handle it
                    continue
            
            # Prepare message data
            user_data = {
                "first": new_member.first_name or "",
                "last": new_member.last_name or "",
                "username": new_member.username or "",
                "id": str(new_member.id),
                "mention": new_member.mention_html()
            }
            
            chat_data = {
                "chatname": chat.title or "this chat"
            }
            
            # Get member count
            try:
                member_count = await context.bot.get_chat_member_count(chat_id)
                chat_data["count"] = str(member_count)
            except:
                chat_data["count"] = "N/A"
            
            # Fill variables - merge user_data and chat_data into single context dict
            context_vars = {**user_data, **chat_data}
            filled_text = parse_filling_variables(welcome_text, context_vars)
            
            # Parse buttons
            text_without_buttons, buttons = parse_buttons(filled_text)
            
            # Create keyboard
            keyboard = None
            if buttons:
                keyboard = InlineKeyboardMarkup(buttons)
            
            # Send message
            sent_message = None
            
            try:
                if welcome_file_id and welcome_file_type:
                    # Send with media
                    send_method = {
                        "photo": context.bot.send_photo,
                        "video": context.bot.send_video,
                        "audio": context.bot.send_audio,
                        "document": context.bot.send_document,
                        "voice": context.bot.send_voice,
                        "video_note": context.bot.send_video_note,
                        "sticker": context.bot.send_sticker,
                        "animation": context.bot.send_animation
                    }.get(welcome_file_type)
                    
                    if send_method:
                        if welcome_file_type in ["voice", "video_note", "sticker"]:
                            # These don't support captions
                            sent_message = await send_method(
                                chat_id=chat_id,
                                **{welcome_file_type: welcome_file_id}
                            )
                            if text_without_buttons:
                                sent_message = await context.bot.send_message(
                                    chat_id=chat_id,
                                    text=text_without_buttons,
                                    parse_mode="HTML",
                                    reply_markup=keyboard
                                )
                        else:
                            sent_message = await send_method(
                                chat_id=chat_id,
                                **{welcome_file_type: welcome_file_id},
                                caption=text_without_buttons,
                                parse_mode="HTML",
                                reply_markup=keyboard
                            )
                else:
                    # Send text only
                    sent_message = await context.bot.send_message(
                        chat_id=chat_id,
                        text=text_without_buttons or "Welcome!",
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                
                # Schedule deletion if clean_welcome is enabled
                if clean_welcome and sent_message:
                    context.job_queue.run_once(
                        delete_welcome_message,
                        when=300,  # 5 minutes
                        data={
                            "chat_id": chat_id,
                            "message_id": sent_message.message_id
                        },
                        name=f"clean_welcome_{chat_id}_{sent_message.message_id}"
                    )
                
            except Exception as e:
                logger.error(f"Error sending welcome message: {e}")
        
    except Exception as e:
        logger.error(f"Error in welcome handler: {e}")

async def handle_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle member leaves"""
    if not update.message or not update.message.left_chat_member:
        return
    
    chat_id = str(update.effective_chat.id)
    chat = update.effective_chat
    left_member = update.message.left_chat_member
    
    # Skip bots
    if left_member.is_bot:
        return
    
    try:
        # Get database
        db = context.application.bot_data.get('database')
        if not db:
            return
        
        # Get chat settings
        chat_settings = await db.chats.find_one({"_id": chat_id})
        
        # Check if goodbye is enabled
        if not chat_settings or not chat_settings.get("goodbye_enabled", False):
            return
        
        # Get goodbye message
        goodbye_text = chat_settings.get("goodbye_text", "Goodbye {first}!")
        goodbye_file_id = chat_settings.get("goodbye_file_id")
        goodbye_file_type = chat_settings.get("goodbye_file_type")
        
        # Prepare message data
        user_data = {
            "first": left_member.first_name or "",
            "last": left_member.last_name or "",
            "username": left_member.username or "",
            "id": str(left_member.id),
            "mention": left_member.mention_html()
        }
        
        chat_data = {
            "chatname": chat.title or "this chat"
        }
        
        # Get member count
        try:
            member_count = await context.bot.get_chat_member_count(chat_id)
            chat_data["count"] = str(member_count)
        except:
            chat_data["count"] = "N/A"
        
        # Fill variables - merge user_data and chat_data into single context dict
        context_vars = {**user_data, **chat_data}
        filled_text = parse_filling_variables(goodbye_text, context_vars)
        
        # Parse buttons
        text_without_buttons, buttons = parse_buttons(filled_text)
        
        # Create keyboard
        keyboard = None
        if buttons:
            keyboard = InlineKeyboardMarkup(buttons)
        
        # Send message
        try:
            if goodbye_file_id and goodbye_file_type:
                # Send with media
                send_method = {
                    "photo": context.bot.send_photo,
                    "video": context.bot.send_video,
                    "audio": context.bot.send_audio,
                    "document": context.bot.send_document,
                    "voice": context.bot.send_voice,
                    "video_note": context.bot.send_video_note,
                    "sticker": context.bot.send_sticker,
                    "animation": context.bot.send_animation
                }.get(goodbye_file_type)
                
                if send_method:
                    if goodbye_file_type in ["voice", "video_note", "sticker"]:
                        # These don't support captions
                        await send_method(
                            chat_id=chat_id,
                            **{goodbye_file_type: goodbye_file_id}
                        )
                        if text_without_buttons:
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=text_without_buttons,
                                parse_mode="HTML",
                                reply_markup=keyboard
                            )
                    else:
                        await send_method(
                            chat_id=chat_id,
                            **{goodbye_file_type: goodbye_file_id},
                            caption=text_without_buttons,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
            else:
                # Send text only
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text_without_buttons or "Goodbye!",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            
        except Exception as e:
            logger.error(f"Error sending goodbye message: {e}")
        
    except Exception as e:
        logger.error(f"Error in goodbye handler: {e}")

async def delete_welcome_message(context: ContextTypes.DEFAULT_TYPE):
    """Delete welcome message after timeout"""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]
    
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.debug(f"Could not delete welcome message: {e}")

def register_handlers(application):
    """Register greetings handlers"""
    from telegram.ext import MessageHandler, filters
    
    # New member handler
    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            handle_new_member
        ),
        group=-7  # After captcha (-8), before locks (0)
    )
    
    # Left member handler
    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.LEFT_CHAT_MEMBER,
            handle_left_member
        ),
        group=-7
    )
    
    logger.info("✅ Greetings middleware registered (priority: -7)")