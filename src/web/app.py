"""
Optional web interface for health checks and webhooks
"""

import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger

from ..config import settings, BOT_NAME, BOT_VERSION
from ..database import db
from ..services import UserService


# Create FastAPI app
app = FastAPI(
    title=f"{BOT_NAME} Web Interface",
    description="Health checks and webhook endpoints for MedusaXD AI Image Editor Bot",
    version=BOT_VERSION
)


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    try:
        await db.connect()
        logger.info("Web service database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    try:
        await db.disconnect()
        logger.info("Web service database connection closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": BOT_NAME,
        "version": BOT_VERSION,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Render.com"""
    try:
        # Check database connection
        if not db.client:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        # Test database ping
        await db.client.admin.command('ping')
        
        # Get basic stats
        analytics = await UserService.get_bot_analytics()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": BOT_NAME,
                "version": BOT_VERSION,
                "environment": settings.environment,
                "timestamp": datetime.utcnow().isoformat(),
                "database": "connected",
                "stats": {
                    "total_users": analytics.get("total_users", 0),
                    "total_edits": analytics.get("total_edits", 0),
                    "success_rate": analytics.get("success_rate", 0)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/stats")
async def get_stats():
    """Get bot statistics"""
    try:
        analytics = await UserService.get_bot_analytics()
        
        if "error" in analytics:
            raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
        
        return JSONResponse(
            status_code=200,
            content={
                "service": BOT_NAME,
                "version": BOT_VERSION,
                "statistics": analytics,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook")
async def webhook_handler():
    """Webhook endpoint (placeholder for future use)"""
    return {
        "status": "webhook_received",
        "message": "Webhook functionality not implemented yet",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/info")
async def bot_info():
    """Get bot information"""
    return {
        "name": BOT_NAME,
        "version": BOT_VERSION,
        "username": settings.bot_username,
        "environment": settings.environment,
        "features": [
            "AI-powered image editing",
            "Text-to-image modifications",
            "Color changes",
            "Object removal/addition",
            "Background modifications",
            "Text editing in images"
        ],
        "powered_by": "BFL.ai FLUX.1 Kontext [pro]",
        "database": "MongoDB",
        "deployment": "Render.com",
        "timestamp": datetime.utcnow().isoformat()
    }


def create_app():
    """Create and configure the FastAPI app"""
    return app


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 10000))
    
    logger.info(f"Starting {BOT_NAME} web service on port {port}")
    
    uvicorn.run(
        "src.web.app:app",
        host="0.0.0.0",
        port=port,
        log_level=settings.log_level.lower(),
        reload=settings.environment == "development"
    )
