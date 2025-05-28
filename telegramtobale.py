import logging
import os
from typing import Dict
from PIL import Image
import subprocess

from baleh import BaleClient
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters
import asyncio

# بارگذاری فایل .env
load_dotenv()

# تنظیمات لاگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# غیرفعال کردن لاگ‌های غیرضروری
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("baleh").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# خواندن متغیرها از .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BLE_TOKEN = os.getenv("BLE_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BLE_CHAT_ID = os.getenv("BLE_CHAT_ID")
CREATOR_TELEGRAM_ID = os.getenv("CREATOR_TELEGRAM_ID")
CREATOR_BLE_ID = os.getenv("CREATOR_BLE_ID")

# چک کردن متغیرها
if not all(
    [
        TELEGRAM_TOKEN,
        BLE_TOKEN,
        TELEGRAM_CHAT_ID,
        BLE_CHAT_ID,
        CREATOR_TELEGRAM_ID,
        CREATOR_BLE_ID,
    ]
):
    logger.error(
        "یکی از متغیرهای محیطی (TELEGRAM_TOKEN, BLE_TOKEN, TELEGRAM_CHAT_ID, BLE_CHAT_ID, CREATOR_TELEGRAM_ID, CREATOR_BLE_ID) تنظیم نشده است."
    )
    exit(1)

# تبدیل chat IDها به عدد
try:
    TELEGRAM_CHAT_ID = int(TELEGRAM_CHAT_ID)
    BLE_CHAT_ID = int(BLE_CHAT_ID)
    CREATOR_TELEGRAM_ID = int(CREATOR_TELEGRAM_ID)
    CREATOR_BLE_ID = int(CREATOR_BLE_ID)
except ValueError as e:
    logger.error(f"خطا در تبدیل chat IDها به عدد: {e}")
    logger.error("TELEGRAM_CHAT_ID، BLE_CHAT_ID، CREATOR_TELEGRAM_ID و CREATOR_BLE_ID باید عدد باشند.")
    exit(1)

# حالت‌های ConversationHandler برای تلگرام
REPORT_WAITING = 1

async def telegram_start(update, context) -> None:
    """پاسخ به دستور /start در تلگرام"""
    welcome_message = (
        "👋 به ربات خوش آمدید!\n"
        "این ربات از پیام‌های متن، عکس، ویدیو، صوت، فایل، استیکر، انیمیشن، صدا، و موقعیت مکانی پشتیبانی می‌کند.\n"
        "برای گزارش، از /report استفاده کنید.\n"
        "بیا شروع کنیم!"
    )
    await update.message.reply_text(welcome_message)
    logger.info(
        f"دستور /start در تلگرام اجرا شد - Chat ID: {update.message.chat_id}, User ID: {update.message.from_user.id}"
    )

async def telegram_report(update, context) -> int:
    """پاسخ به دستور /report در تلگرام و انتظار برای گزارش"""
    report_message = (
        "📝 لطفاً گزارش یا پیشنهاد خود را در پیام بعدی بنویسید.\n"
        "ما آن را برای سازنده ارسال می‌کنیم!"
    )
    await update.message.reply_text(report_message)
    logger.info(
        f"دستور /report در تلگرام اجرا شد - Chat ID: {update.message.chat_id}, User ID: {update.message.from_user.id}"
    )
    return REPORT_WAITING

async def telegram_receive_report(update, context) -> int:
    """دریافت و ارسال گزارش به سازنده در تلگرام و بله"""
    try:
        report_text = update.message.text
        user_id = update.message.from_user.id
        username = update.message.from_user.username or "بدون نام کاربری"
        first_name = update.message.from_user.first_name or "no name"
        report_message = (
            f"📩 گزارش جدید:\n"
            f"👤 آیدی عددی: {user_id}\n"
            f"📛 نام کاربری: @{username}\n"
            f"🧑 نام: {first_name}\n"
            f"📜 متن گزارش:\n{report_text}"
        )

        # ارسال به سازنده در تلگرام
        await context.bot.send_message(
            chat_id=CREATOR_TELEGRAM_ID, text=report_message
        )
        logger.info(
            f"گزارش از تلگرام (user_id: {user_id}) به سازنده (telegram_id: {CREATOR_TELEGRAM_ID}) ارسال شد: {report_text}"
        )

        # ارسال به سازنده در بله
        async with BaleClient(BLE_TOKEN) as ble_client:
            await ble_client.send_message(
                chat_id=CREATOR_BLE_ID, text=report_message
            )
        logger.info(
            f"گزارش از تلگرام (user_id: {user_id}) به سازنده (ble_id: {CREATOR_BLE_ID}) ارسال شد: {report_text}"
        )

        await update.message.reply_text(
            "✅ گزارش شما با موفقیت به سازنده ارسال شد. ممنون!"
        )
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"خطا در ارسال گزارش تلگرام: {str(e)}")
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره امتحان کنید.")
        return ConversationHandler.END

async def cancel_report(update, context) -> int:
    """لغو فرآیند گزارش"""
    await update.message.reply_text("❌ فرآیند گزارش لغو شد.")
    logger.info(
        f"گزارش تلگرام لغو شد - Chat ID: {update.message.chat_id}, User ID: {update.message.from_user.id}"
    )
    return ConversationHandler.END

async def handle_telegram_message(update, context) -> None:
    """پردازش پیام‌های تلگرام و ارسال به بله"""
    try:
        # فقط پیام‌های گروه/کانال مشخص
        if update.message.chat_id != TELEGRAM_CHAT_ID:
            logger.debug(
                f"پیام از chat_id {update.message.chat_id} نادیده گرفته شد (فقط {TELEGRAM_CHAT_ID} مجاز است)."
            )
            return

        # آماده‌سازی پیام برای بله
        user_id = update.message.from_user.id
        username = update.message.from_user.username or "بدون نام کاربری"
        first_name = update.message.from_user.first_name or "Ø"
        date = update.message.date.strftime("%Y-%m-%d %H:%M:%S")
        ble_message = (
            f"📬 پیام از تلگرام:\n"
            f"👤 آیدی عددی: {user_id}\n"
            f"📛 نام کاربری: @{username}\n"
            f"🧑 نام: {first_name}\n"
            f"📅 تاریخ: {date}\n"
        )

        async with BaleClient(BLE_TOKEN) as ble_client:
            logger.info(f"کلاینت بله متصل شد - session: {ble_client.session is not None}")
            # متن
            if update.message.text and not update.message.photo and not update.message.video and not update.message.voice and not update.message.audio and not update.message.animation and not update.message.sticker and not update.message.location and not update.message.video_note:
                ble_message += f"💬 متن:\n{update.message.text}"
                await ble_client.send_message(
                    chat_id=BLE_CHAT_ID,
                    text=ble_message,
                )
                logger.info(
                    f"پیام متنی از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد: {update.message.text}"
                )
                return

            # عکس (با یا بدون کپشن)
            if update.message.photo:
                photo = update.message.photo[-1]
                file = await context.bot.get_file(photo.file_id)
                file_path = f"{photo.file_id}.jpg"
                logger.info(f"دانلود عکس از تلگرام: {file_path}")
                await file.download_to_drive(file_path)
                ble_message += f"📎 فایل: {photo.file_id}.jpg"
                if update.message.caption:
                    ble_message += f"\n📝 کپشن: {update.message.caption}"
                await ble_client.send_photo(
                    chat_id=BLE_CHAT_ID,
                    photo=file_path,
                    caption=ble_message
                )
                os.remove(file_path)
                logger.info(
                    f"پیام عکس از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد"
                    + (f" با کپشن: {update.message.caption}" if update.message.caption else "")
                )
                return

            # فیلم
            if update.message.video:
                video = update.message.video
                file = await context.bot.get_file(video.file_id)
                file_path = f"{video.file_id}.mp4"
                logger.info(f"دانلود ویدیو از تلگرام: {file_path}")
                await file.download_to_drive(file_path)
                ble_message += f"📎 فایل: {video.file_id}.mp4"
                if update.message.caption:
                    ble_message += f"\n📝 کپشن: {update.message.caption}"
                logger.info(f"ارسال ویدیو به بله: {file_path}, مدت: {video.duration}")
                await ble_client.send_video(
                    chat_id=BLE_CHAT_ID,
                    video=file_path,
                    caption=ble_message,
                    duration=video.duration
                )
                os.remove(file_path)
                logger.info(
                    f"پیام ویدیو از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد - مسیر: {file_path}"
                    + (f" با کپشن: {update.message.caption}" if update.message.caption else "")
                )
                return

            # صوت
            if update.message.voice:
                voice = update.message.voice
                file = await context.bot.get_file(voice.file_id)
                file_path = f"{voice.file_id}.ogg"
                logger.info(f"دانلود صوت از تلگرام: {file_path}")
                await file.download_to_drive(file_path)
                ble_message += f"🎵 فایل صوتی: {voice.file_id}.ogg"
                if update.message.caption:
                    ble_message += f"\n📝 کپشن: {update.message.caption}"
                await ble_client.send_voice(
                    chat_id=BLE_CHAT_ID,
                    voice=file_path,
                    caption=ble_message
                )
                os.remove(file_path)
                logger.info(
                    f"پیام صوتی از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد - مسیر: {file_path}"
                    + (f" با کپشن: {update.message.caption}" if update.message.caption else "")
                )
                return

            # صدا با کیفیت بالا (مثل موسیقی)
            if update.message.audio:
                audio = update.message.audio
                file = await context.bot.get_file(audio.file_id)
                file_path = audio.file_name or f"{audio.file_id}.mp3"
                logger.info(f"دانلود صدا از تلگرام: {file_path}")
                await file.download_to_drive(file_path)
                ble_message += f"🎶 فایل صوتی: {audio.file_name}"
                if update.message.caption:
                    ble_message += f"\n📝 کپشن: {update.message.caption}"
                await ble_client.send_audio(
                    chat_id=BLE_CHAT_ID,
                    audio=file_path,
                    caption=ble_message,
                    duration=audio.duration
                )
                os.remove(file_path)
                logger.info(
                    f"پیام صوتی با کیفیت از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد - مسیر: {file_path}"
                    + (f" با کپشن: {update.message.caption}" if update.message.caption else "")
                )
                return

            # انیمیشن (مثل GIF)
            if update.message.animation:
                animation = update.message.animation
                file = await context.bot.get_file(animation.file_id)
                file_path = animation.file_name or f"{animation.file_id}.gif"
                logger.info(f"دانلود انیمیشن از تلگرام: {file_path}")
                await file.download_to_drive(file_path)
                ble_message += f"🎬 فایل انیمیشن: {animation.file_name}"
                if update.message.caption:
                    ble_message += f"\n📝 کپشن: {update.message.caption}"
                await ble_client.send_animation(
                    chat_id=BLE_CHAT_ID,
                    animation=file_path,
                    caption=ble_message
                )
                os.remove(file_path)
                logger.info(
                    f"پیام انیمیشن از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد - مسیر: {file_path}"
                    + (f" با کپشن: {update.message.caption}" if update.message.caption else "")
                )
                return

            # استیکر (شامل WebP و TGS)
            if update.message.sticker:
                sticker = update.message.sticker
                file = await context.bot.get_file(sticker.file_id)
                file_extension = "tgs" if sticker.is_animated else "webp"
                file_path = f"{sticker.file_id}.{file_extension}"
                logger.info(f"دانلود استیکر از تلگرام: {file_path}, انیمیشنی: {sticker.is_animated}")
                await file.download_to_drive(file_path)
                try:
                    async with BaleClient(BLE_TOKEN) as ble_client:
                        if sticker.is_animated:
                            await ble_client.send_animation(
                                chat_id=BLE_CHAT_ID,
                                animation=file_path
                            )
                            logger.info(
                                f"پیام استیکر انیمیشنی از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد - مسیر: {file_path}, فرمت ارسال‌شده: WebM"
                            )
                        else:
                            # تبدیل WebP به PNG
                            with Image.open(file_path) as img:
                                png_path = file_path.replace(".webp", ".png")
                                img.save(png_path, "PNG")
                            await ble_client.send_photo(
                                chat_id=BLE_CHAT_ID,
                                photo=png_path
                            )
                            logger.info(
                                f"پیام استیکر استاتیک از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد - مسیر: {png_path}, فرمت ارسال‌شده: PNG"
                            )
                            os.remove(png_path)
                except Exception as e:
                    logger.error(f"خطا در پردازش استیکر: {str(e)}")
                    await ble_client.send_message(
                        chat_id=BLE_CHAT_ID,
                        text="⚠️ خطا در ارسال استیکر: متأسفم، استیکر ارسال نشد."
                    )
                    logger.info(
                        f"پیام خطا برای استیکر از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد"
                    )
                os.remove(file_path)
                return

            # موقعیت مکانی
            if update.message.location:
                location = update.message.location
                logger.info(f"دریافت موقعیت مکانی: latitude={location.latitude}, longitude={location.longitude}")
                ble_message += f"📍 موقعیت: {location.latitude}, {location.longitude}"
                await ble_client.send_location(
                    chat_id=BLE_CHAT_ID,
                    latitude=location.latitude,
                    longitude=location.longitude
                )
                logger.info(
                    f"موقعیت مکانی از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد"
                )
                return

            # ویدیوی دایره‌ای
            if update.message.video_note:
                video_note = update.message.video_note
                file = await context.bot.get_file(video_note.file_id)
                file_path = f"{video_note.file_id}.mp4"
                logger.info(f"دانلود ویدیو دایره‌ای از تلگرام: {file_path}")
                await file.download_to_drive(file_path)
                ble_message += f"🎥 فایل ویدیو دایره‌ای: {video_note.file_id}.mp4"
                if update.message.caption:
                    ble_message += f"\n📝 کپشن: {update.message.caption}"
                await ble_client.send_video_note(
                    chat_id=BLE_CHAT_ID,
                    video_note=file_path,
                    duration=video_note.duration
                )
                os.remove(file_path)
                logger.info(
                    f"پیام ویدیو دایره‌ای از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد - مسیر: {file_path}"
                    + (f" با کپشن: {update.message.caption}" if update.message.caption else "")
                )
                return

            # فایل (مثل PDF)
            if update.message.document:
                document = update.message.document
                file = await context.bot.get_file(document.file_id)
                file_path = document.file_name or f"{document.file_id}{os.path.splitext(document.file_name)[1] if document.file_name else '.bin'}"
                logger.info(f"دانلود فایل از تلگرام: {file_path}")
                await file.download_to_drive(file_path)
                ble_message += f"📎 فایل: {document.file_name or document.file_id}"
                if update.message.caption:
                    ble_message += f"\n📝 کپشن: {update.message.caption}"
                await ble_client.send_document(
                    chat_id=BLE_CHAT_ID,
                    document=file_path,
                    caption=ble_message
                )
                os.remove(file_path)
                logger.info(
                    f"پیام فایل از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد: {document.file_name or document.file_id}"
                    + (f" با کپشن: {update.message.caption}" if update.message.caption else "")
                )
                return

            # سایر انواع پیام
            ble_message += "❓ نوع: ناشناخته"
            await ble_client.send_message(
                chat_id=BLE_CHAT_ID,
                text=ble_message,
            )
            logger.info(
                f"پیام ناشناخته از تلگرام (chat_id: {TELEGRAM_CHAT_ID}) به بله (chat_id: {BLE_CHAT_ID}) ارسال شد"
            )

    except Exception as e:
        logger.error(f"خطا در پردازش پیام تلگرام: {str(e)}")

async def ble_start(ble_client: BaleClient, message) -> None:
    """پاسخ به دستور /start در بله"""
    try:
        welcome_message = (
            "👋 به ربات بله خوش آمدید!\n"
            "این ربات از پیام‌های متن، عکس، ویدیو، صوت، فایل، استیکر، انیمیشن، صدا، و موقعیت مکانی پشتیبانی می‌کند.\n"
            "برای گزارش، از /report استفاده کنید.\n"
            "بیا شروع کنیم!"
        )
        logger.info(f"در حال ارسال پاسخ /start به Chat ID: {message.chat.id}")
        # اضافه کردن دکمه اینلاین نمونه
        reply_markup = {
            "inline_keyboard": [
                [{"text": "گزینه 1", "callback_data": "option1"}],
                [{"text": "گزینه 2", "callback_data": "option2"}]
            ]
        }
        await ble_client.send_message(
            chat_id=message.chat.id,
            text=welcome_message,
            reply_markup=reply_markup
        )
        logger.info(
            f"دستور /start در بله اجرا شد - Chat ID: {message.chat.id}, User ID: {getattr(message.from_user, 'id', 'ناشناس')}"
        )
    except Exception as e:
        logger.error(f"خطا در پردازش /start بله: {str(e)}")

async def ble_report(ble_client: BaleClient, message) -> None:
    """پاسخ به دستور /report در بله و انتظار برای گزارش"""
    try:
        report_message = (
            "📝 لطفاً گزارش یا پیشنهاد خود را در پیام بعدی بنویسید.\n"
            "ما آن را برای سازنده ارسال می‌کنیم!"
        )
        await ble_client.send_message(
            chat_id=message.chat.id,
            text=report_message
        )
        logger.info(
            f"دستور /report در بله اجرا شد - Chat ID: {message.chat.id}, User ID: {getattr(message.from_user, 'id', 'ناشناس')}"
        )
        # ذخیره وضعیت گزارش در بله
        ble_report_status[message.chat.id] = True
    except Exception as e:
        logger.error(f"خطا در پردازش /report بله: {str(e)}")

# ذخیره وضعیت گزارش در بله
ble_report_status: Dict[int, bool] = {}

async def handle_ble_message(ble_client: BaleClient, message) -> None:
    """پردازش پیام‌های بله"""
    try:
        logger.info(f"پیام بله دریافت شد: {message.text} - Chat ID: {message.chat.id}")
        text = getattr(message, "text", None)
        chat_id = message.chat.id
        user_id = getattr(message.from_user, "id", "ناشناس") if message.from_user else "ناشناس"
        username = getattr(message.from_user, "username", "بدون نام کاربری") if message.from_user else "بدون نام کاربری"
        first_name = getattr(message.from_user, "first_name", "no name") if message.from_user else "no name"

        if text:
            if text.lower() == "/start":
                await ble_start(ble_client, message)
            elif text.lower() == "/report":
                await ble_report(ble_client, message)
            elif chat_id in ble_report_status and ble_report_status[chat_id]:
                # ارسال گزارش به سازنده
                report_message = (
                    f"📩 گزارش جدید:\n"
                    f"👤 آیدی عددی: {user_id}\n"
                    f"📛 نام کاربری: @{username}\n"
                    f"🧑 نام: {first_name}\n"
                    f"📜 متن گزارش:\n{text}"
                )

                # ارسال به سازنده در تلگرام
                async with Application.builder().token(TELEGRAM_TOKEN).build() as app:
                    await app.bot.send_message(
                        chat_id=CREATOR_TELEGRAM_ID, text=report_message
                    )
                logger.info(
                    f"گزارش از بله (user_id: {user_id}) به سازنده (telegram_id: {CREATOR_TELEGRAM_ID}) ارسال شد: {text}"
                )

                # ارسال به سازنده در بله
                await ble_client.send_message(
                    chat_id=CREATOR_BLE_ID, text=report_message
                )
                logger.info(
                    f"گزارش از بله (user_id: {user_id}) به سازنده (ble_id: {CREATOR_BLE_ID}) ارسال شد: {text}"
                )

                await ble_client.send_message(
                    chat_id=chat_id,
                    text="✅ گزارش شما با موفقیت به سازنده ارسال شد. ممنون!"
                )
                ble_report_status.pop(chat_id, None)

    except Exception as e:
        logger.error(f"خطا در پردازش پیام بله: {str(e)}")

async def run_ble_client(ble_client: BaleClient) -> None:
    """اجرای کلاینت بله در حلقه async"""
    try:
        await ble_client.connect()
        logger.info("اتصال به کلاینت بله برقرار شد")
        await ble_client.start_polling()
        logger.info("کلاینت بله در حال اجرا است...")
        while True:
            await asyncio.sleep(3600)  # نگه داشتن حلقه
    except Exception as e:
        logger.error(f"خطا در اجرای کلاینت بله: {str(e)}")
        raise
    finally:
        try:
            await ble_client.disconnect()
        except Exception as e:
            logger.error(f"خطا در بستن کلاینت بله: {str(e)}")

async def main() -> None:
    """اجرای ربات تلگرام و بله"""
    try:
        # ایجاد اپلیکیشن تلگرام
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # ConversationHandler برای گزارش در تلگرام
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("report", telegram_report)],
            states={
                REPORT_WAITING: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, telegram_receive_report
                    )
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_report)],
        )

        # هندلرها برای تلگرام
        application.add_handler(CommandHandler("start", telegram_start))
        application.add_handler(conv_handler)
        application.add_handler(MessageHandler(filters.ALL, handle_telegram_message))

        # ایجاد کلاینت بله
        ble_client = BaleClient(BLE_TOKEN)
        ble_client.on_message()(lambda message: handle_ble_message(ble_client, message))

        # شروع ربات تلگرام
        logger.info("ربات تلگرام شروع شد...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        # اجرای کلاینت بله در تسک جداگانه
        asyncio.create_task(run_ble_client(ble_client))

        # نگه داشتن حلقه اصلی
        while True:
            await asyncio.sleep(3600)

    except Exception as e:
        logger.error(f"خطا در شروع ربات: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())