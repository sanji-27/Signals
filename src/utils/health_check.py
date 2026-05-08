import asyncio
from aiohttp import web
import os
import logging

logger = logging.getLogger(__name__)

async def handle(request):
    return web.Response(text="Bot is running")

async def start_health_check():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    logger.info(f"Starting health check server on port {port}")
    await site.start()
