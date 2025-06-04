"""
User tracking service for managing invitations and restrictions
"""
from aiogram import Bot
from loguru import logger
from typing import Optional
from database.queries import DatabaseQueries
from utils.helpers import restrict_user, unrestrict_user, format_username
from utils.messages import Messages
from config import Config

class UserTracker:
    
    @staticmethod
    async def initialize_existing_group(bot: Bot, group_id: int) -> bool:
        """Initialize bot for an existing group with existing members"""
        try:
            # Get group settings or create default
            group_settings = await DatabaseQueries.get_group_settings(group_id)
            if not group_settings:
                await DatabaseQueries.create_or_update_group_settings(
                    group_id, Config.DEFAULT_REQUIRED_USERS
                )
            
            # Get all current group members
            try:
                member_count = await bot.get_chat_member_count(group_id)
                logger.info(f"Found existing group {group_id} with {member_count} members")
                
                # Mark all existing members as unrestricted (grandfathered in)
                # We'll do this when they first interact, not proactively
                return True
                
            except Exception as e:
                logger.error(f"Error getting member count for group {group_id}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing existing group {group_id}: {e}")
            return False
    
    @staticmethod
    async def handle_existing_user_message(bot: Bot, user_id: int, group_id: int, username: str = None) -> bool:
        """Handle message from user who was in group before bot was added OR is new to this group"""
        try:
            # Check if user exists in THIS SPECIFIC GROUP
            user = await DatabaseQueries.get_user(user_id, group_id)
            
            if not user:
                # User doesn't exist in this group's database
                # This could be:
                # 1. Existing user who was in group before bot was added (grandfather them)
                # 2. New user who somehow bypassed join detection (restrict them)
                
                # For now, we'll assume they're a NEW user and restrict them
                # Admin can use /grandfather_existing if they want to unrestrict existing users
                
                await DatabaseQueries.create_user(
                    user_id=user_id,
                    group_id=group_id,
                    username=username,
                    inviter_id=None,
                    is_restricted=True  # Restrict by default, admin can grandfather if needed
                )
                
                # Set them as RESTRICTED (they need to add users in this group)
                await DatabaseQueries.update_user_restriction_status(user_id, group_id, True)
                
                # Restrict them in Telegram
                await restrict_user(bot, group_id, user_id)
                
                # Get group settings and send welcome message
                group_settings = await DatabaseQueries.get_group_settings(group_id)
                if group_settings:
                    await UserTracker.send_group_welcome_message(
                        bot, group_id, user_id, group_settings.required_users, 0
                    )
                
                logger.info(f"New user {user_id} created as RESTRICTED in group {group_id}")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling existing user {user_id}: {e}")
            return False
    
    @staticmethod
    async def send_group_welcome_message(bot: Bot, group_id: int, user_id: int, required_users: int, current_invites: int):
        """Send welcome message to new user in the group"""
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from utils.helpers import format_username
            
            # Check if user already has a welcome message to prevent duplicates
            existing_user = await DatabaseQueries.get_user(user_id, group_id)
            if existing_user and existing_user.welcome_message_id:
                logger.info(f"User {user_id} already has welcome message {existing_user.welcome_message_id}, skipping duplicate")
                return
            
            # Get user info for formatting
            try:
                user_info = await bot.get_chat_member(group_id, user_id)
                username = format_username(user_info.user)
            except Exception:
                username = f"User {user_id}"
            
            message = Messages.format_group_welcome_message(username, required_users, current_invites)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=Messages.NOT_ENOUGH_INVITES_BUTTON,
                    callback_data=f"check_invites_group:{user_id}:{group_id}"
                )]
            ])
            
            # Send the message and store the message ID
            sent_message = await bot.send_message(group_id, message, reply_markup=keyboard)
            
            # Store the message ID in database for later deletion
            await DatabaseQueries.update_user_welcome_message_id(user_id, group_id, sent_message.message_id)
            
            logger.info(f"Group welcome message sent to user {user_id} in group {group_id}, message ID: {sent_message.message_id}")
            
        except Exception as e:
            logger.error(f"Error sending group welcome message to user {user_id}: {e}")
    
    @staticmethod
    async def delete_welcome_message(bot: Bot, user_id: int, group_id: int):
        """Delete user's welcome message"""
        try:
            user = await DatabaseQueries.get_user(user_id, group_id)
            if user and user.welcome_message_id:
                try:
                    await bot.delete_message(group_id, user.welcome_message_id)
                    logger.info(f"Deleted welcome message {user.welcome_message_id} for user {user_id}")
                    
                    # Clear the message ID from database
                    await DatabaseQueries.update_user_welcome_message_id(user_id, group_id, None)
                except Exception as e:
                    logger.warning(f"Could not delete welcome message {user.welcome_message_id}: {e}")
        except Exception as e:
            logger.error(f"Error deleting welcome message for user {user_id}: {e}")
    
    @staticmethod
    async def handle_new_member(bot: Bot, group_id: int, new_user_id: int, 
                               new_username: Optional[str], inviter_id: Optional[int] = None) -> bool:
        """Handle new member joining the group"""
        try:
            # Get group settings
            group_settings = await DatabaseQueries.get_group_settings(group_id)
            if not group_settings:
                # Create default group settings
                success = await DatabaseQueries.create_or_update_group_settings(
                    group_id, Config.DEFAULT_REQUIRED_USERS
                )
                if success:
                    group_settings = await DatabaseQueries.get_group_settings(group_id)
                
                if not group_settings:
                    logger.error(f"Failed to create/get group settings for {group_id}")
                    return False
            
            # Create user record (restricted by default for new joiners)
            await DatabaseQueries.create_user(
                user_id=new_user_id,
                group_id=group_id,
                username=new_username,
                inviter_id=inviter_id,
                is_restricted=True  # Always restrict new joiners
            )
            
            # DON'T restrict them in Telegram initially for users added by others
            # This avoids the confusing system message
            if not inviter_id:
                # User joined by themselves - restrict them
                restriction_success = await restrict_user(bot, group_id, new_user_id)
                if not restriction_success:
                    logger.warning(f"Failed to restrict user {new_user_id} in group {group_id}")
            else:
                # User was added by someone - we'll handle restriction via message deletion
                logger.info(f"User {new_user_id} added by {inviter_id} - will be handled via message deletion")
            
            # If there's an inviter, increment their invite count
            if inviter_id:
                await DatabaseQueries.increment_user_invites(inviter_id, group_id)
                
                # Delete the inviter's welcome message since they added someone
                await UserTracker.delete_welcome_message(bot, inviter_id, group_id)
                
                # Check if inviter now has enough invites to be unrestricted
                await UserTracker.check_and_update_inviter_status(bot, inviter_id, group_id)
            
            # Send welcome message logic:
            # - Users who joined by themselves (no inviter): GET welcome message immediately
            # - Users who were added by others (has inviter): NO welcome message initially
            #   (they'll get restriction message when they try to write)
            # - Exception: Don't welcome the bot itself
            
            if not inviter_id and new_user_id != bot.id:
                # User joined by themselves (via link, etc.) - they need to add people
                await UserTracker.send_group_welcome_message(bot, group_id, new_user_id, group_settings.required_users, 0)
                logger.info(f"Welcome message sent to self-joined user {new_user_id}")
            elif inviter_id:
                # User was added by someone else - they also need to add people
                # But we don't send welcome message immediately, only when they try to write
                logger.info(f"User {new_user_id} added by {inviter_id} - will be restricted until they add users")
            else:
                logger.info(f"Bot {new_user_id} added to group - no action needed")
            
            logger.info(f"New member {new_user_id} added to group {group_id}, invited by {inviter_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling new member {new_user_id}: {e}")
            return False
    
    @staticmethod
    async def check_and_update_inviter_status(bot: Bot, user_id: int, group_id: int) -> bool:
        """Check if user has enough invites and update their status"""
        try:
            user = await DatabaseQueries.get_user(user_id, group_id)
            group_settings = await DatabaseQueries.get_group_settings(group_id)
            
            if not user or not group_settings:
                return False
            
            # Check if user has enough invites and is currently restricted
            if user.invited_count >= group_settings.required_users and user.is_restricted:
                # Unrestrict the user
                unrestrict_success = await unrestrict_user(bot, group_id, user_id)
                if unrestrict_success:
                    # Update database
                    await DatabaseQueries.update_user_restriction_status(user_id, group_id, False)
                    
                    # Delete the welcome message since user is now unrestricted
                    await UserTracker.delete_welcome_message(bot, user_id, group_id)
                    
                    # Send success message
                    try:
                        await bot.send_message(user_id, Messages.ACCESS_GRANTED)
                    except Exception:
                        logger.warning(f"Could not send success message to user {user_id}")
                    
                    logger.info(f"User {user_id} unrestricted in group {group_id}")
                    return True
                else:
                    logger.warning(f"Failed to unrestrict user {user_id} in group {group_id}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking inviter status for user {user_id}: {e}")
            return False
    
    @staticmethod
    async def send_welcome_message(bot: Bot, user_id: int, required_users: int, current_invites: int):
        """Send welcome message to new user"""
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            message = Messages.format_welcome_message(required_users, current_invites)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=Messages.NOT_ENOUGH_INVITES_BUTTON,
                    callback_data=f"check_invites:{user_id}"
                )]
            ])
            
            await bot.send_message(user_id, message, reply_markup=keyboard)
            logger.info(f"Welcome message sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending welcome message to user {user_id}: {e}")
    
    @staticmethod
    async def handle_restricted_user_message(bot: Bot, message) -> bool:
        """Handle message from restricted user"""
        try:
            user_id = message.from_user.id
            group_id = message.chat.id
            username = format_username(message.from_user)
            
            # Delete the message
            try:
                await message.delete()
            except Exception:
                logger.warning(f"Could not delete message from restricted user {user_id}")
            
            # Get user data
            user = await DatabaseQueries.get_user(user_id, group_id)
            group_settings = await DatabaseQueries.get_group_settings(group_id)
            
            if user and group_settings:
                # Different behavior for users who joined by themselves vs. users added by others
                if user.inviter_id is None:
                    # User joined by themselves - send group notification + welcome message (if missing)
                    notification_message = Messages.format_group_restriction_message(
                        username, user.invited_count, group_settings.required_users
                    )
                    await bot.send_message(group_id, notification_message)
                    
                    # If somehow they don't have a welcome message, send one
                    if not user.welcome_message_id:
                        await UserTracker.send_group_welcome_message(
                            bot, group_id, user_id, group_settings.required_users, user.invited_count
                        )
                        logger.warning(f"User {user_id} joined by themselves but missing welcome message - sent now")
                    
                    logger.info(f"Restriction notification sent for self-joined user {user_id} in group {group_id}")
                else:
                    # User was added by someone else - ONLY send welcome message with button (no group notification)
                    if not user.welcome_message_id:
                        await UserTracker.send_group_welcome_message(
                            bot, group_id, user_id, group_settings.required_users, user.invited_count
                        )
                        logger.info(f"Welcome message sent to user {user_id} who was added by {user.inviter_id}")
                    else:
                        logger.info(f"User {user_id} (added by {user.inviter_id}) already has welcome message, no action needed")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling restricted user message: {e}")
            return False
    
    @staticmethod
    async def check_user_invite_status(bot: Bot, user_id: int, group_id: int) -> bool:
        """Check and update user's invite status (for callback handling)"""
        try:
            user = await DatabaseQueries.get_user(user_id, group_id)
            group_settings = await DatabaseQueries.get_group_settings(group_id)
            
            if not user or not group_settings:
                return False
            
            if user.invited_count >= group_settings.required_users:
                # User has enough invites, unrestrict them
                return await UserTracker.check_and_update_inviter_status(bot, user_id, group_id)
            else:
                # Still not enough invites
                remaining = group_settings.required_users - user.invited_count
                message = Messages.format_still_not_enough(remaining)
                
                try:
                    await bot.send_message(user_id, message)
                except Exception:
                    logger.warning(f"Could not send 'still not enough' message to user {user_id}")
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking user invite status: {e}")
            return False

# Global user tracker instance
user_tracker = UserTracker()