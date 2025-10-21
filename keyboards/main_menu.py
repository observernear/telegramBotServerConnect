from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def get_main_menu() -> ReplyKeyboardMarkup:
    """Get main menu keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="📊 System Info"))
    builder.add(KeyboardButton(text="💾 Disk Usage"))
    builder.add(KeyboardButton(text="🔄 Service Status"))
    builder.add(KeyboardButton(text="📈 Process List"))
    builder.add(KeyboardButton(text="⚡ Quick Commands"))
    builder.add(KeyboardButton(text="🔧 Custom Command"))
    builder.add(KeyboardButton(text="💻 Terminal Mode"))
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_quick_commands_menu() -> InlineKeyboardMarkup:
    """Get quick commands inline keyboard"""
    builder = InlineKeyboardBuilder()
    
    commands = [
        ("🔄 Update System", "sudo apt update && sudo apt upgrade -y"),
        ("🧹 Clean Cache", "sudo apt autoremove -y && sudo apt autoclean"),
        ("📊 Memory Info", "free -h"),
        ("🌐 Network Stats", "ss -tuln"),
        ("📦 Installed Packages", "dpkg --get-selections | wc -l"),
        ("👥 Logged Users", "who"),
    ]
    
    for text, command in commands:
        builder.add(InlineKeyboardButton(text=text, callback_data=f"quick_cmd:{command}"))
    
    builder.adjust(2)
    return builder.as_markup()

def get_cancel_button() -> ReplyKeyboardMarkup:
    """Get cancel button keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Cancel")]],
        resize_keyboard=True
    )

def get_terminal_keyboard() -> ReplyKeyboardMarkup:
    """Get terminal mode keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="📁 Current Directory"))
    builder.add(KeyboardButton(text="🏠 Home Directory"))
    builder.add(KeyboardButton(text="🧹 Clear Screen"))
    builder.add(KeyboardButton(text="🚪 Exit Terminal"))
    
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)