import aiohttp
import asyncio
import logging
import time
import json
import os
import subprocess
from typing import Optional, Callable, Any, List
from .objects.chat import Chat
from .objects.message import Message
from .utils import helpers
from PIL import Image  # اضافه کردن Pillow

# تنظیم لاگ داخلی
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class BaleClient:
    def __init__(self, token: str, proxy: Optional[str] = None, timeout: int = 30):
        """ایجاد کلاینت با توکن، پروکسی، و زمان‌بندی"""
        self.token = token
        self.base_url = f"https://tapi.bale.ai/bot{token}"
        self.proxy = proxy
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.handlers: List[Callable] = []
        self.is_running = False
        self.last_update_id = 0
        self.scheduled_tasks: List[dict] = []  # برای زمان‌بندی پیام‌ها

    async def connect(self):
        """اتصال به API بله با تنظیمات پروکسی و لاگ"""
        if not self.session:
            try:
                connector = aiohttp.TCPConnector(verify_ssl=True)
                self.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    proxy=self.proxy
                )
                logger.info("اتصال به API بله با موفقیت برقرار شد.")
            except Exception as e:
                logger.error(f"خطا در اتصال به API: {str(e)}")
                raise
        return self

    async def disconnect(self):
        """قطع اتصال با مدیریت صحیح منابع"""
        if self.session:
            await self.session.close()
            self.session = None
            self.is_running = False
            logger.info("اتصال به API بله قطع شد.")
        for task in self.scheduled_tasks:
            task["task"].cancel()

    async def send_message(self, chat_id: int, text: str, parse_mode: Optional[str] = None, reply_markup: Optional[dict] = None) -> Message:
        """ارسال پیام متنی با پارامترهای پیشرفته"""
        if not self.session:
            await self.connect()
        data = {"chat_id": chat_id, "text": helpers.format_message(text)}
        if parse_mode:
            data["parse_mode"] = parse_mode
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        try:
            async with self.session.post(
                f"{self.base_url}/sendMessage",
                json=data
            ) as resp:
                data = await helpers.handle_response(resp)
                if data and data.get("ok"):
                    result = data["result"]
                    chat = Chat(id=result.get("chat", {}).get("id"), type="unknown")
                    message = Message(
                        message_id=result.get("message_id"),
                        chat=chat,
                        date=result.get("date", 0),
                        text=result.get("text"),
                        from_user=result.get("from", {})
                    )
                    logger.info(f"پیام به {chat_id} ارسال شد: {text}")
                    return message
                raise Exception(f"Error sending message: {data.get('description', 'Unknown error')}")
        except Exception as e:
            logger.error(f"خطا در ارسال پیام: {str(e)}")
            raise

    async def send_photo(self, chat_id: int, photo: str, caption: Optional[str] = None) -> Message:
        """ارسال عکس با کپشن"""
        if not self.session:
            await self.connect()
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        with open(photo, "rb") as f:
            file_content = f.read()
        form.add_field("photo", file_content, filename=photo.split("/")[-1])
        if caption:
            form.add_field("caption", caption)
        try:
            async with self.session.post(
                f"{self.base_url}/sendPhoto",
                data=form
            ) as resp:
                data = await helpers.handle_response(resp)
                if data and data.get("ok"):
                    result = data["result"]
                    chat = Chat(id=result.get("chat", {}).get("id"), type="unknown")
                    message = Message(
                        message_id=result.get("message_id"),
                        chat=chat,
                        date=result.get("date", 0),
                        caption=result.get("caption"),
                        from_user=result.get("from", {})
                    )
                    logger.info(f"عکس به {chat_id} ارسال شد")
                    return message
                raise Exception(f"Error sending photo: {data.get('description', 'Unknown error')}")
        except Exception as e:
            logger.error(f"خطا در ارسال عکس: {str(e)}")
            raise

    async def send_video(self, chat_id: int, video: str, caption: Optional[str] = None, duration: Optional[int] = None) -> Message:
        """ارسال ویدیو با کپشن و مدت زمان"""
        logger.info(f"در حال ارسال ویدیو به {chat_id} - مسیر فایل: {video}")
        if not self.session:
            await self.connect()
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        with open(video, "rb") as f:
            file_content = f.read()
        form.add_field("video", file_content, filename=video.split("/")[-1])
        if caption:
            form.add_field("caption", caption)
        if duration:
            form.add_field("duration", str(duration))
        try:
            async with self.session.post(
                f"{self.base_url}/sendVideo",
                data=form
            ) as resp:
                data = await helpers.handle_response(resp)
                if data and data.get("ok"):
                    result = data["result"]
                    chat = Chat(id=result.get("chat", {}).get("id"), type="unknown")
                    message = Message(
                        message_id=result.get("message_id"),
                        chat=chat,
                        date=result.get("date", 0),
                        caption=result.get("caption"),
                        from_user=result.get("from", {})
                    )
                    logger.info(f"ویدیو با موفقیت به {chat_id} ارسال شد")
                    return message
                logger.error(f"خطا در ارسال ویدیو: پاسخ API: {data}")
                raise Exception(f"Error sending video: {data.get('description', 'Unknown error')}")
        except Exception as e:
            logger.error(f"خطا در ارسال ویدیو: {str(e)}")
            raise

    async def send_voice(self, chat_id: int, voice: str, caption: Optional[str] = None) -> Message:
        """ارسال صوت با کپشن"""
        if not self.session:
            await self.connect()
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        with open(voice, "rb") as f:
            file_content = f.read()
        form.add_field("voice", file_content, filename=voice.split("/")[-1])
        if caption:
            form.add_field("caption", caption)
        try:
            async with self.session.post(
                f"{self.base_url}/sendVoice",
                data=form
            ) as resp:
                data = await helpers.handle_response(resp)
                if data and data.get("ok"):
                    result = data["result"]
                    chat = Chat(id=result.get("chat", {}).get("id"), type="unknown")
                    message = Message(
                        message_id=result.get("message_id"),
                        chat=chat,
                        date=result.get("date", 0),
                        caption=result.get("caption"),
                        from_user=result.get("from", {})
                    )
                    logger.info(f"صوت به {chat_id} ارسال شد")
                    return message
                raise Exception(f"Error sending voice: {data.get('description', 'Unknown error')}")
        except Exception as e:
            logger.error(f"خطا در ارسال صوت: {str(e)}")
            raise

    async def send_audio(self, chat_id: int, audio: str, caption: Optional[str] = None, duration: Optional[int] = None) -> Message:
        """ارسال صدا با کیفیت بالا (مثل موسیقی)"""
        if not self.session:
            await self.connect()
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        with open(audio, "rb") as f:
            file_content = f.read()
        form.add_field("audio", file_content, filename=audio.split("/")[-1])
        if caption:
            form.add_field("caption", caption)
        if duration:
            form.add_field("duration", str(duration))
        try:
            async with self.session.post(
                f"{self.base_url}/sendAudio",
                data=form
            ) as resp:
                data = await helpers.handle_response(resp)
                if data and data.get("ok"):
                    result = data["result"]
                    chat = Chat(id=result.get("chat", {}).get("id"), type="unknown")
                    message = Message(
                        message_id=result.get("message_id"),
                        chat=chat,
                        date=result.get("date", 0),
                        caption=result.get("caption"),
                        from_user=result.get("from", {})
                    )
                    logger.info(f"صدا با کیفیت بالا به {chat_id} ارسال شد")
                    return message
                raise Exception(f"Error sending audio: {data.get('description', 'Unknown error')}")
        except Exception as e:
            logger.error(f"خطا در ارسال صدا: {str(e)}")
            raise

    async def send_animation(self, chat_id: int, animation: str, caption: Optional[str] = None) -> Message:
        """ارسال انیمیشن (پشتیبانی از GIF، WebM، و تبدیل TGS به WebM)"""
        if not self.session:
            await self.connect()
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        
        # بررسی فرمت فایل و تبدیل TGS به WebM اگر لازم باشه
        file_extension = animation.lower().split(".")[-1]
        temp_webm_path = None
        if file_extension == "tgs":
            temp_webm_path = animation.replace(".tgs", "_temp.webm")
            try:
                subprocess.run(
                    ["ffmpeg", "-i", animation, "-c:v", "libvpx-vp9", "-an", "-s", "512x512", "-r", "30", temp_webm_path],
                    check=True,
                    capture_output=True
                )
                animation = temp_webm_path
                file_extension = "webm"
            except subprocess.CalledProcessError as e:
                logger.error(f"خطا در تبدیل TGS به WebM: {str(e)}")
                raise Exception("تبدیل TGS به WebM ناموفق بود")
        
        with open(animation, "rb") as f:
            file_content = f.read()
        form.add_field("animation", file_content, filename=animation.split("/")[-1])
        if caption:
            form.add_field("caption", caption)
        
        for attempt in range(2):  # دو تلاش
            try:
                async with self.session.post(
                    f"{self.base_url}/sendAnimation",
                    data=form
                ) as resp:
                    data = await helpers.handle_response(resp)
                    if data and data.get("ok"):
                        result = data["result"]
                        chat = Chat(id=result.get("chat", {}).get("id"), type="unknown")
                        message = Message(
                            message_id=result.get("message_id"),
                            chat=chat,
                            date=result.get("date", 0),
                            caption=result.get("caption"),
                            from_user=result.get("from", {})
                        )
                        logger.info(f"انیمیشن به {chat_id} ارسال شد - فرمت: {file_extension}")
                        if temp_webm_path:
                            os.remove(temp_webm_path)  # حذف فایل موقت
                        return message
                    logger.error(f"تلاش {attempt + 1} - خطا: {data.get('description', 'Unknown error')}")
                    if attempt == 0:  # اگه اولین تلاش بود، صبر کن و دوباره تلاش کن
                        await asyncio.sleep(1)
                    else:
                        raise Exception(f"Error sending animation after retries: {data.get('description', 'Unknown error')}")
            except Exception as e:
                logger.error(f"تلاش {attempt + 1} - خطا در ارسال انیمیشن: {str(e)}")
                if attempt == 0:
                    await asyncio.sleep(1)
                else:
                    if temp_webm_path:
                        os.remove(temp_webm_path)  # حذف فایل موقت در صورت خطا
                    raise

    async def send_sticker(self, chat_id: int, sticker: str) -> Message:
        """ارسال استیکر (پشتیبانی از PNG، WebP و GIF)"""
        if not self.session:
            await self.connect()
        
        file_extension = sticker.lower().split(".")[-1]
        if file_extension not in ["png", "webp", "gif"]:
            raise ValueError("فقط فرمت‌های PNG، WebP و GIF برای استیکر پشتیبانی می‌شوند")

        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        with open(sticker, "rb") as f:
            file_content = f.read()
        form.add_field("sticker", file_content, filename=sticker.split("/")[-1])
        
        for attempt in range(2):  # دو تلاش
            try:
                async with self.session.post(
                    f"{self.base_url}/sendSticker",
                    data=form
                ) as resp:
                    data = await helpers.handle_response(resp)
                    if data and data.get("ok"):
                        result = data["result"]
                        chat = Chat(id=result.get("chat", {}).get("id"), type="unknown")
                        message = Message(
                            message_id=result.get("message_id"),
                            chat=chat,
                            date=result.get("date", 0),
                            from_user=result.get("from", {})
                        )
                        logger.info(f"استیکر به {chat_id} ارسال شد - فرمت: {file_extension}")
                        return message
                    logger.error(f"تلاش {attempt + 1} - خطا: {data.get('description', 'Unknown error')}")
                    if attempt == 0:  # اگه اولین تلاش بود، صبر کن و دوباره تلاش کن
                        await asyncio.sleep(1)
                    else:
                        raise Exception(f"Error sending sticker after retries: {data.get('description', 'Unknown error')}")
            except Exception as e:
                logger.error(f"تلاش {attempt + 1} - خطا در ارسال استیکر: {str(e)}")
                if attempt == 0:
                    await asyncio.sleep(1)
                else:
                    raise

    async def send_location(self, chat_id: int, latitude: float, longitude: float) -> Message:
        """ارسال موقعیت مکانی"""
        if not self.session:
            await self.connect()
        data = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude
        }
        try:
            async with self.session.post(
                f"{self.base_url}/sendLocation",
                json=data
            ) as resp:
                data = await helpers.handle_response(resp)
                if data and data.get("ok"):
                    result = data["result"]
                    chat = Chat(id=result.get("chat", {}).get("id"), type="unknown")
                    message = Message(
                        message_id=result.get("message_id"),
                        chat=chat,
                        date=result.get("date", 0),
                        from_user=result.get("from", {})
                    )
                    logger.info(f"موقعیت مکانی به {chat_id} ارسال شد")
                    return message
                raise Exception(f"Error sending location: {data.get('description', 'Unknown error')}")
        except Exception as e:
            logger.error(f"خطا در ارسال موقعیت مکانی: {str(e)}")
            raise

    async def send_video_note(self, chat_id: int, video_note: str, duration: Optional[int] = None) -> Message:
        """ارسال ویدیو دایره‌ای"""
        if not self.session:
            await self.connect()
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        with open(video_note, "rb") as f:
            file_content = f.read()
        form.add_field("video_note", file_content, filename=video_note.split("/")[-1])
        if duration:
            form.add_field("duration", str(duration))
        try:
            async with self.session.post(
                f"{self.base_url}/sendVideoNote",
                data=form
            ) as resp:
                data = await helpers.handle_response(resp)
                if data and data.get("ok"):
                    result = data["result"]
                    chat = Chat(id=result.get("chat", {}).get("id"), type="unknown")
                    message = Message(
                        message_id=result.get("message_id"),
                        chat=chat,
                        date=result.get("date", 0),
                        from_user=result.get("from", {})
                    )
                    logger.info(f"ویدیو دایره‌ای به {chat_id} ارسال شد")
                    return message
                raise Exception(f"Error sending video note: {data.get('description', 'Unknown error')}")
        except Exception as e:
            logger.error(f"خطا در ارسال ویدیو دایره‌ای: {str(e)}")
            raise

    async def send_document(self, chat_id: int, document: str, caption: Optional[str] = None) -> Message:
        """ارسال فایل (مثل PDF)"""
        if not self.session:
            await self.connect()
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        with open(document, "rb") as f:
            file_content = f.read()
        form.add_field("document", file_content, filename=document.split("/")[-1])
        if caption:
            form.add_field("caption", caption)
        try:
            async with self.session.post(
                f"{self.base_url}/sendDocument",
                data=form
            ) as resp:
                data = await helpers.handle_response(resp)
                if data and data.get("ok"):
                    result = data["result"]
                    chat = Chat(id=result.get("chat", {}).get("id"), type="unknown")
                    message = Message(
                        message_id=result.get("message_id"),
                        chat=chat,
                        date=result.get("date", 0),
                        caption=result.get("caption"),
                        from_user=result.get("from", {})
                    )
                    logger.info(f"فایل به {chat_id} ارسال شد")
                    return message
                raise Exception(f"Error sending document: {data.get('description', 'Unknown error')}")
        except Exception as e:
            logger.error(f"خطا در ارسال فایل: {str(e)}")
            raise

    def on_message(self):
        """دکوراتور برای هندل کردن پیام‌ها با فیلترهای پیشرفته"""
        def decorator(handler: Callable):
            def wrapper(message: Message):
                if hasattr(message, "text") and message.text:
                    asyncio.create_task(handler(message))
            self.handlers.append(wrapper)
            return wrapper
        return decorator

    async def get_updates(self, offset: int, timeout: int) -> List[Message]:
        """دریافت آپدیت‌ها از API بله"""
        if not self.session:
            await self.connect()
        params = {"offset": offset, "timeout": timeout}
        try:
            async with self.session.get(
                f"{self.base_url}/getUpdates",
                params=params
            ) as resp:
                data = await helpers.handle_response(resp)
                if not data or not data.get("ok"):
                    logger.warning("پاسخ نادرست از سرور بله")
                    return []
                updates = data.get("result", [])
                messages = []
                for update in updates:
                    message_data = update.get("message")
                    if message_data:
                        chat_id = message_data.get("chat", {}).get("id")
                        if chat_id:
                            chat = Chat(id=chat_id, type="unknown")
                            from_data = message_data.get("from", {})
                            message = Message(
                                message_id=message_data.get("message_id"),
                                chat=chat,
                                date=message_data.get("date", 0),
                                text=message_data.get("text"),
                                from_user=from_data
                            )
                            messages.append(message)
                if updates:
                    self.last_update_id = max(update["update_id"] for update in updates) + 1
                return messages
        except Exception as e:
            logger.error(f"خطا در دریافت آپدیت‌ها: {str(e)}")
            return []

    async def start_polling(self, allowed_updates: Optional[List[str]] = None):
        """شروع پولینگ با آپدیت‌های فیلترشده و مدیریت قطع ارتباط"""
        await self.connect()  # اطمینان از اتصال قبل از شروع
        self.is_running = True
        offset = self.last_update_id
        while self.is_running:
            try:
                messages = await self.get_updates(offset, self.timeout)
                for message in messages:
                    if message:
                        offset = self.last_update_id
                        for handler in self.handlers:
                            await handler(message)
                await self._check_scheduled_tasks()
            except Exception as e:
                logger.error(f"خطا در پولینگ: {str(e)}")
            await asyncio.sleep(1)  # تأخیر 1 ثانیه

    async def _check_scheduled_tasks(self):
        """بررسی و اجرای وظایف زمان‌بندی‌شده"""
        current_time = time.time()
        tasks_to_remove = []
        for task in self.scheduled_tasks:
            if current_time >= task["time"]:
                await self.send_message(task["chat_id"], task["text"])
                tasks_to_remove.append(task)
        for task in tasks_to_remove:
            self.scheduled_tasks.remove(task)

    def schedule_message(self, chat_id: int, text: str, delay_seconds: int):
        """زمان‌بندی ارسال پیام"""
        task_time = time.time() + delay_seconds
        task = {"chat_id": chat_id, "text": text, "time": task_time, "task": None}
        self.scheduled_tasks.append(task)
        logger.info(f"پیام برای {chat_id} در {delay_seconds} ثانیه زمان‌بندی شد")

    async def get_chat_member(self, chat_id: int, user_id: int) -> dict:
        """دریافت اطلاعات عضویت کاربر در چت"""
        if not self.session:
            await self.connect()
        try:
            async with self.session.post(
                f"{self.base_url}/getChatMember",
                json={"chat_id": chat_id, "user_id": user_id}
            ) as resp:
                data = await helpers.handle_response(resp)
                if data and data.get("ok"):
                    return data["result"]
                raise Exception(f"Error getting chat member: {data.get('description', 'Unknown error')}")
        except Exception as e:
            logger.error(f"خطا در دریافت اطلاعات عضویت: {str(e)}")
            raise

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    def stop_polling(self):
        """توقف پولینگ"""
        self.is_running = False
        logger.info("پولینگ متوقف شد.")

if __name__ == "__main__":
    async def handle_message(message):
        await message.reply_text(f"دریافت شد: {message.text}")

    async def main():
        client = BaleClient("YOUR_BLE_TOKEN")
        client.on_message()(handle_message)
        await client.connect()
        client.schedule_message(123456789, "پیام زمان‌بندی‌شده", 5)
        await client.start_polling()

    asyncio.run(main())