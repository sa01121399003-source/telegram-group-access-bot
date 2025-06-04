"""
New member join handlers
"""
from aiogram import Router, F
from aiogram.types import ChatMemberUpdated
from loguru import logger
from services.user_tracker import user_tracker
from utils.helpers import format_username

member_router = Router()

@member_router.chat_member()
async def handle_chat_member_update(chat_member_update: ChatMemberUpdated):
    """Handle new members joining the group"""
    try:
        # Check if this is a new member joining
        old_status = chat_member_update.old_chat_member.status
        new_status = chat_member_update.new_chat_member.status
        
        # Get the user who joined
        joined_user = chat_member_update.new_chat_member.user
        chat_id = chat_member_update.chat.id
        
        # Check if this is a bot being added to the group
        if new_status == "member" and joined_user.is_bot and joined_user.id == chat_member_update.bot.id:
            # The bot itself was added to the group
            logger.info(f"Bot was added to group {chat_id}")
            await user_tracker.initialize_existing_group(chat_member_update.bot, chat_id)
            return
        
        # User joined the group
        if old_status in ["left", "kicked"] and new_status == "member":
            # Skip if user is bot
            if joined_user.is_bot:
                logger.debug(f"Skipping bot user {joined_user.id}")
                return
            
            # Get inviter information
            inviter_id = None
            if chat_member_update.from_user and chat_member_update.from_user.id != joined_user.id:
                inviter_id = chat_member_update.from_user.id
                logger.info(f"User {joined_user.id} invited by {inviter_id} to group {chat_id}")
            else:
                logger.info(f"User {joined_user.id} joined group {chat_id} (inviter unknown)")
            
            # Handle new member
            success = await user_tracker.handle_new_member(
                bot=chat_member_update.bot,
                group_id=chat_id,
                new_user_id=joined_user.id,
                new_username=joined_user.username,
                inviter_id=inviter_id
            )
            
            if success:
                username = format_username(joined_user)
                logger.info(f"New member {username} ({joined_user.id}) processed for group {chat_id}")
            else:
                logger.error(f"Failed to process new member {joined_user.id} for group {chat_id}")
            
        # User left the group
        elif old_status == "member" and new_status in ["left", "kicked"]:
            left_user = chat_member_update.old_chat_member.user
            
            # Note: We could implement cleanup logic here if needed
            # For now, we'll keep the user data for potential rejoining
            
            username = format_username(left_user)
            logger.info(f"Member {username} ({left_user.id}) left group {chat_id}")
            
    except Exception as e:
        logger.error(f"Error handling chat member update: {e}")

@member_router.message(F.content_type == "new_chat_members")
async def handle_new_chat_members_fallback(message):
    """Fallback handler for new chat members (in case chat_member update doesn't work)"""
    try:
        chat_id = message.chat.id
        
        for new_member in message.new_chat_members:
            # Skip if user is bot
            if new_member.is_bot:
                continue
            
            # Try to determine inviter (the user who sent the message)
            inviter_id = None
            if message.from_user and message.from_user.id != new_member.id:
                inviter_id = message.from_user.id
            
            # Handle new member
            await user_tracker.handle_new_member(
                bot=message.bot,
                group_id=chat_id,
                new_user_id=new_member.id,
                new_username=new_member.username,
                inviter_id=inviter_id
            )
            
            username = format_username(new_member)
            logger.info(f"New member {username} ({new_member.id}) processed via fallback for group {chat_id}")
            
    except Exception as e:
        logger.error(f"Error in new chat members fallback handler: {e}")