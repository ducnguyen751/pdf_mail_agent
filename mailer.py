import os
import httpx

MCP_URL = os.getenv("MCP_API_URL")
API_KEY = os.getenv("MCP_API_KEY")

async def send_email_async(to: str, subject: str, body: str, attachment_path: str):
    """
    Gửi email bất đồng bộ qua MCP Server.
    """
    with open(attachment_path, 'rb') as f:
        file_bytes = f.read()
    payload = {
        "to": to,
        "subject": subject,
        "body": body,
        "attachment": file_bytes.decode('latin1')
    }
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient() as client:
        r = await client.post(MCP_URL, json=payload, headers=headers)
        r.raise_for_status()


def send_email_sync(to: str, subject: str, body: str, attachment_path: str):
    """
    Wrapper đồng bộ cho send_email_async, để gọi từ Streamlit hoặc watcher.
    """
    import asyncio
    asyncio.run(send_email_async(to, subject, body, attachment_path))