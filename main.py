from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import sqlite3
import os

api_id = 1234567  # চাইলে চেঞ্জ করিস
api_hash = "your_api_hash"  # এটা দরকার নাই Render এ, শুধু লোকালে টেস্ট করলে
bot_token = "7742252147:AAEiIlrK_P2kw7_QJJcCw-iv3kMx4WYBcP4"

app = Client("EarnTaskBD", bot_token=bot_token)

# Database setup
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, referrals INTEGER DEFAULT 0, ads_watched INTEGER DEFAULT 0)''')
conn.commit()

def get_user(user_id):
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row:
        return {"balance": row[1], "referrals": row[2], "ads_watched": row[3]}
    else:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return {"balance": 0, "referrals": 0, "ads_watched": 0}

def update_user(user_id, balance=None, referrals=None, ads=None):
    user = get_user(user_id)
    c.execute("UPDATE users SET balance=?, referrals=?, ads_watched=? WHERE user_id=?", 
              (balance if balance is not None else user["balance"],
               referrals if referrals is not None else user["referrals"],
               ads if ads is not None else user["ads_watched"],
               user_id))
    conn.commit()

@app.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id
    args = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    if args and args.startswith("ref_"):
        ref_id = int(args.split("_")[1])
        if ref_id != user_id:
            user = get_user(ref_id)
            update_user(ref_id, balance=user["balance"] + 50, referrals=user["referrals"] + 1)
            update_user(user_id, balance=50)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 ব্যালেন্স চেক", callback_data="balance"),
         InlineKeyboardButton("👥 রেফার করুন", callback_data="refer")],
        [InlineKeyboardButton("📺 টাস্ক করুন", callback_data="task"),
         InlineKeyboardButton("💸 উইথড্র", callback_data="withdraw")],
        [InlineKeyboardButton("🎁 প্রোফাইল", callback_data="profile"),
         InlineKeyboardButton("ℹ️ টিউটোরিয়াল", callback_data="tutorial")]
    ])

    message.reply_text(
        "🔥 স্বাগতম! 🔥\n\n"
        "আসসালামু আলাইকুম, সবাইকে পেমেন্ট করছি\n"
        "নিয়ম মেনে কাজ করলে ১০০% পেমেন্ট পাবেন ইনশাআল্লাহ 🔥\n\n"
        "⚡️ জয়েন বোনাস: ৫০ টাকা\n"
        "👑 প্রতি রেফার: ৫০ টাকা\n"
        "💎 প্রতি বিজ্ঞাপন: ২০ টাকা\n"
        "❤️ প্রতিদিন ১০ টা করে বিজ্ঞাপন দেখার সুযোগ\n\n"
        "এই সাইটে কোন ইনভেস্ট করতে হবে না সম্পূর্ণ ফ্রি\n"
        "ধন্যবাদ! ✅ ১০০% পেমেন্ট গ্যারান্টি",
        reply_markup=keyboard
    )

@app.on_callback_query()
def callback_handler(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    user = get_user(user_id)

    if data == "balance":
        query.message.edit_text(
            f"💰 আপনার ব্যালেন্স\n\n৳ {user['balance']:.2f} BDT",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]])
        )

    elif data == "refer":
        ref_link = f"https://t.me/{app.get_me().username}?start=ref_{user_id}"
        query.message.edit_text(
            f"👥 রেফার করুন এবং আয় করুন\n\n"
            f"প্রতি রেফারে ৫০.০০ টাকা বোনাস\n\n"
            f"আপনার রেফার লিংক:\n{ref_link}\n\n"
            f"মোট রেফার: {user['referrals']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 লিংক কপি করুন", url=f"https://t.me/share/url?url={ref_link}")],
                [InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]
            ])
        )

    elif data == "task":
        if user['ads_watched'] >= 50:
            text = "❌ আজকের সব টাস্ক শেষ! আগামীকাল আসো ❤️"
        else:
            text = "📺 বিজ্ঞাপন দেখুন\n\nপ্রতি বিজ্ঞাপন দেখলে ২০.০০ BDT আয় করুন\n\n"
            text += f"আজ দেখেছো: {user['ads_watched']}/50"
        query.message.edit_text(text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁️ বিজ্ঞাপন দেখুন", callback_data="watch_ad")],
                [InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]
            ]))

    elif data == "watch_ad":
        if user['ads_watched'] >= 50:
            query.answer("আজকের লিমিট শেষ!", show_alert=True)
        else:
            update_user(user_id, balance=user["balance"] + 20, ads=user['ads_watched'] + 1)
            query.answer("+২০ টাকা যোগ হয়েছে! 💸", show_alert=True)
            callback_handler(client, query)  # রিফ্রেশ

    elif data == "withdraw":
        query.message.edit_text(
            "💸 টাকা উইথড্র\n\n"
            "ন্যূনতম উইথড্র: ৫০০০.০০ BDT\n"
            "ন্যূনতম রেফারের প্রয়োজন: ২০ জন\n\n"
            "পেমেন্ট মেথড নির্বাচন করুন",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("বিকাশ", callback_data="bkash")],
                [InlineKeyboardButton("নগদ", callback_data="nagad")],
                [InlineKeyboardButton("রকেট", callback_data="rocket")],
                [InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]
            ])
        )

    elif data in ["bkash", "nagad", "rocket"]:
        query.answer("এডমিনের সাথে যোগাযোগ করুন: @YourAdminUsername", show_alert=True)

    elif data == "profile":
        query.message.edit_text(
            f"👤 প্রোফাইল\n\n"
            f"নাম: {query.from_user.first_name}\n"
            f"ব্যালেন্স: ৳ {user['balance']:.2f} BDT\n"
            f"মোট রেফার: {user['referrals']}\n"
            f"আজকের টাস্ক: {user['ads_watched']}/50",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]])
        )

    elif data == "tutorial":
        query.message.edit_text(
            "🎥 টিউটোরিয়াল ভিডিও\n\n"
            "কিভাবে আয় করবেন - টিউটোরিয়াল ভিডিও দেখে নিন এবং সহজেই আয় শুরু করুন।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ ভিডিও দেখুন", url="https://youtu.be/example")],
                [InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]
            ])
        )

    elif data == "back":
        # রিফ্রেশ মেইন মেনু
        query.message.delete()
        start(client, query.message)

app.run()
