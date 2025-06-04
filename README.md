# Telegram Group Access Control Bot

A sophisticated Telegram bot that manages user access to groups by requiring new members to invite a configurable number of users before they can send messages. The bot integrates with ChatGPT to provide AI-powered responses and uses PostgreSQL for data persistence.

## Features

- 🔒 **Access Control**: Restricts new members until they invite required number of users (1-20)
- 🤖 **ChatGPT Integration**: AI-powered responses with conversation history for unrestricted users
- 📊 **Admin Dashboard**: Configure settings and view group statistics
- 🗄️ **PostgreSQL Database**: Robust data persistence with connection pooling
- 🇺🇿 **Uzbek Language**: All user-facing messages in Uzbek
- 📝 **Comprehensive Logging**: Detailed logging for debugging and monitoring
- ⚡ **High Performance**: Asynchronous processing with aiogram 3.x
- 🔄 **Network Resilience**: Retry logic with exponential backoff for network errors
- 🚫 **Duplicate Prevention**: Smart welcome message handling to prevent spam
- 💬 **Conversation Memory**: ChatGPT maintains conversation history per user/group

## Requirements

- Python 3.8+
- PostgreSQL 12+
- Telegram Bot Token
- OpenAI API Key and Assistant ID

## Installation

### Option 1: Using Docker (Recommended for Development)

1. **Clone the repository**
```bash
git clone <repository-url>
cd chatbot-7
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up PostgreSQL with Docker**
```bash
docker-compose up -d postgres
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Run the bot**
```bash
python main.py
```

### Option 2: Production Server Setup

1. **Install PostgreSQL on your server**
```powershell
# Windows Server (using Chocolatey)
choco install postgresql

# Or download from https://www.postgresql.org/download/windows/
```

2. **Copy project files** (exclude `__pycache__` and `logs` folders)
```
main.py
config.py
requirements.txt
setup_database.sql
.env
database/
handlers/
services/
utils/
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup database**
```bash
# Run the provided setup script
psql -U postgres -f setup_database.sql
```

5. **Configure environment variables**
- Update `.env` with your production values
- Ensure database password matches the setup script

6. **Run the bot**
```bash
python main.py
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# ChatGPT Configuration
CHATGPT_API_KEY=your_openai_api_key_here
CHATGPT_ASSISTANT_ID=your_assistant_id_here

# PostgreSQL Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/telegram_bot_db

# Optional Settings
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=20
LOG_LEVEL=INFO
```

### Bot Setup

1. **Create Telegram Bot**
   - Message @BotFather on Telegram
   - Use `/newbot` command and follow instructions
   - Copy the bot token to your `.env` file

2. **Add Bot to Group**
   - Add your bot to the target Telegram group
   - Promote bot to administrator with these permissions:
     - Delete messages
     - Restrict members
     - Invite users via link

3. **OpenAI Setup**
   - Get API key from OpenAI dashboard
   - Create an assistant and copy the assistant ID

## Usage

### Admin Commands

- `/set_required_users <number>` - Set required number of invites (1-20)
- `/status` - View group statistics
- `/grandfather_existing` - Unrestrict all current members when bot is added to existing groups
- `/help` - Show help message

### User Flow

1. **New Member Joins**: Bot automatically restricts messaging privileges
2. **Welcome Handling**: 
   - Users who join by themselves: Get group notification + private welcome message
   - Users added by others: Only get private welcome message (prevents duplicate notifications)
3. **Private Message**: Bot sends welcome message with invite requirement
4. **Invite Process**: User invites required number of people
5. **Status Check**: User clicks "I added enough users" button
6. **Access Granted**: Bot removes restrictions if requirement met
7. **ChatGPT Responses**: Unrestricted users get AI responses with conversation history

### Existing Group Members

When adding the bot to an established group with existing members:

1. **Automatic Restriction**: All existing members are initially restricted (can't send messages)
2. **Admin Solution**: Group admin runs `/grandfather_existing` command
3. **Mass Unrestriction**: All current members are automatically unrestricted
4. **Future Members**: Only new members joining after bot addition will face invite requirements

This prevents existing group members from needing to invite users to regain access.

## Database Schema

### Tables

- **group_settings**: Group configuration (required users count, timestamps)
- **users**: User tracking (invite count, restriction status, welcome message IDs)
- **admin_commands**: Command execution log with parameters
- **conversation_history**: ChatGPT conversation history per user/group

### Key Features

- Automatic timestamp updates with triggers
- Foreign key constraints for data integrity
- Optimized indexes for performance
- Connection pooling for scalability
- Transaction safety with proper error handling
- Conversation history cleanup (7-day retention)

## Architecture

```
telegram_bot/
├── main.py              # Application entry point
├── config.py           # Configuration management
├── database/           # Database layer
│   ├── models.py       # Data models and schemas
│   ├── connection.py   # Connection management
│   └── queries.py      # Database operations
├── handlers/           # Event handlers
│   ├── admin.py        # Admin commands
│   ├── user.py         # User messages
│   ├── member.py       # Member join/leave
│   └── callback.py     # Button callbacks
├── services/           # Business logic
│   ├── chatgpt.py      # ChatGPT integration
│   └── user_tracker.py # User management
└── utils/              # Utilities
    ├── messages.py     # Uzbek message templates
    └── helpers.py      # Helper functions
```

## Security Features

- Input validation for all commands and user inputs
- Admin-only command restrictions with proper authorization
- SQL injection prevention with parameterized queries
- Error handling with graceful degradation
- Comprehensive logging for security audit trails
- Network timeout and retry protection
- Rate limiting through OpenAI client configuration

## Monitoring and Logging

- Structured logging with loguru
- Log rotation (daily)
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)
- File and console output
- Performance monitoring for database operations

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running: `systemctl status postgresql` (Linux) or check Windows Services
   - Verify DATABASE_URL format: `postgresql://user:password@host:port/database`
   - Ensure database exists: Use `setup_database.sql` script
   - Check user permissions and password

2. **Bot Not Responding**
   - Verify bot token is correct in `.env`
   - Check bot has admin permissions in group:
     - Delete messages
     - Restrict members
     - Invite users via link
   - Review logs for errors: `logs/bot.log`

3. **ChatGPT Not Working**
   - Verify OpenAI API key is valid and has credits
   - Check assistant ID is correct
   - Monitor API rate limits and quotas
   - Check network connectivity for API calls

4. **Network Connectivity Issues**
   - Bot includes retry logic with exponential backoff (3 attempts)
   - Check server's internet connection
   - Verify firewall isn't blocking outbound HTTPS (443)
   - Monitor logs for "network connectivity" errors

5. **Duplicate Welcome Messages**
   - Fixed in current version with smart detection
   - Users added by others vs. self-joined are handled differently
   - Check logs for "duplicate prevention" messages

### Performance Issues

- **High Memory Usage**: Check connection pool settings in `.env`
- **Slow Responses**: Monitor database query performance in logs
- **API Timeouts**: Increase timeout settings in config if needed

### Logs Location

- Console output: Real-time logs with color coding
- File logs: `logs/bot.log` (rotated daily)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Structured logging with timestamps and context

## Recent Improvements

### v2.1.0 - Network Resilience & Bug Fixes
- ✅ **Network Error Handling**: Added retry logic with exponential backoff for ChatGPT API calls
- ✅ **Duplicate Message Prevention**: Fixed duplicate welcome messages for users added by others
- ✅ **SQL Security**: Fixed SQL injection vulnerability in conversation cleanup
- ✅ **Enhanced Logging**: Improved error tracking and debugging information
- ✅ **OpenAI Integration**: Added explicit timeout and retry parameters
- ✅ **Database Optimization**: Added conversation history table with proper indexes

### v2.0.0 - ChatGPT Integration
- 🤖 **Conversation History**: ChatGPT now maintains context per user/group
- 📝 **Smart Responses**: AI responses only for unrestricted users
- 🔄 **Fallback System**: Multiple response methods for reliability
- 🗄️ **History Management**: Automatic cleanup of old conversations (7 days)

### v1.5.0 - Production Ready
- 🔒 **Security Hardening**: Input validation and SQL injection prevention
- ⚡ **Performance**: Connection pooling and optimized database queries
- 📊 **Monitoring**: Comprehensive logging and error tracking
- 🇺🇿 **Localization**: Complete Uzbek language support

## Development

### Adding New Features

1. Create handler in appropriate module (`handlers/`)
2. Register router in `main.py`
3. Add database queries if needed in `database/queries.py`
4. Update message templates for Uzbek text in `utils/messages.py`
5. Add proper error handling and logging
6. Test with different user scenarios

### Testing

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python main.py

# Test database connection
python -c "from database.connection import db_manager; import asyncio; asyncio.run(db_manager.connect())"

# Test ChatGPT connection
python -c "from services.chatgpt import chatgpt_service; import asyncio; print(asyncio.run(chatgpt_service.test_connection()))"
```

### Project Structure Explanation

```
chatbot-7/
├── main.py                    # Application entry point and bot initialization
├── config.py                 # Configuration management and environment variables
├── requirements.txt          # Python dependencies
├── setup_database.sql        # Complete database setup script
├── .env                      # Environment variables (not in git)
├── database/                 # Database layer
│   ├── models.py            # Data models, schemas, and CREATE_TABLES_SQL
│   ├── connection.py        # Connection pooling and schema initialization
│   └── queries.py           # All database operations and queries
├── handlers/                # Telegram event handlers
│   ├── admin.py            # Admin commands (/status, /set_required_users)
│   ├── user.py             # User messages and ChatGPT integration
│   ├── member.py           # Member join/leave events
│   └── callback.py         # Button click callbacks
├── services/               # Business logic services
│   ├── chatgpt.py         # OpenAI API integration with history
│   └── user_tracker.py    # User restriction and invite tracking
├── utils/                  # Utility functions
│   ├── messages.py        # Uzbek message templates and constants
│   └── helpers.py         # Helper functions (formatting, admin checks)
└── logs/                   # Application logs (auto-created)
```

## Deployment Checklist

### Pre-Deployment
- [ ] PostgreSQL installed and running on server
- [ ] Valid Telegram Bot Token obtained from @BotFather
- [ ] OpenAI API Key with sufficient credits
- [ ] ChatGPT Assistant created and ID obtained
- [ ] Bot added to target group with admin permissions

### Server Setup
- [ ] Python 3.8+ installed
- [ ] All project files copied (excluding `__pycache__`, `logs`)
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Database created: `psql -U postgres -f setup_database.sql`
- [ ] Environment variables configured in `.env`
- [ ] Network connectivity tested (internet access required)

### Post-Deployment Testing
- [ ] Bot starts without errors: `python main.py`
- [ ] Database connection successful
- [ ] ChatGPT API connectivity working
- [ ] Admin commands responding: `/status`, `/help`
- [ ] User restriction flow working
- [ ] Welcome messages sent correctly
- [ ] Invite tracking functional

### Monitoring
- [ ] Log files rotating properly in `logs/` directory
- [ ] Database performance acceptable
- [ ] API rate limits not exceeded
- [ ] Memory usage within acceptable limits

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the logs for error details
2. Review this documentation
3. Create an issue with detailed information