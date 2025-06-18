import asyncio

import aiohttp
from aiohttp import BasicAuth

from tmdb_service.globals import global_config, tmdb_logger


async def update_media_release_webhook_async(message: str) -> None:
    if not global_config.WEBHOOK_ENABLED:
        return

    if (
        not global_config.WEBHOOK_URL
        or not global_config.WEBHOOK_BOT_USR
        or not global_config.WEBHOOK_BOT_PW
    ):
        tmdb_logger.error(
            "Attempted to execute the webhook with missing URL or credentials."
        )
        raise ValueError("Missing webhook URL or credentials.")

    retry_count = 0
    MAX_RETRIES = 6
    headers = {"Content-Type": "application/json"}
    auth = BasicAuth(global_config.WEBHOOK_BOT_USR, global_config.WEBHOOK_BOT_PW)
    data = {"content": message}

    while retry_count < MAX_RETRIES:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    global_config.WEBHOOK_URL,
                    json=data,
                    headers=headers,
                    auth=auth,
                ) as response:
                    if response.status == 200:
                        tmdb_logger.debug(f"Webhook sent successfully ({message}).")
                        return
                    tmdb_logger.warning(
                        f"Failed to send webhook: {response.status} ({response.reason}). Trying again..."
                    )
        except aiohttp.ClientError as e:
            tmdb_logger.warning(f"ClientError while sending webhook: {e}. Retrying...")

        retry_count += 1
        await asyncio.sleep(1)

    tmdb_logger.warning(f"Webhook failed after {MAX_RETRIES} retries")


def update_media_release_webhook_sync(message: str) -> asyncio.Task | None:
    if not global_config.WEBHOOK_ENABLED:
        return

    try:
        asyncio.get_running_loop()
        # if we're here, we're in an async context, execute the task
        return asyncio.create_task(update_media_release_webhook_async(message))
    except RuntimeError:
        # not in an async context, run the async function synchronously
        return asyncio.run(update_media_release_webhook_async(message))
