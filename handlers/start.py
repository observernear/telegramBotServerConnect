from aiogram import Router, types
from aiogram.filters import Command
from keyboards.main_menu import get_main_menu
from config.config import config

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    welcome_text = """
        🤖 *SSH Bot for Ubuntu Server*

        Welcome to your personal server management bot! I can help you execute commands on your Ubuntu server securely.

        *Available Features:*
        • System monitoring
        • Disk usage analysis  
        • Service management
        • Process monitoring
        • Quick commands
        • Custom command execution

        *Security:*
        • Only authorized users can access
        • All commands are logged
        • Safe command execution

        Use the menu below or type /help for more information.
    """
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command"""
    help_text = """
        📖 *Available Commands*

        *Main Menu Options:*
        📊 System Info - Basic system information
        💾 Disk Usage - Disk space analysis  
        🔄 Service Status - Check system services
        📈 Process List - Running processes
        ⚡ Quick Commands - Common operations
        🔧 Custom Command - Execute custom command

        *Manual Commands:*
        /start - Start the bot
        /help - Show this help
        /status - Check bot and server status

        *Security Notes:*
        • Commands are executed with your SSH credentials
        • Be careful with destructive commands
        • All activity is logged
    """
    
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    """Handle /status command"""
    from services.ssh_client import ssh_client
    
    status_text = "🔍 *System Status*\n\n"
    
    # Check SSH connection
    if ssh_client.connection:
        status_text += "🔗 *SSH Connection:* ✅ Connected\n"
    else:
        status_text += "🔗 *SSH Connection:* ❌ Disconnected\n"
    
    status_text += f"👤 *Admin Access:* {'✅ Yes' if message.from_user.id in config.ADMIN_IDS else '❌ No'}\n"
    status_text += f"🖥️ *Target Server:* {config.SSH_HOST}\n"
    status_text += f"👤 *SSH User:* {config.SSH_USERNAME}"
    
    await message.answer(status_text, parse_mode="Markdown")