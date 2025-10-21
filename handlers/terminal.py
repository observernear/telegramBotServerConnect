from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.ssh_client import StatefulSSHClient as SSHClient
from keyboards.main_menu import get_main_menu, get_terminal_keyboard
from utils.helpers import truncate_text
import logging

logger = logging.getLogger(__name__)

router = Router()

# Use stateful client
ssh_client = SSHClient()

class TerminalState(StatesGroup):
    active = State()

@router.message(F.text == "💻 Terminal Mode")
async def start_terminal_mode(message: types.Message, state: FSMContext):
    """Start terminal mode"""
    user_id = message.from_user.id
    
    processing_msg = await message.answer("🔄 Starting terminal session with state preservation...")
    
    success = await ssh_client.create_session(user_id)
    
    if success:
        # Get current directory
        dir_success, current_dir = await ssh_client.get_current_directory(user_id)
        
        await processing_msg.delete()
        
        welcome_text = f"""
💻 *Terminal Mode Activated - State Preserved!*

✅ Directory state is now preserved between commands!
✅ `cd` commands work correctly
✅ Each command executes in the proper context

*Current directory:* `{current_dir if dir_success else '~'}`

*Try this sequence to test:*
1. `pwd` - See current directory
2. `cd /var/log` - Change directory  
3. `pwd` - Confirm it changed to /var/log
4. `ls` - See log files

The directory state is maintained throughout your session!
        """
        
        await message.answer(
            welcome_text,
            reply_markup=get_terminal_keyboard(),
            parse_mode="Markdown"
        )
        
        await state.set_state(TerminalState.active)
    else:
        await processing_msg.delete()
        await message.answer(
            "❌ Failed to start terminal session.",
            reply_markup=get_main_menu()
        )

@router.message(TerminalState.active, F.text == "🚪 Exit Terminal")
async def exit_terminal_mode(message: types.Message, state: FSMContext):
    """Exit terminal mode"""
    user_id = message.from_user.id
    await ssh_client.close_session(user_id)
    await state.clear()
    
    await message.answer(
        "🚪 Terminal session closed.",
        reply_markup=get_main_menu()
    )

@router.message(TerminalState.active, F.text == "🧹 Clear Screen")
async def clear_screen(message: types.Message):
    """Clear screen in terminal mode"""
    await message.answer("🧹 Screen cleared. Continue with your commands:")

@router.message(TerminalState.active, F.text == "📁 Current Directory")
async def show_current_directory(message: types.Message):
    """Show current directory in terminal mode"""
    user_id = message.from_user.id
    success, current_dir = await ssh_client.get_current_directory(user_id)
    
    if success:
        # Get directory listing
        ls_success, ls_output = await ssh_client.execute_in_session(user_id, "ls -la")
        if ls_success:
            response = f"📁 *Current Directory:* `{current_dir}`\n\n*Contents:*\n```{ls_output}```"
        else:
            response = f"📁 *Current Directory:* `{current_dir}`\n\n*Note:* Cannot list directory contents"
    else:
        response = f"❌ *Error:*\n```{current_dir}```"
    
    await message.answer(response, parse_mode="Markdown")

@router.message(TerminalState.active, F.text == "🏠 Home Directory")
async def go_home_directory(message: types.Message):
    """Go to home directory"""
    user_id = message.from_user.id
    success, output = await ssh_client.execute_in_session(user_id, "cd ~")
    
    if success:
        dir_success, new_dir = await ssh_client.get_current_directory(user_id)
        if dir_success:
            await message.answer(f"🏠 Changed to home directory:\n```{new_dir}```", parse_mode="Markdown")
        else:
            await message.answer("🏠 Changed to home directory", parse_mode="Markdown")
    else:
        await message.answer(f"❌ Failed to change directory:\n```{output}```", parse_mode="Markdown")

@router.message(TerminalState.active)
async def handle_terminal_command(message: types.Message, state: FSMContext):
    """Handle commands in terminal mode"""
    user_id = message.from_user.id
    command = message.text.strip()
    
    if not command:
        await message.answer("Please enter a command.")
        return
    
    # Handle special commands
    if command.lower() in ['exit', 'quit']:
        await exit_terminal_mode(message, state)
        return
    
    if command.lower() == 'clear':
        await message.answer("🧹 Screen cleared. Continue with your commands:")
        return
    
    # Security check
    dangerous_commands = ['rm -rf /', 'mkfs', 'dd if=', ':(){ :|:& };:', '> /dev/sda']
    if any(dangerous in command for dangerous in dangerous_commands):
        await message.answer("🚫 This command is blocked for security reasons.")
        return
    
    # Show typing action
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Execute command with state preservation
        success, output = await ssh_client.execute_in_session(user_id, command)
        
        # Format output
        if success:
            if output and output != "Command executed successfully":
                formatted_output = f"`$ {command}`\n```{output}```"
            else:
                formatted_output = f"`$ {command}`\n✅ Command executed successfully"
        else:
            formatted_output = f"`$ {command}`\n❌ Error:\n```{output}```"
        
        # Send the result
        await message.answer(
            truncate_text(formatted_output),
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        await message.answer(
            f"`$ {command}`\n❌ Unexpected error:\n```{str(e)}```",
            parse_mode="MarkdownV2"
        )