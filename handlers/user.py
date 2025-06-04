"""
User message handlers
"""
from aiogram import Router, F
from aiogram.types import Message
from loguru import logger
from database.queries import DatabaseQueries
from services.chatgpt import chatgpt_service
from services.user_tracker import user_tracker
from utils.helpers import is_user_admin, format_username
from utils.messages import Messages

user_router = Router()

@user_router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: Message):
    """Handle all messages in groups"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Skip if message is from bot itself
        if message.from_user.is_bot:
            return
        
        # Skip if user is admin
        if await is_user_admin(message.bot, chat_id, user_id):
            logger.debug(f"Skipping message from admin {user_id} in group {chat_id}")
            return
        
        # CRITICAL: Check if user exists in THIS SPECIFIC GROUP
        user = await DatabaseQueries.get_user(user_id, chat_id)
        
        if not user:
            # This is an existing user who was in the group before the bot
            # OR a new user who somehow bypassed the member join handler
            await user_tracker.handle_existing_user_message(
                message.bot, user_id, chat_id, message.from_user.username
            )
            # After handling, get the updated user record
            user = await DatabaseQueries.get_user(user_id, chat_id)
        
        if not user:
            # Still no user record, something went wrong
            logger.warning(f"Could not create user record for {user_id} in group {chat_id}")
            return
        
        # CRITICAL: Check if user is restricted IN THIS SPECIFIC GROUP
        if user.is_restricted:
            await user_tracker.handle_restricted_user_message(message.bot, message)
            return
        
        # User is not restricted IN THIS GROUP, process message with ChatGPT
        if message.text and len(message.text.strip()) > 0:
            await process_message_with_chatgpt(message)
            
    except Exception as e:
        logger.error(f"Error handling group message: {e}")

async def process_message_with_chatgpt(message: Message):
    """Process user message with ChatGPT"""
    try:
        user_id = message.from_user.id
        group_id = message.chat.id
        username = format_username(message.from_user)
        
        # Get ChatGPT response with conversation history
        chatgpt_response = await chatgpt_service.get_response_with_history(message.text, user_id, group_id)
        
        if chatgpt_response:
            # Send response tagging the user with retry logic
            response_text = f"{username}, {chatgpt_response}"
            
            # Try to send with retry logic for network issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await message.reply(response_text)
                    logger.info(f"ChatGPT response with history sent for user {user_id}")
                    return
                except Exception as send_error:
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed to send ChatGPT response: {send_error}")
                        import asyncio
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise send_error
        else:
            # Try fallback method
            fallback_response = await chatgpt_service.get_simple_response(message.text, user_id)
            if fallback_response:
                response_text = f"{username}, {fallback_response}"
                
                # Try to send fallback with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await message.reply(response_text)
                        logger.info(f"ChatGPT fallback response sent for user {user_id}")
                        return
                    except Exception as send_error:
                        if attempt < max_retries - 1:
                            logger.warning(f"Attempt {attempt + 1} failed to send fallback response: {send_error}")
                            import asyncio
                            await asyncio.sleep(2 ** attempt)
                        else:
                            raise send_error
            else:
                # Send error message
                await message.reply(f"{username}, {Messages.CHATGPT_ERROR}")
                logger.warning(f"ChatGPT service unavailable for user {user_id}")
                
    except Exception as e:
        logger.error(f"Error processing message with ChatGPT: {e}")
        try:
            username = format_username(message.from_user)
            # Try to send error message with simple retry
            for attempt in range(2):
                try:
                    await message.reply(f"{username}, {Messages.CHATGPT_ERROR}")
                    break
                except Exception:
                    if attempt == 0:
                        import asyncio
                        await asyncio.sleep(1)
                    else:
                        logger.error("Failed to send error message to user after retries")
        except Exception:
            logger.error("Failed to send error message to user")

@user_router.message(F.chat.type == "private")
async def handle_private_message(message: Message):
    """Handle private messages to the bot"""
    try:
        # For now, just send help message for private chats
        await message.reply(Messages.HELP_MESSAGE)
    except Exception as e:
        logger.error(f"Error handling private message: {e}")