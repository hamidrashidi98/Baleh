from dataclasses import dataclass
from typing import Optional, Any
from .chat import Chat

@dataclass
class Message:
    message_id: int
    chat: Chat
    date: int
    text: Optional[str] = None
    photo: Optional[list] = None
    video: Optional[dict] = None
    audio: Optional[dict] = None
    document: Optional[dict] = None
    sticker: Optional[dict] = None
    voice: Optional[dict] = None
    caption: Optional[str] = None
    from_user: Optional[dict] = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def reply_text(self, text: str, parse_mode: Optional[str] = None):
        """ارسال پاسخ متنی به چت"""
        from ..client import BaleClient
        client = BaleClient("")  # توکن باید از محیط خوانده شود
        if hasattr(self, 'chat') and hasattr(self.chat, 'id'):
            return await client.send_message(self.chat.id, text, parse_mode)
        else:
            raise ValueError("Chat ID not available for reply")