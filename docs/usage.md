راهنمای استفاده از Baleh
شروع سریع
برای ساخت یک ربات ساده، کد زیر را اجرا کنید:

python

کپی
from baleh import BaleClient
import asyncio

async def handle_message(message):
    await message.reply_text(f"دریافت شد: {message.text}")

async def main():
    client = BaleClient("YOUR_BLE_TOKEN")
    client.on_message()(handle_message)
    await client.connect()
    await client.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
ویژگی‌ها
ارسال پیام، عکس، ویدیو، و فایل
زمان‌بندی پیام‌ها با schedule_message
مدیریت چت و اعضای آن با get_chat_member
لاگینگ داخلی برای دیباگ
مثال پیشرفته
زمان‌بندی یک پیام بعد از 10 ثانیه:

python

کپی
client.schedule_message(123456789, "پیام زمان‌بندی‌شده", 10)
نکات
توکن ربات را از بله دریافت کنید.
برای استفاده از پروکسی، در زمان ایجاد BaleClient مشخص کنید:
python

کپی
client = BaleClient("YOUR_BLE_TOKEN", proxy="http://proxy:port")