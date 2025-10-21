import asyncssh
import asyncio
from typing import Optional, Tuple, Dict
from config.config import config
import logging

logger = logging.getLogger(__name__)
# WORKED
class SSHInteractiveClient:
    def __init__(self):
        self.sessions: Dict[int, dict] = {}  # user_id -> session info
    
    async def create_session(self, user_id: int) -> bool:
        """Create interactive shell session"""
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
            
            # Create connection and start shell
            conn = await asyncssh.connect(**conn_args)
            shell = await conn.create_process(term_type='xterm-256color')
            
            self.sessions[user_id] = {
                'connection': conn,
                'shell': shell,
                'stdin': shell.stdin,
                'stdout': shell.stdout,
                'stderr': shell.stderr
            }
            
            # Wait for shell to be ready
            await asyncio.sleep(0.5)
            
            logger.info(f"Interactive SSH session created for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create interactive session: {e}")
            return False
    
    async def execute_command(self, user_id: int, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute command in interactive shell"""
        if user_id not in self.sessions:
            return False, "❌ No active session"
        
        session = self.sessions[user_id]
        
        try:
            # Send command
            session['stdin'].write(command + '\n')
            
            # Read output with timeout
            output = await asyncio.wait_for(
                self._read_output(session['stdout']),
                timeout=timeout
            )
            
            # Clean output
            cleaned_output = self._clean_output(output, command)
            
            return True, cleaned_output
            
        except asyncio.TimeoutError:
            return False, "❌ Command timed out"
        except Exception as e:
            return False, f"❌ Error: {e}"
    
    async def _read_output(self, stdout) -> str:
        """Read output until we have reasonable data"""
        output = ""
        max_wait = 3.0  # Maximum time to wait for output
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < max_wait:
            try:
                # Try to read available data
                chunk = await asyncio.wait_for(stdout.read(1024), 0.1)
                if chunk:
                    output += chunk
                    # If we got some output and it seems complete, break
                    if len(output) > 10 and '\n' in output:
                        break
                else:
                    # If no data, wait a bit
                    await asyncio.sleep(0.1)
            except asyncio.TimeoutError:
                # If timeout reading, check if we have enough output
                if output:
                    break
                await asyncio.sleep(0.1)
        
        return output
    
    def _clean_output(self, output: str, command: str) -> str:
        """Clean the command output"""
        if not output:
            return "Command executed"
        
        # Remove command echo
        lines = output.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Skip the command itself and empty lines at start
            if stripped == command or (not cleaned_lines and not stripped):
                continue
            cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        return result if result else "Command executed"
    
    async def close_session(self, user_id: int):
        """Close interactive session"""
        if user_id in self.sessions:
            session = self.sessions[user_id]
            try:
                session['shell'].close()
                session['connection'].close()
                await session['connection'].wait_closed()
            except:
                pass
            finally:
                del self.sessions[user_id]
    
    async def close_all_sessions(self):
        """Close all sessions"""
        for user_id in list(self.sessions.keys()):
            await self.close_session(user_id)
