"""
Database queries for the Telegram bot
"""
from datetime import datetime
from typing import Optional, List
from loguru import logger
from .connection import db_manager
from .models import GroupSettings, User, AdminCommand

class DatabaseQueries:
    
    # Group Settings Queries
    @staticmethod
    async def get_group_settings(group_id: int) -> Optional[GroupSettings]:
        """Get group settings by group ID"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM group_settings WHERE group_id = $1",
                    group_id
                )
                if row:
                    return GroupSettings(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Error getting group settings for {group_id}: {e}")
            return None
    
    @staticmethod
    async def create_or_update_group_settings(group_id: int, required_users: int) -> bool:
        """Create or update group settings"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO group_settings (group_id, required_users, created_at, updated_at)
                    VALUES ($1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (group_id) 
                    DO UPDATE SET 
                        required_users = $2,
                        updated_at = CURRENT_TIMESTAMP
                """, group_id, required_users)
                return True
        except Exception as e:
            logger.error(f"Error updating group settings for {group_id}: {e}")
            return False
    
    # User Queries
    @staticmethod
    async def get_user(user_id: int, group_id: int) -> Optional[User]:
        """Get user by user ID and group ID"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE user_id = $1 AND group_id = $2",
                    user_id, group_id
                )
                if row:
                    return User(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Error getting user {user_id} in group {group_id}: {e}")
            return None
    
    @staticmethod
    async def create_user(user_id: int, group_id: int, username: Optional[str] = None, 
                         inviter_id: Optional[int] = None, is_restricted: bool = True) -> bool:
        """Create new user record"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO users (user_id, group_id, username, inviter_id, invited_count, is_restricted)
                    VALUES ($1, $2, $3, $4, 0, $5)
                    ON CONFLICT (user_id, group_id) DO NOTHING
                """, user_id, group_id, username, inviter_id, is_restricted)
                return True
        except Exception as e:
            logger.error(f"Error creating user {user_id} in group {group_id}: {e}")
            return False
    
    @staticmethod
    async def increment_user_invites(inviter_id: int, group_id: int) -> bool:
        """Increment the number of invites for a user"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE users 
                    SET invited_count = invited_count + 1,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = $1 AND group_id = $2
                """, inviter_id, group_id)
                return True
        except Exception as e:
            logger.error(f"Error incrementing invites for user {inviter_id}: {e}")
            return False
    
    @staticmethod
    async def update_user_restriction_status(user_id: int, group_id: int, is_restricted: bool) -> bool:
        """Update user restriction status"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE users 
                    SET is_restricted = $3,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = $1 AND group_id = $2
                """, user_id, group_id, is_restricted)
                return True
        except Exception as e:
            logger.error(f"Error updating restriction status for user {user_id}: {e}")
            return False
    
    @staticmethod
    async def get_restricted_users(group_id: int) -> List[User]:
        """Get all restricted users in a group"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM users WHERE group_id = $1 AND is_restricted = TRUE",
                    group_id
                )
                return [User(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting restricted users for group {group_id}: {e}")
            return []
    
    @staticmethod
    async def update_user_welcome_message_id(user_id: int, group_id: int, message_id: int) -> bool:
        """Update user's welcome message ID"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE users 
                    SET welcome_message_id = $3,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = $1 AND group_id = $2
                """, user_id, group_id, message_id)
                return True
        except Exception as e:
            logger.error(f"Error updating welcome message ID for user {user_id}: {e}")
            return False
    
    # Admin Commands Queries
    @staticmethod
    async def log_admin_command(group_id: int, admin_id: int, command: str, 
                               parameters: Optional[str] = None) -> bool:
        """Log admin command execution"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO admin_commands (group_id, admin_id, command, parameters)
                    VALUES ($1, $2, $3, $4)
                """, group_id, admin_id, command, parameters)
                return True
        except Exception as e:
            logger.error(f"Error logging admin command: {e}")
            return False
    
    # Conversation History Queries
    @staticmethod
    async def add_conversation_message(user_id: int, group_id: int, message_text: str, 
                                      message_type: str, response_text: str = None) -> bool:
        """Add message to conversation history"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO conversation_history (user_id, group_id, message_text, response_text, message_type)
                    VALUES ($1, $2, $3, $4, $5)
                """, user_id, group_id, message_text, response_text, message_type)
                return True
        except Exception as e:
            logger.error(f"Error adding conversation message: {e}")
            return False
    
    @staticmethod
    async def get_conversation_history(user_id: int, group_id: int, limit: int = 10) -> List[dict]:
        """Get recent conversation history for user in group"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT message_text, response_text, message_type, created_at
                    FROM conversation_history 
                    WHERE user_id = $1 AND group_id = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                """, user_id, group_id, limit)
                
                # Return in chronological order (oldest first)
                return [dict(row) for row in reversed(rows)]
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    @staticmethod
    async def cleanup_old_conversations(days_old: int = 7) -> bool:
        """Clean up conversation history older than specified days"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    DELETE FROM conversation_history 
                    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL $1
                """, f"{days_old} days")
                return True
        except Exception as e:
            logger.error(f"Error cleaning up old conversations: {e}")
            return False
    
    @staticmethod
    async def get_user_invite_count(user_id: int, group_id: int) -> int:
        """Get the number of users invited by a specific user"""
        try:
            pool = db_manager.get_pool()
            async with pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT invited_count FROM users WHERE user_id = $1 AND group_id = $2",
                    user_id, group_id
                )
                return result or 0
        except Exception as e:
            logger.error(f"Error getting invite count for user {user_id}: {e}")
            return 0