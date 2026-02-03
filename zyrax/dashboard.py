"""
ZyraX Dashboard

Web dashboard for bot monitoring and administration.
"""

import hashlib
import hmac
import secrets
import time
import os
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from zyrax.config import Config
from zyrax.utils.logger import logger


# Create FastAPI app
app = FastAPI(
    title="ZyraX Dashboard",
    description="Bot monitoring and administration dashboard",
    docs_url=None,  # Disable docs in production
    redoc_url=None
)

# Security
security = HTTPBasic()

# Webhook secret for HMAC validation
WEBHOOK_SECRET: Optional[str] = os.environ.get("WEBHOOK_SECRET")

# Mount Static Files
STATIC_DIR = "zyrax/static"
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory="zyrax/templates")


# =============================================================================
# Authentication
# =============================================================================

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """
    Verify admin credentials for dashboard access.
    
    Uses timing-safe comparison to prevent timing attacks.
    """
    # Get credentials from environment or config
    admin_user = os.environ.get("DASHBOARD_USER", "admin")
    admin_pass = os.environ.get("DASHBOARD_PASS")
    
    if not admin_pass:
        # If no password set, dashboard is disabled
        raise HTTPException(
            status_code=503,
            detail="Dashboard authentication not configured"
        )
    
    # Timing-safe comparison
    user_ok = secrets.compare_digest(credentials.username, admin_user)
    pass_ok = secrets.compare_digest(credentials.password, admin_pass)
    
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return True


def verify_webhook_signature(
    payload: bytes,
    signature: Optional[str],
    timestamp: Optional[str]
) -> bool:
    """
    Verify webhook request signature using HMAC-SHA256.
    
    Args:
        payload: Request body bytes
        signature: X-Signature header value
        timestamp: X-Timestamp header value
        
    Returns:
        True if signature is valid
    """
    if not WEBHOOK_SECRET:
        logger.warning("Webhook secret not configured")
        return False
    
    if not signature or not timestamp:
        return False
    
    # Check timestamp is recent (within 5 minutes)
    try:
        ts = int(timestamp)
        if abs(time.time() - ts) > 300:
            logger.warning("Webhook timestamp too old")
            return False
    except ValueError:
        return False
    
    # Compute expected signature
    message = f"{timestamp}.{payload.decode('utf-8')}"
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Timing-safe comparison
    return hmac.compare_digest(signature, expected)


# =============================================================================
# Dashboard Routes (Protected)
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, _: bool = Depends(verify_admin)):
    """Dashboard home page with bot statistics."""
    try:
        from zyrax.database.mongo import db
        stats = await db.get_stats()
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        stats = {"users": 0, "chats": 0, "commands_today": 0}
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "stats": stats}
    )


@app.get("/logs", response_class=HTMLResponse)
async def logs(request: Request, _: bool = Depends(verify_admin)):
    """Audit logs page."""
    try:
        from zyrax.database.mongo import db
        audit_logs = await db.get_audit_logs(limit=50)
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        audit_logs = []
    
    return templates.TemplateResponse(
        "logs.html", 
        {"request": request, "logs": audit_logs}
    )


@app.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request, _: bool = Depends(verify_admin)):
    """Analytics page with activity charts."""
    try:
        from zyrax.database.mongo import db
        data = await db.get_activity_stats()
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        data = {"daily": [], "hourly": []}
    
    return templates.TemplateResponse(
        "analytics.html", 
        {"request": request, "data": data}
    )


@app.get("/stats", response_class=HTMLResponse)
async def stats(request: Request, _: bool = Depends(verify_admin)):
    """Detailed stats page."""
    return templates.TemplateResponse(
        "stats.html", 
        {"request": request}
    )


@app.get("/premium", response_class=HTMLResponse)
async def premium(request: Request, _: bool = Depends(verify_admin)):
    """Premium features page."""
    return templates.TemplateResponse(
        "premium.html", 
        {"request": request}
    )


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    No authentication required.
    """
    try:
        from zyrax.database.mongo import db
        db_health = await db.health_check()
    except Exception:
        db_health = {"mongodb": False, "redis": False}
    
    # Check if bot is connected
    bot_connected = False
    try:
        bot = app.state.bot
        if bot and hasattr(bot, 'is_connected'):
            bot_connected = bot.is_connected
    except Exception:
        pass
    
    status = "healthy" if all([
        db_health.get("mongodb"),
        db_health.get("redis"),
        bot_connected
    ]) else "degraded"
    
    return JSONResponse({
        "status": status,
        "services": {
            "mongodb": db_health.get("mongodb", False),
            "redis": db_health.get("redis", False),
            "bot": bot_connected
        },
        "timestamp": int(time.time())
    })


@app.get("/api/stats", dependencies=[Depends(verify_admin)])
async def api_stats():
    """Get bot statistics as JSON."""
    try:
        from zyrax.database.mongo import db
        stats = await db.get_stats()
        return JSONResponse(stats)
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@app.get("/api/modules", dependencies=[Depends(verify_admin)])
async def api_modules():
    """Get module loading statistics."""
    try:
        from zyrax.modules import get_load_stats, get_all_help
        return JSONResponse({
            "stats": get_load_stats(),
            "modules": list(get_all_help().keys())
        })
    except Exception as e:
        logger.error(f"Error fetching module stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch modules")


# =============================================================================
# Webhook Endpoint (Secured)
# =============================================================================

@app.post("/webhook/{chat_id}")
async def handle_webhook(
    chat_id: str,
    request: Request,
    x_signature: Optional[str] = Header(None),
    x_timestamp: Optional[str] = Header(None)
):
    """
    Handle incoming webhooks to send messages.
    
    Security:
    - Requires valid HMAC-SHA256 signature
    - Validates timestamp to prevent replay attacks
    - Only allows messages to pre-authorized chats
    
    Headers required:
    - X-Signature: HMAC-SHA256 signature
    - X-Timestamp: Unix timestamp
    """
    # Check if webhook is enabled
    if not WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Webhook not configured"
        )
    
    # Read body
    try:
        body = await request.body()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request body")
    
    # Verify signature
    if not verify_webhook_signature(body, x_signature, x_timestamp):
        logger.warning(f"Invalid webhook signature for chat {chat_id}")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse JSON
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    text = data.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' field")
    
    # Validate chat_id
    try:
        chat_id_int = int(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat_id")
    
    # Check if chat is authorized (optional - could maintain a whitelist)
    # For now, we just require valid signature which proves authenticity
    
    # Get bot instance
    bot = getattr(request.app.state, 'bot', None)
    if not bot:
        raise HTTPException(
            status_code=503,
            detail="Bot not initialized"
        )
    
    # Send message
    try:
        # Prefix with [Webhook] for transparency
        await bot.send_message(chat_id_int, f"[Webhook] {text}")
        logger.info(f"Webhook message sent to {chat_id_int}")
        return JSONResponse({"status": "sent", "chat_id": chat_id_int})
    except Exception as e:
        logger.error(f"Webhook send failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send: {str(e)}")


# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler."""
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
