from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.ssh_client import ssh_client
from keyboards.main_menu import get_main_menu, get_quick_commands_menu, get_cancel_button
from utils.helpers import format_command_output, truncate_text
import logging

logger = logging.getLogger(__name__)

router = Router()

class CommandState(StatesGroup):
    waiting_for_command = State()

# Quick commands handler
@router.callback_query(F.data.startswith("quick_cmd:"))
async def handle_quick_command(callback: types.CallbackQuery):
    """Handle quick command from inline keyboard"""
    command = callback.data.split(":", 1)[1]
    
    await callback.message.edit_reply_markup(reply_markup=None)
    processing_msg = await callback.message.answer(f"🔄 Executing: `{command}`", parse_mode="Markdown")
    
    # Используем старый метод для быстрых команд
    success, output = await ssh_client.execute_command(command)
    formatted_output = format_command_output(command, output, success)
    
    await processing_msg.delete()
    await callback.message.answer(
        truncate_text(formatted_output),
        parse_mode="MarkdownV2"
    )

# Menu command handlers
@router.message(F.text == "📊 System Info")
async def system_info(message: types.Message):
    """Get system information"""
    processing_msg = await message.answer("🔄 Getting system information...")
    
    commands = [
        ("uname -a", "System Info"),
        ("cat /etc/os-release", "OS Release"),
        ("uptime", "Uptime"),
        ("cat /proc/cpuinfo | grep 'model name' | uniq", "CPU Info"),
    ]
    
    full_output = ""
    for cmd, description in commands:
        # Используем старый метод для системных команд
        success, output = await ssh_client.execute_command(cmd)
        full_output += f"*{description}:*\n```{output}```\n\n"
    
    await processing_msg.delete()
    await message.answer(
        truncate_text(full_output),
        parse_mode="MarkdownV2"
    )

@router.message(F.text == "💾 Disk Usage")
async def disk_usage(message: types.Message):
    """Get disk usage information"""
    processing_msg = await message.answer("🔄 Checking disk usage...")
    
    # Используем старый метод
    success, output = await ssh_client.execute_command("df -h")
    
    if success:
        response = f"💾 *Disk Usage:*\n```{output}```"
    else:
        response = f"❌ *Error:*\n{output}"
    
    await processing_msg.delete()
    await message.answer(response, parse_mode="MarkdownV2")

@router.message(F.text == "🔄 Service Status")
async def service_status(message: types.Message):
    """Get service status"""
    processing_msg = await message.answer("🔄 Checking service status...")
    
    commands = [
        ("systemctl list-units --type=service --state=running | head -10", "Running Services"),
        ("systemctl list-units --type=service --state=failed", "Failed Services"),
    ]
    
    full_output = ""
    for cmd, description in commands:
        # Используем старый метод
        success, output = await ssh_client.execute_command(cmd)
        full_output += f"*{description}:*\n```{output}```\n\n"
    
    await processing_msg.delete()
    await message.answer(
        truncate_text(full_output),
        parse_mode="MarkdownV2"
    )

@router.message(F.text == "📈 Process List")
async def process_list(message: types.Message):
    """Get process list"""
    processing_msg = await message.answer("🔄 Getting process list...")
    
    # Используем старый метод
    success, output = await ssh_client.execute_command("ps aux --sort=-%cpu | head -15")
    
    if success:
        response = f"📈 *Top Processes by CPU:*\n```{output}```"
    else:
        response = f"❌ *Error:*\n{output}"
    
    await processing_msg.delete()
    await message.answer(response, parse_mode="MarkdownV2")

@router.message(F.text == "⚡ Quick Commands")
async def quick_commands(message: types.Message):
    """Show quick commands menu"""
    await message.answer(
        "⚡ *Quick Commands*\n\nSelect a command to execute:",
        reply_markup=get_quick_commands_menu(),
        parse_mode="Markdown"
    )

@router.message(F.text == "🔧 Custom Command")
async def custom_command_start(message: types.Message, state: FSMContext):
    """Start custom command input"""
    await message.answer(
        "🔧 *Custom Command*\n\nPlease enter the command you want to execute:",
        reply_markup=get_cancel_button(),
        parse_mode="Markdown"
    )
    await state.set_state(CommandState.waiting_for_command)

@router.message(CommandState.waiting_for_command, F.text == "❌ Cancel")
async def cancel_command(message: types.Message, state: FSMContext):
    """Cancel command input"""
    await state.clear()
    await message.answer(
        "❌ Command cancelled.",
        reply_markup=get_main_menu()
    )

@router.message(CommandState.waiting_for_command)
async def execute_custom_command(message: types.Message, state: FSMContext):
    """Execute custom command"""
    command = message.text.strip()
    
    if not command:
        await message.answer("❌ Please enter a valid command.")
        return
    
    # Security check - prevent dangerous commands
    dangerous_commands = ['rm -rf /', 'mkfs', 'dd if=', ':(){ :|:& };:', '> /dev/sda']
    if any(dangerous in command for dangerous in dangerous_commands):
        await message.answer("🚫 This command is blocked for security reasons.")
        return
    
    processing_msg = await message.answer(f"🔄 Executing: `{command}`", parse_mode="Markdown")
    
    # Используем старый метод для единичных команд
    success, output = await ssh_client.execute_command(command)
    formatted_output = format_command_output(command, output, success)
    
    await processing_msg.delete()
    await message.answer(
        truncate_text(formatted_output),
        parse_mode="MarkdownV2",
        reply_markup=get_main_menu()
    )
    
    # Предложить терминальный режим для множественных команд
    if success:
        await message.answer(
            "💡 *Tip:* Use '💻 Terminal Mode' from main menu to execute multiple commands in sequence!",
            parse_mode="Markdown"
        )
    
    await state.clear()

# Handle unknown messages
@router.message()
async def handle_unknown(message: types.Message):
    """Handle unknown messages"""
    await message.answer(
        "🤔 I don't understand that command. Use the menu below or /help for available options.",
        reply_markup=get_main_menu()
    )