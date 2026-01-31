import asyncio
from pyrogram import Client, idle
from zyrax.config import Config
from zyrax.modules import load_modules
from aiohttp import web

async def main():
    # Load all modules dynamically before starting client
    load_modules()
    
    app = Client(
        "ZyraX",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        plugins=dict(root="zyrax.modules")
    )
    
    # Start the Bridge Web Server
    # We define a simple handler here that uses 'app' to send messages
    async def handle_webhook(request):
        chat_id = request.match_info.get('chat_id')
        try:
            data = await request.json()
            text = data.get("text")
            if chat_id and text:
                # Resolve chat_id - try integer conversion
                try:
                    chat_id_int = int(chat_id)
                except ValueError:
                    chat_id_int = chat_id # Use username or string
                
                await app.send_message(chat_id_int, f"[Webhook]: {text}")
                return web.Response(text="Sent")
        except Exception as e:
            return web.Response(text=str(e), status=500)
        return web.Response(text="Invalid Request", status=400)

    server = web.Application()
    server.add_routes([web.post('/webhook/{chat_id}', handle_webhook)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Bridge Server running on 0.0.0.0:8080")

    await app.start()
    print("ZyraX started successfully!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
