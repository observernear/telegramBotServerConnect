import re
from typing import Optional

def truncate_text(text: str, max_length: int = 4000) -> str:
    """Truncate text to maximum length for Telegram"""
    if len(text) > max_length:
        return text[:max_length-100] + "\n\n... (output truncated) ...\n\n" + text[-100:]
    return text

def escape_markdown(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def format_command_output(command: str, output: str, success: bool) -> str:
    """Format command output for Telegram"""
    status_icon = "✅" if success else "❌"
    
    formatted_output = escape_markdown(output)
    formatted_command = escape_markdown(command)
    
    return f"""{status_icon} *Command executed:*\n {formatted_command} \n\n*Output:*\n{formatted_output}"""