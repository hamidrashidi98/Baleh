مرجع API کتابخونه Baleh
کلاس BaleClient
متدهای اصلی
__init__(self, token: str, proxy: Optional[str] = None, timeout: int = 30)
ایجاد کلاینت با توکن، پروکسی، و زمان‌بندی.
async connect(self)
اتصال به API بله.
async disconnect(self)
قطع اتصال از API.
async send_message(self, chat_id: int, text: str, parse_mode: Optional[str] = None) -> Message
ارسال پیام متنی.
async send_photo(self, chat_id: int, photo: str, caption: Optional[str] = None) -> Message
ارسال عکس با کپشن.
async send_video(self, chat_id: int, video: str, caption: Optional[str] = None, duration: Optional[int] = None) -> Message
ارسال ویدیو با کپشن و مدت زمان.
async send_document(self, chat_id: int, document: str, caption: Optional[str] = None) -> Message
ارسال فایل با کپشن.
async send_voice(self, chat_id: int, voice: str, caption: Optional[str] = None) -> Message
ارسال صوت با کپشن.
async send_sticker(self, chat_id: int, sticker: str) -> Message
ارسال استیکر.
async reply_text(self, chat_id: int, text: str) -> Message
پاسخ به پیام.
def on_message(self)
دکوراتور برای هندل کردن پیام‌ها.
async start_polling(self, allowed_updates: Optional[List[str]] = None)
شروع پولینگ با فیلتر آپدیت‌ها.
def schedule_message(self, chat_id: int, text: str, delay_seconds: int)
زمان‌بندی ارسال پیام.
async get_chat_member(self, chat_id: int, user_id: int) -> dict
دریافت اطلاعات عضویت کاربر.
def stop_polling(self)
توقف پولینگ.
اشیا
Message: شامل message_id, chat, text, author.
Chat: شامل id, type.
User: شامل id, username, first_name.
نکات توسعه
همه متدهای ارسال از لاگینگ داخلی استفاده می‌کنن.
زمان‌بندی پیام‌ها با scheduled_tasks مدیریت می‌شه.