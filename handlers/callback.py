"""
Inline button callback handlers
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from loguru import logger
from services.user_tracker import user_tracker
from utils.messages import Messages

callback_router = Router()

@callback_router.callback_query(F.data.startswith("check_invites:"))
async def handle_check_invites_callback(callback_query: CallbackQuery):
    """Handle 'I added enough users' button callback"""
    try:
        # Extract user ID from callback data
        callback_data = callback_query.data
        user_id_from_callback = int(callback_data.split(":")[1])
        actual_user_id = callback_query.from_user.id
        
        # Verify that the user clicking the button is the same as the user in the callback data
        if user_id_from_callback != actual_user_id:
            await callback_query.answer("Bu tugma siz uchun emas!", show_alert=True)
            return
        
        # We need to determine which group this is for
        # Since we don't have group context in private callback, we'll need to check all groups
        # For now, let's assume the most recent group the user joined
        # In a production system, you might want to store group context in the callback data
        
        # For this implementation, we'll try to find the user's group from the database
        # This is a limitation of the current design - in a real implementation,
        # you might want to include group_id in the callback data
        
        await callback_query.answer("Tekshirilmoqda...")
        
        # We need to find which groups this user is in and check their status
        # Since we don't have a direct query for this, we'll need to implement it
        # For now, let's send a message indicating they should use the command in the group
        
        message = """
Iltimos, guruhda yozganingizni ko'ring. Agar siz yetarlicha foydalanuvchi qo'shgan bo'lsangiz, 
sizning cheklovingiz avtomatik ravishda olib tashlanadi.

Agar cheklov hali ham mavjud bo'lsa, bu siz hali yetarlicha foydalanuvchi qo'shmaganingizni anglatadi.
"""
        
        try:
            await callback_query.message.edit_text(message)
        except Exception:
            await callback_query.message.answer(message)
            
        logger.info(f"Check invites callback handled for user {actual_user_id}")
        
    except Exception as e:
        logger.error(f"Error handling check invites callback: {e}")
        await callback_query.answer("Xatolik yuz berdi!", show_alert=True)

@callback_router.callback_query(F.data.startswith("check_invites_group:"))
async def handle_check_invites_group_callback(callback_query: CallbackQuery):
    """Handle 'I added enough users' button callback with group context"""
    try:
        # Extract user ID and group ID from callback data
        callback_data = callback_query.data
        data_parts = callback_data.split(":")
        if len(data_parts) != 3:
            await callback_query.answer("Noto'g'ri ma'lumot!", show_alert=True)
            return
            
        user_id_from_callback = int(data_parts[1])
        group_id = int(data_parts[2])
        actual_user_id = callback_query.from_user.id
        
        # Verify that the user clicking the button is the same as the user in the callback data
        if user_id_from_callback != actual_user_id:
            await callback_query.answer("Bu tugma siz uchun emas!", show_alert=True)
            return
        
        await callback_query.answer("Tekshirilmoqda...")
        
        # Check user's invite status for the specific group
        success = await user_tracker.check_user_invite_status(
            callback_query.bot, actual_user_id, group_id
        )
        
        if success:
            # User was successfully unrestricted, send success message in group
            try:
                user_info = await callback_query.bot.get_chat_member(group_id, actual_user_id)
                username = callback_query.from_user.username or callback_query.from_user.first_name or f"User {actual_user_id}"
                success_message = f"🎉 @{username}, muvaffaqiyatli! Endi guruhda yoza olasiz."
                await callback_query.bot.send_message(group_id, success_message)
                
                # Also edit the original message
                await callback_query.message.edit_text("✅ " + Messages.ACCESS_GRANTED)
            except Exception as e:
                logger.error(f"Error sending success message: {e}")
        else:
            # User still doesn't have enough invites - the service will send appropriate message
            pass
            
        logger.info(f"Check invites group callback handled for user {actual_user_id} in group {group_id}")
        
    except Exception as e:
        logger.error(f"Error handling check invites group callback: {e}")
        await callback_query.answer("Xatolik yuz berdi!", show_alert=True)

# Enhanced welcome message sender with group context
async def send_welcome_message_with_group_context(bot, user_id: int, group_id: int, required_users: int, current_invites: int):
    """Enhanced version of welcome message that includes group context in callback"""
    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        message = Messages.format_welcome_message(required_users, current_invites)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=Messages.NOT_ENOUGH_INVITES_BUTTON,
                callback_data=f"check_invites_group:{user_id}:{group_id}"
            )]
        ])
        
        await bot.send_message(user_id, message, reply_markup=keyboard)
        logger.info(f"Welcome message with group context sent to user {user_id} for group {group_id}")
        
    except Exception as e:
        logger.error(f"Error sending welcome message with group context to user {user_id}: {e}")