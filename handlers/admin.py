"""
Admin command handlers
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from loguru import logger
from database.queries import DatabaseQueries
from utils.helpers import is_user_admin, validate_required_users_count, unrestrict_user
from utils.messages import Messages
from config import Config
from services.user_tracker import user_tracker

admin_router = Router()

@admin_router.message(Command("set_required_users"))
async def set_required_users_command(message: Message):
    """Handle /set_required_users command"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Check if user is admin
        if not await is_user_admin(message.bot, chat_id, user_id):
            await message.reply(Messages.ADMIN_ONLY_COMMAND)
            return
        
        # Parse command arguments
        command_parts = message.text.split()
        if len(command_parts) != 2:
            await message.reply(Messages.INVALID_NUMBER_RANGE)
            return
        
        try:
            required_users = int(command_parts[1])
        except ValueError:
            await message.reply(Messages.INVALID_NUMBER_RANGE)
            return
        
        # Validate range
        if not validate_required_users_count(required_users, Config.MIN_REQUIRED_USERS, Config.MAX_REQUIRED_USERS):
            await message.reply(Messages.INVALID_NUMBER_RANGE)
            return
        
        # Update group settings
        success = await DatabaseQueries.create_or_update_group_settings(chat_id, required_users)
        
        if success:
            # Log admin command
            await DatabaseQueries.log_admin_command(
                group_id=chat_id,
                admin_id=user_id,
                command="set_required_users",
                parameters=str(required_users)
            )
            
            await message.reply(Messages.REQUIRED_USERS_UPDATED.format(count=required_users))
            logger.info(f"Required users updated to {required_users} for group {chat_id} by admin {user_id}")
        else:
            await message.reply(Messages.DATABASE_ERROR)
            
    except Exception as e:
        logger.error(f"Error in set_required_users command: {e}")
        await message.reply(Messages.GENERAL_ERROR)

@admin_router.message(Command("help"))
async def help_command(message: Message):
    """Handle /help command"""
    try:
        await message.reply(Messages.HELP_MESSAGE)
    except Exception as e:
        logger.error(f"Error in help command: {e}")

@admin_router.message(Command("grandfather_existing"))
async def grandfather_existing_command(message: Message):
    """Handle /grandfather_existing command - marks all current users as unrestricted"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Check if user is admin
        if not await is_user_admin(message.bot, chat_id, user_id):
            await message.reply(Messages.ADMIN_ONLY_COMMAND)
            return
        
        # Get all restricted users in this group
        restricted_users = await DatabaseQueries.get_restricted_users(chat_id)
        
        if not restricted_users:
            await message.reply("✅ Hech qanday cheklangan foydalanuvchi topilmadi.")
            return
        
        # Unrestrict all current restricted users
        unrestricted_count = 0
        for user_record in restricted_users:
            try:
                # Remove Telegram restriction
                await unrestrict_user(message.bot, chat_id, user_record.user_id)
                
                # Update database
                await DatabaseQueries.update_user_restriction_status(
                    user_record.user_id, chat_id, False
                )
                
                # Delete their welcome message if it exists
                await user_tracker.delete_welcome_message(message.bot, user_record.user_id, chat_id)
                
                unrestricted_count += 1
                
            except Exception as e:
                logger.error(f"Error unrestricting user {user_record.user_id}: {e}")
        
        await message.reply(f"✅ {unrestricted_count} ta foydalanuvchi cheklashdan ozod qilindi. Endi faqat yangi qo'shilgan a'zolar cheklanadi.")
        
        # Log admin command
        await DatabaseQueries.log_admin_command(
            group_id=chat_id,
            admin_id=user_id,
            command="grandfather_existing",
            parameters=f"unrestricted_{unrestricted_count}_users"
        )
        
        logger.info(f"Grandfathering executed for {unrestricted_count} users in group {chat_id} by admin {user_id}")
            
    except Exception as e:
        logger.error(f"Error in grandfather_existing command: {e}")
        await message.reply(Messages.GENERAL_ERROR)

@admin_router.message(Command("status"))
async def status_command(message: Message):
    """Handle /status command - show group statistics"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Check if user is admin
        if not await is_user_admin(message.bot, chat_id, user_id):
            await message.reply(Messages.ADMIN_ONLY_COMMAND)
            return
        
        # Get group settings
        group_settings = await DatabaseQueries.get_group_settings(chat_id)
        if not group_settings:
            await message.reply("Guruh sozlamalari topilmadi.")
            return
        
        # Get restricted users count
        restricted_users = await DatabaseQueries.get_restricted_users(chat_id)
        restricted_count = len(restricted_users)
        
        status_message = f"""
📊 **Guruh statistikasi:**

⚙️ Talab qilinadigan foydalanuvchilar: {group_settings.required_users}
🚫 Cheklangan foydalanuvchilar: {restricted_count}
📅 Sozlamalar yangilangan: {group_settings.updated_at.strftime('%Y-%m-%d %H:%M') if group_settings.updated_at else 'Noma\'lum'}
"""
        
        await message.reply(status_message)
        logger.info(f"Status command executed by admin {user_id} in group {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await message.reply(Messages.GENERAL_ERROR)