import asyncio
import json
import logging
import sys
from typing import Set

import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("websocket-relay")

browser_clients: Set[WebSocketServerProtocol] = set()
cli_clients: Set[WebSocketServerProtocol] = set()


async def relay_to_browsers(message: str) -> None:
    if not browser_clients:
        logger.info("No browser clients connected; message dropped.")
        return
    await asyncio.gather(
        *(client.send(message) for client in browser_clients),
        return_exceptions=True,
    )


async def relay_to_cli(message: str) -> None:
    if not cli_clients:
        logger.info("No CLI clients connected; message dropped.")
        return
    await asyncio.gather(
        *(client.send(message) for client in cli_clients),
        return_exceptions=True,
    )


async def handle_browser(websocket: WebSocketServerProtocol) -> None:
    browser_clients.add(websocket)
    logger.info(f"Browser connected ({websocket.remote_address}). Total: {len(browser_clients)}")
    try:
        async for message in websocket:
            logger.info(f"[Browser->CLI] {str(message)[:200]}")
            await relay_to_cli(message)
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Browser disconnected: {e}")
    finally:
        browser_clients.discard(websocket)
        logger.info(f"Browser removed. Total: {len(browser_clients)}")


async def handle_cli(websocket: WebSocketServerProtocol) -> None:
    cli_clients.add(websocket)
    logger.info(f"CLI connected ({websocket.remote_address}). Total: {len(cli_clients)}")
    try:
        async for message in websocket:
            logger.info(f"[CLI->Browser] {str(message)[:200]}")
            if not browser_clients:
                logger.warning("No browser client connected; notifying CLI client.")
                try:
                    data = json.loads(message)
                    req_id = data.get("request_id")
                    error_resp = json.dumps({
                        "request_id": req_id,
                        "error": "No browser extension client connected to Hermes relay server."
                    })
                    await websocket.send(error_resp)
                except Exception:
                    pass
            else:
                await relay_to_browsers(message)
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"CLI disconnected: {e}")
    finally:
        cli_clients.discard(websocket)
        logger.info(f"CLI removed. Total: {len(cli_clients)}")


async def register_client(websocket: WebSocketServerProtocol) -> None:
    try:
        raw = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        data = json.loads(raw)
        client_type = data.get("type")
        if client_type == "browser":
            await handle_browser(websocket)
        elif client_type == "cli":
            await handle_cli(websocket)
        else:
            logger.warning(f"Unknown client type '{client_type}'; closing.")
            await websocket.close(4003, "Invalid client type")
    except asyncio.TimeoutError:
        logger.warning(f"Registration timeout; closing.")
        await websocket.close(4001, "Registration timeout")
    except json.JSONDecodeError:
        logger.warning(f"Invalid registration JSON; closing.")
        await websocket.close(4002, "Invalid JSON")


async def main() -> None:
    async with websockets.serve(register_client, "localhost", 8765):
        logger.info("Server started on ws://localhost:8765")
        logger.info("Hermes Browser Extension Relay Server")
        logger.info("Waiting for connections...")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
