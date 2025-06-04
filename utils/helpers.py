"""
Helper functions for the Telegram bot
"""
from aiogram import Bot
from aiogram.types import ChatMember, ChatPermissions
from loguru import logger
from typing import Optional

async def is_user_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Check if user is an administrator in the chat"""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        if "group chat was upgraded to a supergroup" in str(e):
            logger.warning(f"Group {chat_id} was upgraded to supergroup, admin check failed")
        return False

async def restrict_user(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Restrict user from sending messages"""
    try:
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=True,  # Allow inviting users
            can_pin_messages=False
        )
        
        result = await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=permissions
        )
        return result
    except Exception as e:
        logger.error(f"Error restricting user {user_id}: {e}")
        if "group chat was upgraded to a supergroup" in str(e):
            logger.warning(f"Group {chat_id} was upgraded to supergroup, restriction failed")
        return False

async def unrestrict_user(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Remove restrictions from user"""
    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        )
        
        result = await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=permissions
        )
        return result
    except Exception as e:
        logger.error(f"Error unrestricting user {user_id}: {e}")
        return False

def validate_required_users_count(count: int, min_val: int = 1, max_val: int = 20) -> bool:
    """Validate that the required users count is within acceptable range"""
    return min_val <= count <= max_val

async def get_chat_admins(bot: Bot, chat_id: int) -> list:
    """Get list of chat administrators"""
    try:
        administrators = await bot.get_chat_administrators(chat_id)
        return [admin.user.id for admin in administrators]
    except Exception as e:
        logger.error(f"Error getting chat admins: {e}")
        return []

def format_username(user) -> str:
    """Format username for display"""
    if user.username:
        return f"@{user.username}"
    elif user.first_name:
        return user.first_name
    else:
        return f"User {user.id}"