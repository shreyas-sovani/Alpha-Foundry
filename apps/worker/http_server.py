"""Minimal read-only HTTP server for exposing preview and metadata."""
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional

from aiohttp import web

logger = logging.getLogger(__name__)


class ReadOnlyHTTPServer:
    """
    Minimal HTTP server that serves preview.json and metadata.json.
    
    Features:
    - Read-only (GET only)
    - CORS enabled
    - Proper content types
    - Request logging with latency
    - Graceful shutdown
    """
    
    def __init__(self, host: str, port: int, preview_path: str, metadata_path: str):
        self.host = host
        self.port = port
        self.preview_path = Path(preview_path)
        self.metadata_path = Path(metadata_path)
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
    
    async def handle_preview(self, request: web.Request) -> web.Response:
        """Serve preview.json with cache headers."""
        start_time = time.time()
        
        try:
            if not self.preview_path.exists():
                logger.warning(f"Preview file not found: {self.preview_path}")
                latency_ms = int((time.time() - start_time) * 1000)
                logger.info(f"GET /preview 404 {latency_ms}ms")
                return web.json_response(
                    {"error": "Preview not available"},
                    status=404,
                    headers={"Cache-Control": "no-store"}
                )
            
            with open(self.preview_path, "r") as f:
                data = json.load(f)
            
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(f"GET /preview 200 {latency_ms}ms")
            
            return web.json_response(
                data,
                headers={
                    "Cache-Control": "max-age=15",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET",
                }
            )
        
        except Exception as e:
            logger.error(f"Error serving preview: {e}")
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(f"GET /preview 500 {latency_ms}ms")
            return web.json_response(
                {"error": "Internal server error"},
                status=500,
                headers={"Cache-Control": "no-store"}
            )
    
    async def handle_metadata(self, request: web.Request) -> web.Response:
        """Serve metadata.json with no-store cache headers."""
        start_time = time.time()
        
        try:
            if not self.metadata_path.exists():
                logger.warning(f"Metadata file not found: {self.metadata_path}")
                latency_ms = int((time.time() - start_time) * 1000)
                logger.info(f"GET /metadata 404 {latency_ms}ms")
                return web.json_response(
                    {"error": "Metadata not available"},
                    status=404,
                    headers={"Cache-Control": "no-store"}
                )
            
            with open(self.metadata_path, "r") as f:
                data = json.load(f)
            
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(f"GET /metadata 200 {latency_ms}ms")
            
            return web.json_response(
                data,
                headers={
                    "Cache-Control": "no-store",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET",
                }
            )
        
        except Exception as e:
            logger.error(f"Error serving metadata: {e}")
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(f"GET /metadata 500 {latency_ms}ms")
            return web.json_response(
                {"error": "Internal server error"},
                status=500,
                headers={"Cache-Control": "no-store"}
            )
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        start_time = time.time()
        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"GET /health 200 {latency_ms}ms")
        return web.json_response(
            {"status": "ok"},
            headers={
                "Cache-Control": "no-store",
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    async def start(self):
        """Start the HTTP server."""
        self.app = web.Application()
        
        # Register routes
        self.app.router.add_get("/preview", self.handle_preview)
        self.app.router.add_get("/metadata", self.handle_metadata)
        self.app.router.add_get("/health", self.handle_health)
        
        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        logger.info(f"✓ HTTP server started on http://{self.host}:{self.port}")
        logger.info(f"  • GET http://{self.host}:{self.port}/preview")
        logger.info(f"  • GET http://{self.host}:{self.port}/metadata")
        logger.info(f"  • GET http://{self.host}:{self.port}/health")
    
    async def stop(self):
        """Stop the HTTP server gracefully."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("✓ HTTP server stopped")


async def run_server(host: str, port: int, preview_path: str, metadata_path: str):
    """
    Run the HTTP server until interrupted.
    
    This is a standalone function that can be called from run.py.
    """
    server = ReadOnlyHTTPServer(host, port, preview_path, metadata_path)
    await server.start()
    
    try:
        # Keep server running
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        await server.stop()
        raise
