import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    SSH_HOST: str = os.getenv('SSH_HOST', 'localhost')
    SSH_PORT: int = int(os.getenv('SSH_PORT', 22))
    SSH_USERNAME: str = os.getenv('SSH_USERNAME', 'root')
    SSH_PASSWORD: str = os.getenv('SSH_PASSWORD', '')
    SSH_KEY_PATH: str = os.getenv('SSH_KEY_PATH', '')
    ADMIN_IDS: list = None
    
    def __post_init__(self):
        if self.ADMIN_IDS is None:
            admin_ids = os.getenv('ADMIN_IDS', '')
            self.ADMIN_IDS = [int(id.strip()) for id in admin_ids.split(',') if id.strip()]
    
    def validate(self):
        """Validate configuration"""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        if not self.SSH_HOST:
            raise ValueError("SSH_HOST is required")
        if not self.SSH_USERNAME:
            raise ValueError("SSH_USERNAME is required")
        if not self.SSH_PASSWORD and not self.SSH_KEY_PATH:
            raise ValueError("Either SSH_PASSWORD or SSH_KEY_PATH is required")

config = Config()