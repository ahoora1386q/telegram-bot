from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging
import os

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# دریافت توکن از متغیر محیطی
BOT_TOKEN = os.getenv('BOT_TOKEN', "7799335334:AAHUf7tDDF81lBxXctxqAcVCfOeuOJNSXaI")
ADMIN_CHAT_ID = 6444593264

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('سلام! به بات پشتیبانی خوش آمدید. پیام خود را ارسال کنید.')

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندل کردن پیامهای کاربران و فوروارد به ادمین"""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "بدون یوزرنیم"
    first_name = update.message.from_user.first_name or "بدون نام"
    last_name = update.message.from_user.last_name or "بدون نام خانوادگی"
    
    # اطلاعات کاربر
    user_info = f"👤 پیام جدید از کاربر:\n"
    user_info += f"🆔 آیدی: {user_id}\n"
    user_info += f"👤 یوزرنیم: @{username}\n"
    user_info += f"📛 نام: {first_name} {last_name}"
    
    # ایجاد دکمه پاسخ
    keyboard = [
        [InlineKeyboardButton("📝 پاسخ به این کاربر", callback_data=f"reply_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # فوروارد پیام اصلی به ادمین
        forwarded_msg = await update.message.forward(ADMIN_CHAT_ID)
        
        # ارسال اطلاعات کاربر با دکمه پاسخ
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=user_info,
            reply_to_message_id=forwarded_msg.message_id,
            reply_markup=reply_markup
        )
        
        # تأیید دریافت پیام به کاربر
        await update.message.reply_text("✅ پیام شما ارسال شد.")
        
    except Exception as e:
        print(f"خطا در فوروارد پیام: {e}")
        await update.message.reply_text("❌ خطا در ارسال پیام. لطفاً مجدد تلاش کنید.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندل کردن کلیک روی دکمه پاسخ"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("reply_"):
        target_user_id = data.split("_")[1]
        
        # ذخیره اطلاعات برای پاسخ
        context.user_data['waiting_for_reply'] = True
        context.user_data['target_user_id'] = target_user_id
        
        await query.edit_message_text(
            text=f"🎯 در حال پاسخ به کاربر:\nآیدی: {target_user_id}\n\nلطفاً پیام پاسخ خود را ارسال کنید:"
        )

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندل کردن پاسخ ادمین"""
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    
    if context.user_data.get('waiting_for_reply'):
        target_user_id = context.user_data.get('target_user_id')
        admin_message = update.message.text
        
        if target_user_id and admin_message:
            try:
                # ارسال پیام به کاربر
                await context.bot.send_message(
                    chat_id=int(target_user_id),
                    text=f"📨 پاسخ:\n\n{admin_message}"
                )
                
                await update.message.reply_text(
                    f"✅ پاسخ شما با موفقیت ارسال شد!",
                    reply_to_message_id=update.message.message_id
                )
                
                # پاک کردن وضعیت پاسخ
                context.user_data['waiting_for_reply'] = False
                context.user_data['target_user_id'] = None
                
            except Exception as e:
                error_msg = f"❌ خطا در ارسال پاسخ: {e}"
                await update.message.reply_text(error_msg)
                print(error_msg)

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندل کردن پیامهای معمولی ادمین"""
    if update.effective_chat.id == ADMIN_CHAT_ID and not context.user_data.get('waiting_for_reply'):
        await update.message.reply_text(
            "💡 برای پاسخ به کاربر، روی دکمه '📝 پاسخ به این کاربر' در زیر پیام کاربر کلیک کنید."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور help"""
    if update.effective_chat.id == ADMIN_CHAT_ID:
        help_text = """
🤖 دستورات بات:
• برای پاسخ به کاربر: روی دکمه "📝 پاسخ به این کاربر" کلیک کنید
• سپس پیام پاسخ خود را تایپ کنید
• تمام پیامهای کاربران به صورت خودکار فوروارد می‌شوند
        """
        await update.message.reply_text(help_text)
    else:
        await update.message.reply_text("برای ارتباط با پشتیبانی، پیام خود را ارسال کنید.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Chat(ADMIN_CHAT_ID), 
        handle_user_message
    ))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Chat(ADMIN_CHAT_ID),
        handle_admin_reply
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Chat(ADMIN_CHAT_ID),
        handle_admin_message
    ))
    
    # اجرای بات روی سرور
    print("🤖 Bot is running on Railway...")
    application.run_polling()

if __name__ == '__main__':
    main()
