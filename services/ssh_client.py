import asyncssh
import asyncio
from typing import Optional, Tuple, Dict
from config.config import config
import logging
import os

logger = logging.getLogger(__name__)

class StatefulSSHClient:
    def __init__(self):
        self.sessions: Dict[int, dict] = {}  # user_id -> session data
        self.single_connection: Optional[asyncssh.SSHClientConnection] = None
    
    async def connect(self) -> bool:
        """Establish single SSH connection"""
        try:
            conn_args = {
                'host': config.SSH_HOST,
                'port': config.SSH_PORT,
                'username': config.SSH_USERNAME,
            }
            
            if config.SSH_PASSWORD:
                conn_args['password'] = config.SSH_PASSWORD
            elif config.SSH_KEY_PATH:
                conn_args['client_keys'] = [config.SSH_KEY_PATH]
            
            self.single_connection = await asyncssh.connect(**conn_args)
            logger.info(f"SSH connection established to {config.SSH_HOST}")
            return True
            
        except Exception as e:
            logger.error(f"SSH connection failed: {e}")
            return False
    
    async def execute_command(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute single command"""
        if not self.single_connection:
            success = await self.connect()
            if not success:
                return False, "❌ Failed to establish SSH connection"
        
        try:
            result = await asyncio.wait_for(
                self.single_connection.run(command, check=True),
                timeout=timeout
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nStderr: {result.stderr}"
                
            return True, output.strip()
            
        except Exception as e:
            return False, f"❌ Error: {e}"
    
    async def create_session(self, user_id: int) -> bool:
        """Create stateful session for user"""
        try:
            if user_id in self.sessions:
                await self.close_session(user_id)
            
            conn_args = {
                'host': config.SSH_HOST,
                'port': config.SSH_PORT,
                'username': config.SSH_USERNAME,
            }
            
            if config.SSH_PASSWORD:
                conn_args['password'] = config.SSH_PASSWORD
            elif config.SSH_KEY_PATH:
                conn_args['client_keys'] = [config.SSH_KEY_PATH]
            
            connection = await asyncssh.connect(**conn_args)
            
            # Initialize session with home directory
            result = await connection.run("pwd", check=True)
            current_dir = result.stdout.strip()
            
            self.sessions[user_id] = {
                'connection': connection,
                'current_directory': current_dir,
                'lock': asyncio.Lock()
            }
            
            logger.info(f"Stateful SSH session created for user {user_id}, starting in: {current_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Session creation failed for user {user_id}: {e}")
            return False
    
    async def execute_in_session(self, user_id: int, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute command with state preservation"""
        if user_id not in self.sessions:
            success = await self.create_session(user_id)
            if not success:
                return False, "❌ Failed to create SSH session"
        
        session = self.sessions[user_id]
        
        async with session['lock']:
            try:
                # Handle cd commands specially
                if command.strip().startswith('cd '):
                    return await self._handle_cd_command(session, command, timeout)
                else:
                    # For other commands, execute in current directory
                    full_command = f"cd '{session['current_directory']}' && {command}"
                    result = await asyncio.wait_for(
                        session['connection'].run(full_command, check=True),
                        timeout=timeout
                    )
                    
                    output = result.stdout
                    if result.stderr:
                        output += f"\nStderr: {result.stderr}"
                    
                    return True, output.strip()
                    
            except asyncio.TimeoutError:
                return False, f"❌ Command timed out after {timeout} seconds"
            except asyncssh.ProcessError as e:
                return False, f"❌ Command failed: {e.stderr}"
            except Exception as e:
                return False, f"❌ Error: {e}"
    
    async def _handle_cd_command(self, session: dict, command: str, timeout: int) -> Tuple[bool, str]:
        """Handle cd command and update current directory"""
        try:
            parts = command.strip().split()
            if len(parts) < 2:
                return False, "❌ Invalid cd command: no directory specified"
            
            target_dir = parts[1]
            
            # If relative path, resolve it relative to current directory
            if not target_dir.startswith('/'):
                if session['current_directory'] == '/':
                    target_dir = '/' + target_dir
                else:
                    target_dir = session['current_directory'] + '/' + target_dir
            
            # Normalize path (resolve .. and .)
            target_dir = os.path.normpath(target_dir)
            
            # Check if directory exists and get absolute path
            result = await asyncio.wait_for(
                session['connection'].run(f"cd '{target_dir}' && pwd", check=True),
                timeout=timeout
            )
            
            new_dir = result.stdout.strip()
            session['current_directory'] = new_dir
            
            return True, f"Changed directory to: {new_dir}"
            
        except asyncssh.ProcessError as e:
            return False, f"❌ Directory not found or inaccessible: {e.stderr}"
        except Exception as e:
            return False, f"❌ Error changing directory: {e}"
    
    async def get_current_directory(self, user_id: int) -> Tuple[bool, str]:
        """Get current working directory"""
        if user_id not in self.sessions:
            return False, "No active session"
        
        return True, self.sessions[user_id]['current_directory']
    
    async def close_session(self, user_id: int):
        """Close user's session"""
        if user_id in self.sessions:
            try:
                self.sessions[user_id]['connection'].close()
                await self.sessions[user_id]['connection'].wait_closed()
            except:
                pass
            finally:
                del self.sessions[user_id]
                logger.info(f"SSH session closed for user {user_id}")
    
    async def close_all_sessions(self):
        """Close all sessions"""
        user_ids = list(self.sessions.keys())
        for user_id in user_ids:
            await self.close_session(user_id)
        
        if self.single_connection:
            self.single_connection.close()
            await self.single_connection.wait_closed()
            self.single_connection = None

# Alternative: use this for stateful emulation
ssh_client = StatefulSSHClient()