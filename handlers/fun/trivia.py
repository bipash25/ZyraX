"""
Trivia command - Answer trivia questions for coins
"""
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "trivia",
    "aliases": ["quiz"],
    "description": "Answer trivia questions to earn coins",
    "usage": "/trivia - Random question (earn 50-200 coins)",
    "category": "fun"
}

TRIVIA_QUESTIONS = [
    {
        "question": "What is the capital of France?",
        "options": ["London", "Paris", "Berlin", "Madrid"],
        "correct": 1,
        "reward": 50
    },
    {
        "question": "What is 2 + 2?",
        "options": ["3", "4", "5", "22"],
        "correct": 1,
        "reward": 50
    },
    {
        "question": "What is the largest planet in our solar system?",
        "options": ["Earth", "Mars", "Jupiter", "Saturn"],
        "correct": 2,
        "reward": 100
    },
    {
        "question": "How many continents are there?",
        "options": ["5", "6", "7", "8"],
        "correct": 2,
        "reward": 75
    },
    {
        "question": "What is the chemical symbol for gold?",
        "options": ["Go", "Au", "Gd", "Ag"],
        "correct": 1,
        "reward": 150
    },
    {
        "question": "What year did World War 2 end?",
        "options": ["1943", "1944", "1945", "1946"],
        "correct": 2,
        "reward": 125
    },
    {
        "question": "What is the speed of light?",
        "options": ["300,000 km/s", "150,000 km/s", "500,000 km/s", "1,000,000 km/s"],
        "correct": 0,
        "reward": 200
    },
    {
        "question": "Who painted the Mona Lisa?",
        "options": ["Van Gogh", "Picasso", "Da Vinci", "Monet"],
        "correct": 2,
        "reward": 100
    },
    {
        "question": "What is the smallest country in the world?",
        "options": ["Monaco", "Vatican City", "San Marino", "Liechtenstein"],
        "correct": 1,
        "reward": 150
    },
    {
        "question": "How many bones are in the human body?",
        "options": ["186", "206", "226", "246"],
        "correct": 1,
        "reward": 125
    },
]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start trivia question"""
    message = update.message
    
    # Pick random question
    question_data = random.choice(TRIVIA_QUESTIONS)
    
    # Build keyboard
    keyboard = []
    for i, option in enumerate(question_data['options']):
        keyboard.append([
            InlineKeyboardButton(
                option,
                callback_data=f"trivia_{i}_{question_data['correct']}_{question_data['reward']}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_html(
        f"🧠 <b>Trivia Time!</b>\n\n"
        f"<b>{question_data['question']}</b>\n\n"
        f"💰 <b>Reward:</b> {question_data['reward']} 🪙",
        reply_markup=reply_markup
    )


async def handle_trivia_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle trivia answer button click"""
    query = update.callback_query
    user = query.from_user
    
    if not query.data.startswith("trivia_"):
        return
    
    await query.answer()
    
    # Parse callback data
    parts = query.data.split("_")
    user_answer = int(parts[1])
    correct_answer = int(parts[2])
    reward = int(parts[3])
    
    db = context.application.bot_data.get('database')
    
    if user_answer == correct_answer:
        # Correct!
        if db:
            try:
                # Award coins
                await db.users.update_one(
                    {"_id": str(user.id)},
                    {
                        "$inc": {"currency": reward},
                        "$set": {
                            "username": user.username,
                            "first_name": user.first_name
                        }
                    },
                    upsert=True
                )
                
                # Get new balance
                user_doc = await db.users.find_one({"_id": str(user.id)})
                balance = user_doc.get('currency', reward)
                
                await query.edit_message_text(
                    f"✅ <b>Correct!</b> 🎉\n\n"
                    f"💰 <b>You earned:</b> {reward} 🪙\n"
                    f"<b>New balance:</b> {balance:,} 🪙",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Error awarding trivia coins: {e}")
                await query.edit_message_text(
                    "✅ Correct! (But couldn't award coins)",
                    parse_mode='HTML'
                )
        else:
            await query.edit_message_text(
                "✅ Correct! 🎉",
                parse_mode='HTML'
            )
    else:
        # Wrong
        await query.edit_message_text(
            "❌ <b>Wrong answer!</b>\n\n"
            "Better luck next time!",
            parse_mode='HTML'
        )


def get_trivia_handler():
    """Get trivia callback handler"""
    return CallbackQueryHandler(handle_trivia_answer, pattern="^trivia_")

