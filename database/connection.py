"""
Database connection management
"""
import asyncpg
from asyncpg import Pool
from loguru import logger
from config import Config
from .models import CREATE_TABLES_SQL
from typing import Optional

class DatabaseManager:
    def __init__(self):
        self.pool: Optional[Pool] = None
    
    async def connect(self) -> bool:
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                Config.DATABASE_URL,
                min_size=Config.DB_POOL_MIN_SIZE,
                max_size=Config.DB_POOL_MAX_SIZE,
                command_timeout=60
            )
            logger.info("Database connection pool created successfully")
            
            # Initialize database schema
            await self.init_schema()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            return False
    
    async def init_schema(self):
        """Initialize database schema"""
        try:
            async with self.pool.acquire() as conn:
                # Create tables one by one
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS group_settings (
                        group_id BIGINT PRIMARY KEY,
                        required_users INTEGER NOT NULL DEFAULT 5,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        bot_added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT NOT NULL,
                        group_id BIGINT NOT NULL,
                        username VARCHAR(255),
                        inviter_id BIGINT,
                        invited_count INTEGER DEFAULT 0,
                        is_restricted BOOLEAN DEFAULT TRUE,
                        joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        welcome_message_id INTEGER,
                        PRIMARY KEY (user_id, group_id)
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS admin_commands (
                        id SERIAL PRIMARY KEY,
                        group_id BIGINT NOT NULL,
                        admin_id BIGINT NOT NULL,
                        command VARCHAR(255) NOT NULL,
                        parameters TEXT,
                        executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        group_id BIGINT NOT NULL,
                        message_text TEXT NOT NULL,
                        response_text TEXT,
                        message_type VARCHAR(10) NOT NULL CHECK (message_type IN ('user', 'assistant')),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_group_id ON users(group_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_inviter_id ON users(inviter_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_is_restricted ON users(is_restricted)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_admin_commands_group_id ON admin_commands(group_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversation_history_user_group ON conversation_history(user_id, group_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversation_history_created_at ON conversation_history(created_at)")
                
                # Add columns for existing installations
                try:
                    await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS welcome_message_id INTEGER")
                    await conn.execute("ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS bot_added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
                except Exception:
                    # Columns might already exist, ignore errors
                    pass
                
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    def get_pool(self) -> Pool:
        """Get database connection pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return self.pool

# Global database manager instance
db_manager = DatabaseManager()