from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="ZyraX Dashboard")

# Mount Static Files
if not os.path.exists("zyrax/static"):
    os.makedirs("zyrax/static")
app.mount("/static", StaticFiles(directory="zyrax/static"), name="static")

# Templates
templates = Jinja2Templates(directory="zyrax/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    from zyrax.database.mongo import db
    stats = await db.get_stats()
    return templates.TemplateResponse("index.html", {"request": request, "stats": stats})

@app.get("/stats", response_class=HTMLResponse)
async def stats(request: Request):
    return templates.TemplateResponse("stats.html", {"request": request})

@app.get("/premium", response_class=HTMLResponse)
async def premium(request: Request):
    return templates.TemplateResponse("premium.html", {"request": request})

@app.post("/webhook/{chat_id}")
async def handle_webhook(chat_id: str, request: Request):
    try:
        data = await request.json()
        text = data.get("text")
        bot = request.app.state.bot # Pyrogram client injected here
        
        if chat_id and text:
            try:
                chat_id_int = int(chat_id)
            except ValueError:
                chat_id_int = chat_id
            
            await bot.send_message(chat_id_int, f"[Webhook]: {text}")
            return {"status": "sent"}
    except Exception as e:
        return {"error": str(e), "status": 500}
    return {"status": "invalid request", "code": 400}
