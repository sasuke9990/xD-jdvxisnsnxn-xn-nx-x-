import sqlite3
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import asyncio

# Bot configuration
BOT_TOKEN = "8430813277:AAFQSJe7q2hsbTuSLGGMs79niI0dQV4K44E"
API_URL = "https://ox.taitaninfo.workers.dev/?mobile="
ADMIN_USER_ID = "8295606531"
ADMIN_USERNAME = "@ah_Saske"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SIMPLE CREDIT SYSTEM
def init_db():
    conn = sqlite3.connect('credits.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  username TEXT,
                  credits INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def get_credits(user_id):
    try:
        conn = sqlite3.connect('credits.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT credits FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"❌ Error getting credits: {e}")
        return 0

def set_credits(user_id, username, credits):
    try:
        conn = sqlite3.connect('credits.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO users (user_id, username, credits) 
                     VALUES (?, ?, ?)''', (user_id, username, credits))
        conn.commit()
        conn.close()
        print(f"✅ Credits set: {user_id} = {credits}")
        return True
    except Exception as e:
        print(f"❌ Error setting credits: {e}")
        return False

# AUTO CREATE USER WITH USERNAME
def create_user_if_not_exists(user_id, username):
    try:
        conn = sqlite3.connect('credits.db', check_same_thread=False)
        c = conn.cursor()
        
        # Check if user exists
        c.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        if not c.fetchone():
            # Create new user
            c.execute('INSERT INTO users (user_id, username, credits) VALUES (?, ?, 0)', 
                     (user_id, username))
            conn.commit()
            print(f"✅ New user created: {user_id} (@{username})")
        else:
            # Update username if changed
            c.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
            conn.commit()
            print(f"✅ Username updated: {user_id} = @{username}")
            
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

# FIND USER BY USERNAME
def find_user_by_username(username):
    try:
        conn = sqlite3.connect('credits.db', check_same_thread=False)
        c = conn.cursor()
        
        # Remove @ if present
        clean_username = username.replace('@', '')
        
        # Search for user
        c.execute('SELECT user_id, credits FROM users WHERE username = ?', (clean_username,))
        result = c.fetchone()
        conn.close()
        
        if result:
            print(f"✅ User found: @{clean_username} = {result[0]}")
            return result[0], result[1]  # user_id, credits
        else:
            print(f"❌ User not found: @{clean_username}")
            return None, 0
            
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        return None, 0

# API function
def get_number_info(number):
    try:
        if number == "7052500819":
            return "special_number"
        response = requests.get(f"{API_URL}{number}", timeout=10)
        return response.json() if response.status_code == 200 else {"error": "API failed"}
    except Exception as e:
        return {"error": str(e)}

def format_number_info(data, number):
    if data == "special_number":
        return "❌ Beta jis thali me khata ussi mei ched krta 🤡"
    
    if isinstance(data, dict) and "error" in data:
        return f"❌ Error: {data['error']}"
    
    if not isinstance(data, dict) or "data" not in data:
        return "❌ No data found"
    
    records = data["data"]
    if not records:
        return "❌ No records found"
    
    message = f"🔍 Akatsuki Finds - Mobile Info: {number}\n"
    message += f"📊 Total Records Found: {len(records)}\n\n"
    
    for i, record in enumerate(records, 1):
        message += f"➖ Source {i} Results:\n────────────────────\n"
        message += f"📋 Record 1:\n"
        message += f"👤 Name: {record.get('name', 'N/A')}\n"
        message += f"📞 Mobile: {record.get('mobile', 'N/A')}\n"
        message += f"👨‍👧 Father: {record.get('fname', 'N/A')}\n"
        message += f"🏠 Address: {record.get('address', 'N/A').replace('!', ' ')}\n"
        message += f"📱 Alt Mobile: {record.get('alt', 'N/A')}\n"
        message += f"📡 Circle: {record.get('circle', 'N/A')}\n"
        message += f"🆔 Aadhar: {record.get('id', 'N/A')}\n\n"
    
    message += "────────────────────\n"
    message += f"👑 Admin: {ADMIN_USERNAME}\n"
    message += "💔 Contact admin for credits"
    return message

# BOT COMMANDS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    print(f"🚀 Start command: {user_id} (@{username})")
    
    # CREATE USER IF NOT EXISTS
    create_user_if_not_exists(user_id, username)
    
    if str(user_id) == ADMIN_USER_ID:
        set_credits(user_id, username, 999999)
        await update.message.reply_text(
            f"👑 Welcome Admin {ADMIN_USERNAME}!\n\n"
            f"Credits: Unlimited\n"
            f"Use /give @username credits to give credits"
        )
    else:
        credits = get_credits(user_id)
        await update.message.reply_text(
            f"🔍 Welcome to Akatsuki Finds\n\n"
            f"Your credits: {credits}\n"
            f"Use /num <number> to search (1 credit)\n\n"
            f"Contact {ADMIN_USERNAME} for credits"
        )

async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    print(f"🔍 Num command: {user_id} (@{username})")
    
    # Ensure user exists
    create_user_if_not_exists(user_id, username)
    
    # CHECK CREDITS
    if str(user_id) != ADMIN_USER_ID:
        credits = get_credits(user_id)
        print(f"💰 User credits: {credits}")
        if credits < 1:
            await update.message.reply_text(f"❌ 0 credits! Contact {ADMIN_USERNAME}")
            return
        # DEDUCT CREDIT IMMEDIATELY
        set_credits(user_id, username, credits - 1)
        print(f"💰 Credit deducted: {credits} -> {credits-1}")
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /num <number>")
        return
    
    number = context.args[0]
    if not number.isdigit() or len(number) < 10:
        await update.message.reply_text("❌ Invalid number")
        return
    
    msg = await update.message.reply_text("🔍 Searching...")
    info = get_number_info(number)
    result = format_number_info(info, number)
    
    if str(user_id) != ADMIN_USER_ID:
        remaining = get_credits(user_id)
        result += f"\n\n💎 Remaining Credits: {remaining}"
    
    await msg.edit_text(result)

async def credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    print(f"💰 Credits command: {user_id} (@{username})")
    
    create_user_if_not_exists(user_id, username)
    credits = get_credits(user_id)
    
    if str(user_id) == ADMIN_USER_ID:
        await update.message.reply_text("👑 Admin - Unlimited credits")
    else:
        await update.message.reply_text(f"💎 Your credits: {credits}")

async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"🎁 Give command from: {user_id}")
    
    if str(user_id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /give @username credits")
        return
    
    target_username = context.args[0]
    try:
        credits = int(context.args[1])
    except:
        await update.message.reply_text("❌ Invalid credits")
        return
    
    print(f"🎁 Giving {credits} credits to: {target_username}")
    
    # FIND USER BY USERNAME
    target_user_id, current_credits = find_user_by_username(target_username)
    
    if target_user_id:
        # User found - give credits
        new_credits = current_credits + credits
        set_credits(target_user_id, target_username.replace('@', ''), new_credits)
        
        await update.message.reply_text(
            f"✅ Success!\n"
            f"Given {credits} credits to @{target_username}\n"
            f"Old balance: {current_credits}\n"
            f"New balance: {new_credits}"
        )
    else:
        # User not found
        await update.message.reply_text(
            f"❌ User @{target_username} not found in database!\n\n"
            f"Tell them to:\n"
            f"1. Search @Sasukeinfo_bot\n"
            f"2. Click START button\n"
            f"3. Then you can give credits\n\n"
            f"User MUST start the bot first!"
        )

async def take_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /take @username credits")
        return
    
    target_username = context.args[0]
    try:
        credits = int(context.args[1])
    except:
        await update.message.reply_text("❌ Invalid credits")
        return
    
    target_user_id, current_credits = find_user_by_username(target_username)
    
    if not target_user_id:
        await update.message.reply_text(f"❌ User @{target_username} not found!")
        return
    
    credits_to_take = min(credits, current_credits)
    new_balance = current_credits - credits_to_take
    set_credits(target_user_id, target_username.replace('@', ''), new_balance)
    
    await update.message.reply_text(
        f"✅ Took {credits_to_take} credits from @{target_username}\n"
        f"Old balance: {current_credits}\n"
        f"New balance: {new_balance}"
    )

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    try:
        conn = sqlite3.connect('credits.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT username, credits FROM users WHERE user_id != ? ORDER BY credits DESC', (ADMIN_USER_ID,))
        users = c.fetchall()
        conn.close()
        
        if not users:
            await update.message.reply_text("📝 No users found")
            return
        
        message = "📊 All Users:\n\n"
        for username, credits in users:
            message += f"@{username}: {credits} credits\n"
        
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    init_db()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("num", num_command))
    app.add_handler(CommandHandler("credits", credits_command))
    app.add_handler(CommandHandler("give", give_command))
    app.add_handler(CommandHandler("take", take_command))
    app.add_handler(CommandHandler("users", users_command))
    
    print("🤖 Bot starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
