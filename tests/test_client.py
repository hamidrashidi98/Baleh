import pytest
import asyncio
from baleh import BaleClient

@pytest.mark.asyncio
async def test_send_message():
    client = BaleClient("invalid_token")
    result = await client.send_message(123456789, "Test")
    assert result is None

@pytest.mark.asyncio
async def test_get_me():
    client = BaleClient("invalid_token")
    result = await client.get_me()
    assert result is None