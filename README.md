# Telegram-Broadcast-Bot

📢 Telegram-Broadcast-Bot

Telegram-Broadcast-Bot v1.0.0

A professional Telegram administration bot built with Python and "python-telegram-bot", designed for controlled message broadcasting to groups where the bot is already a member and has permission to send messages.

The project focuses on reliable group management, message preview, controlled broadcasting, detailed reporting, error handling, and JSON-based data persistence.

---

✨ Features

- 📢 Broadcast text messages to registered groups
- 👥 Automatic group registration when the bot joins a group
- 🗑 Automatic removal when the bot leaves or is removed
- 🟢 Enable / disable individual groups
- 📋 View registered groups
- 📊 Group statistics
- 🔄 Update group information from Telegram
- 📝 Preserve multiline text, whitespace, empty lines, Emoji, and Unicode
- 📋 Message preview before broadcasting
- ✂️ Split messages longer than Telegram's message limit
- ✅ Track successful deliveries
- ❌ Track failed deliveries and errors
- 📊 Detailed broadcast reports
- 🆔 Unique report IDs
- 🔐 Admin-only control panel
- 🛡 Global error handling
- 📝 Structured application logging
- 💾 JSON-based persistent storage
- ⚡ Fully asynchronous Telegram API operations
- 🧩 Modular and maintainable project structure

---

🏗️ Project Structure

Telegram-Broadcast-Bot/
│
├── main.py
├── config.py
├── requirements.txt
│
├── data/
│   ├── groups.json
│   └── reports.json
│
└── bot/
    ├── __init__.py
    ├── storage.py
    └── reports.py

---

⚙️ Requirements

- Python 3
- "python-telegram-bot==22.8"
- Telegram Bot API

---

📦 Installation

Clone the repository:

git clone https://github.com/YOUR_USERNAME/Telegram-Broadcast-Bot.git
cd Telegram-Broadcast-Bot

Install dependencies:

py -m pip install -r requirements.txt

---

🔧 Configuration

Open "config.py" and configure your bot:

BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789

🔐 Security

Never publish your real bot token on GitHub.

It is recommended to keep your token outside the public repository or use environment variables in production.

---

▶️ Run

Start the bot with:

py main.py

---

🖥️ Admin Panel

After sending "/start", the authorized administrator will receive:

📢 ارسال پیام
👥 مدیریت گروه‌ها
📊 گزارش‌ها

Only the configured "ADMIN_ID" can access administrative features.

Unauthorized users receive:

⛔ دسترسی ندارید.

---

📢 Broadcasting Flow

📢 Send Message
       ↓
Receive Message
       ↓
Preview
       ↓
Confirm
       ↓
Get Active Groups
       ↓
Broadcast
       ↓
Success / Failed
       ↓
Create Report
       ↓
Show Final Result

Each group is processed independently, so an error in one group does not stop the broadcast to the remaining groups.

---

👥 Group Management

The bot automatically maintains its internal group list.

Available operations include:

- 📋 List groups
- 📊 Group statistics
- 🔄 Update group information
- 🟢 Enable group
- 🔴 Disable group
- 🔄 Update group name
- 🗑 Remove group
- ⚠️ Two-step deletion confirmation

Example group record:

{
    "chat_id": "-1001234567890",
    "title": "Example Group",
    "active": true
}

---

📊 Reporting

Every broadcast operation generates a report containing information such as:

{
    "id": 1,
    "time": "2026-09-09 22:00:00",
    "message_length": 120,
    "total_groups": 10,
    "success": 8,
    "failed": 2,
    "message": "Example message",
    "results": []
}

Each group result is recorded separately:

{
    "chat_id": "-1001234567890",
    "title": "Example Group",
    "status": "success"
}

Failed operations include the associated error:

{
    "chat_id": "-1001234567890",
    "title": "Example Group",
    "status": "failed",
    "error": "Telegram API error"
}

---

📝 Message Handling

The bot is designed to preserve the original structure of administrator messages.

Supported content includes:

- Multiline text
- Empty lines
- Whitespace
- Emoji
- Unicode characters
- Long text

The original message is not processed with operations such as "strip()" or "split()" that could unintentionally alter its structure.

Messages exceeding the configured size limit are divided into smaller parts while preserving the original content as much as practical.

---

🛡️ Error Handling

The project includes centralized error handling and logging.

A failure in one group does not terminate the entire broadcast process:

Group A → ✅ Success
Group B → ❌ Failed
Group C → ✅ Success

The bot continues processing the remaining groups and records the final results in the report system.

---

🔐 Security

The project follows several security principles:

- Admin-only control
- Protected bot token
- Admin-only callback processing
- No sensitive credentials in reports
- Telegram API errors are handled safely
- No broadcasting outside registered groups
- No attempts to bypass Telegram restrictions

The bot only broadcasts to groups where it is already a member and has permission to send messages.

---

💾 Data Storage

The project uses JSON files for persistent storage:

data/
├── groups.json
└── reports.json

Both files are created automatically if they do not exist.

Data writes use temporary files before replacement to reduce the risk of corrupting JSON files during write operations.

---

📝 Logging

Important events are recorded using Python's built-in "logging" module.

Logged events include:

- Bot startup
- Group registration
- Group removal
- Group information errors
- Broadcast errors
- Unexpected exceptions

---

⚡ Async Architecture

Telegram API operations are implemented using Python's asynchronous programming model.

The project uses:

async / await

for Telegram operations and includes a reasonable delay between broadcast operations to avoid unnecessarily aggressive API requests.

---

🚫 Scope & Limitations

This project intentionally does not provide functionality for:

- Finding random groups
- Automatically joining unknown groups
- Sending messages to groups where the bot is not a member
- Bypassing Telegram restrictions
- Hiding broadcast activity
- Sending unsolicited messages outside the bot's authorized groups

The system is designed specifically for controlled broadcasting within groups managed by the bot.

---

📄 License

This project is provided for educational and development purposes.

If you plan to redistribute or commercially use this source, make sure your usage complies with Telegram's terms and the license included with this repository.

---

📌 Version

Telegram-Broadcast-Bot v1.0.0

Built with:

- Python 3
- python-telegram-bot 22.8
- Telegram Bot API
- JSON
- Async/Await

---

⭐ Support

If you find this project useful, consider giving the repository a ⭐.
