"""
Uzbek language message templates for the Telegram bot
"""

class Messages:
    # Welcome and restriction messages
    WELCOME_GROUP_MESSAGE = "⚠️ {username}, Guruhda yozish uchun {required_users} ta odam qo'shishingiz kerak.\n\nHozirda: {current_invites} ta\nKerak: {remaining} ta"
    
    WELCOME_PRIVATE_MESSAGE = """
Assalomu alaykum! Guruhda xabar yuborish uchun siz {required_users} ta yangi foydalanuvchi taklif qilishingiz kerak.

Hozirda siz {current_invites} ta foydalanuvchi qo'shdingiz.
Yana {remaining} ta foydalanuvchi qo'shing.

Yetarlicha foydalanuvchi qo'shganingizdan so'ng, quyidagi tugmani bosing.
"""

    NOT_ENOUGH_INVITES_BUTTON = "Men yetarlicha foydalanuvchi qo'shdim"
    
    # Group messages for restricted users
    GROUP_RESTRICTION_MESSAGE = "@{username}, siz xabar yuborish uchun yetarlicha foydalanuvchi qo'shmadingiz. Siz {current_invites} ta foydalanuvchi qo'shdingiz, yana {remaining} ta qo'shing."
    
    # Success messages
    ACCESS_GRANTED = "Tabriklaymiz! Endi siz guruhda xabar yuborishingiz mumkin. 🎉"
    
    # Admin messages
    ADMIN_ONLY_COMMAND = "Bu buyruq faqat guruh administratorlari uchun mo'ljallangan."
    INVALID_NUMBER_RANGE = "Iltimos, 1 dan 20 gacha bo'lgan son kiriting."
    REQUIRED_USERS_UPDATED = "Guruh sozlamalari yangilandi. Endi yangi foydalanuvchilar {count} ta odam taklif qilishlari kerak."
    
    # Error messages
    CHATGPT_ERROR = "ChatGPT xizmati hozirda ishlamayapti, keyinroq urinib ko'ring."
    DATABASE_ERROR = "Ma'lumotlar bazasida xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
    GENERAL_ERROR = "Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
    
    # Callback messages
    STILL_NOT_ENOUGH = "Siz hali ham yetarlicha foydalanuvchi qo'shmadingiz. Yana {remaining} ta foydalanuvchi qo'shing."
    
    # Help messages
    HELP_MESSAGE = """
Bot buyruqlari:

/set_required_users (son) - Talab qilinadigan foydalanuvchilar sonini o'rnatish (1-20)
/help - Yordam

Guruhga yangi a'zolar qo'shish uchun do'stlaringizni taklif qiling!
"""

    @staticmethod
    def format_group_welcome_message(username: str, required_users: int, current_invites: int) -> str:
        remaining = max(0, required_users - current_invites)
        return Messages.WELCOME_GROUP_MESSAGE.format(
            username=username,
            required_users=required_users,
            current_invites=current_invites,
            remaining=remaining
        )
    
    @staticmethod
    def format_welcome_message(required_users: int, current_invites: int) -> str:
        remaining = max(0, required_users - current_invites)
        return Messages.WELCOME_PRIVATE_MESSAGE.format(
            required_users=required_users,
            current_invites=current_invites,
            remaining=remaining
        )
    
    @staticmethod
    def format_group_restriction_message(username: str, current_invites: int, required_users: int) -> str:
        remaining = max(0, required_users - current_invites)
        return Messages.GROUP_RESTRICTION_MESSAGE.format(
            username=username,
            current_invites=current_invites,
            remaining=remaining
        )
    
    @staticmethod
    def format_still_not_enough(remaining: int) -> str:
        return Messages.STILL_NOT_ENOUGH.format(remaining=remaining)