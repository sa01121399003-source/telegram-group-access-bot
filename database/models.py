"""
Database models and schemas for the Telegram bot
"""
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class GroupSettings:
    group_id: int
    required_users: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    bot_added_at: Optional[datetime] = None

@dataclass
class User:
    user_id: int
    username: Optional[str]
    group_id: int
    inviter_id: Optional[int]
    invited_count: int
    is_restricted: bool
    joined_at: datetime
    last_updated: Optional[datetime] = None
    welcome_message_id: Optional[int] = None  # Store the welcome message ID

@dataclass
class AdminCommand:
    id: Optional[int]
    group_id: int
    admin_id: int
    command: str
    parameters: Optional[str]
    executed_at: datetime

# SQL Schemas
CREATE_TABLES_SQL = """
-- Group settings table
CREATE TABLE IF NOT EXISTS group_settings (
    group_id BIGINT PRIMARY KEY,
    required_users INTEGER NOT NULL DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    username VARCHAR(255),
    inviter_id BIGINT,
    invited_count INTEGER DEFAULT 0,
    is_restricted BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (group_id) REFERENCES group_settings(group_id) ON DELETE CASCADE
);

-- Admin commands log table
CREATE TABLE IF NOT EXISTS admin_commands (
    id SERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL,
    admin_id BIGINT NOT NULL,
    command VARCHAR(255) NOT NULL,
    parameters TEXT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES group_settings(group_id) ON DELETE CASCADE
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_group_id ON users(group_id);
CREATE INDEX IF NOT EXISTS idx_users_inviter_id ON users(inviter_id);
CREATE INDEX IF NOT EXISTS idx_users_is_restricted ON users(is_restricted);
CREATE INDEX IF NOT EXISTS idx_admin_commands_group_id ON admin_commands(group_id);

-- Update trigger function for group_settings
CREATE OR REPLACE FUNCTION update_group_settings_timestamp()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Create trigger only if it doesn't exist
DO $
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_update_group_settings_timestamp') THEN
        CREATE TRIGGER trigger_update_group_settings_timestamp
            BEFORE UPDATE ON group_settings
            FOR EACH ROW
            EXECUTE FUNCTION update_group_settings_timestamp();
    END IF;
END;
$;

-- Update trigger function for users
CREATE OR REPLACE FUNCTION update_users_timestamp()
RETURNS TRIGGER AS $
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Create trigger only if it doesn't exist
DO $
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_update_users_timestamp') THEN
        CREATE TRIGGER trigger_update_users_timestamp
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_users_timestamp();
    END IF;
END;
$;
"""