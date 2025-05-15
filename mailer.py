import os, httpx

MCP_URL = os.getenv('MCP_API_URL')
API_KEY = os.getenv('MCP_API_KEY')

async def send_email_async(to, subject, body, attachment_path):
    with open(attachment_path,'rb') as f:
        data = f.read()
    payload = {'to':to,'subject':subject,'body':body,'attachment':data.decode('latin1')}
    headers={'Authorization':f"Bearer {API_KEY}"}
    async with httpx.AsyncClient() as client:
        r = await client.post(MCP_URL,json=payload,headers=headers)
        r.raise_for_status()

def send_email_sync(to,subject,body,attachment_path):
    import asyncio
    asyncio.run(send_email_async(to,subject,body,attachment_path))