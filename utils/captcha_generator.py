"""
Captcha generation utilities
Generates math and text challenges for user verification
"""
import random
import string
from typing import Tuple


def generate_math_captcha() -> Tuple[str, str]:
    """
    Generate a simple math captcha
    
    Returns:
        Tuple of (question, answer)
    """
    operations = [
        lambda: (random.randint(1, 50), random.randint(1, 50), '+'),
        lambda: (random.randint(10, 100), random.randint(1, 10), '-'),
        lambda: (random.randint(1, 12), random.randint(1, 12), '×')
    ]
    
    op_func = random.choice(operations)
    num1, num2, operator = op_func()
    
    if operator == '+':
        answer = num1 + num2
    elif operator == '-':
        answer = num1 - num2
    else:  # ×
        answer = num1 * num2
    
    question = f"What is {num1} {operator} {num2}?"
    
    return question, str(answer)


def generate_text_captcha(length: int = 6) -> str:
    """
    Generate a random text captcha
    
    Args:
        length: Length of the captcha text
        
    Returns:
        Random alphanumeric string
    """
    # Exclude confusing characters: 0, O, I, l, 1
    characters = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choice(characters) for _ in range(length))


def generate_button_captcha() -> Tuple[str, list]:
    """
    Generate a button-based captcha challenge
    
    Returns:
        Tuple of (correct_answer, all_buttons)
    """
    # Generate options
    emojis = ['🍎', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍑', '🍒', '🥝']
    random.shuffle(emojis)
    
    correct = random.choice(emojis[:4])
    options = emojis[:4]
    random.shuffle(options)
    
    return correct, options


def generate_number_button_captcha() -> Tuple[int, list]:
    """
    Generate a number selection captcha
    
    Returns:
        Tuple of (correct_number, button_numbers)
    """
    # Generate 4 random numbers
    numbers = random.sample(range(1, 100), 4)
    correct = random.choice(numbers)
    
    return correct, sorted(numbers)