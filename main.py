#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

import uvicorn
from pathlib import Path
import argparse
import sys
import logging
from core.registrar import register_app
from core.conf import settings

logger = logging.getLogger(__name__)

app = register_app()


@app.get("/")
async def root():
    return {
        "message": "Welcome to PicFast",
        "version": settings.PROJECT_VERSION,
        "docs_url": settings.DOCS_URL,
        "redoc_url": settings.REDOCS_URL,
        "openai_url": settings.OPENAPI_URL,
    }


def run_server(host: str, port: int):
    logger.info(f"Environment Variables: {os.environ}")
    config = uvicorn.Config(
        app=f'{Path(__file__).stem}:app',
        host=host,
        port=port,
        reload=settings.RELOAD
    )
    server = uvicorn.Server(config)
    try:
        logger.info(f"Starting server on {host}:{port}")
        server.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down gracefully...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e
    finally:
        logger.info("Server is shutting down")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FastAPI server.")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Port to run the server on")
    parser.add_argument("--host", type=str, default=settings.HOST, help="Host to run the server on")
    args = parser.parse_args()
    try:
        run_server(args.host, args.port)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        raise e
    finally:
        logger.info("Application has been shut down")
