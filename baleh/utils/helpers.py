import aiohttp
import logging

logger = logging.getLogger(__name__)

def format_message(text: str) -> str:
    """فرمت کردن پیام برای ارسال"""
    if not isinstance(text, str):
        text = str(text)
    return text.strip()

async def handle_response(response: aiohttp.ClientResponse) -> dict:
    """مدیریت پاسخ‌های API"""
    try:
        result = await response.json()
        if result.get("ok"):
            return result
        logger.error(f"خطای API بله: {result}")
        if result.get("error_code") == 403 and "Token not found" in result.get("description", ""):
            raise ValueError("توکن ربات نامعتبر است.")
        return None
    except Exception as e:
        logger.error(f"خطا در پردازش پاسخ: {str(e)}")
        raise
