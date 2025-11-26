import asyncio

import aiohttp
from aiohttp import BasicAuth

from tmdb_service.globals import global_config, tmdb_logger


async def update_media_release_webhook_async(message: str) -> None:
    if not global_config.WEBHOOK_ENABLED:
        tmdb_logger.debug("Webhook is disabled, skipping notification.")
        return

    if (
        not global_config.WEBHOOK_URL
        or not global_config.WEBHOOK_BOT_USR
        or not global_config.WEBHOOK_BOT_PW
    ):
        tmdb_logger.error(
            "Webhook enabled but missing URL or credentials. "
            "Check WEBHOOK_URL, WEBHOOK_BOT_USR, and WEBHOOK_BOT_PW."
        )
        return

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
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        tmdb_logger.info(
                            f"Webhook sent successfully: {message[:100]}..."
                        )
                        return

                    tmdb_logger.warning(
                        f"Webhook failed with status {response.status} ({response.reason}). "
                        f"Response: {response_text[:200]}. Retry {retry_count + 1}/{MAX_RETRIES}"
                    )
        except aiohttp.ClientError as e:
            tmdb_logger.warning(
                f"ClientError while sending webhook: {e}. "
                f"Retry {retry_count + 1}/{MAX_RETRIES}"
            )
        except asyncio.TimeoutError:
            tmdb_logger.warning(
                f"Webhook request timed out. Retry {retry_count + 1}/{MAX_RETRIES}"
            )

        retry_count += 1
        if retry_count < MAX_RETRIES:
            await asyncio.sleep(2)  # Increased delay between retries

    tmdb_logger.error(
        f"Webhook failed after {MAX_RETRIES} retries. Message: {message[:100]}..."
    )


def update_media_release_webhook_sync(message: str) -> asyncio.Task | None:
    if not global_config.WEBHOOK_ENABLED:
        tmdb_logger.debug("Webhook is disabled, skipping notification.")
        return

    try:
        asyncio.get_running_loop()
        # if we're here, we're in an async context, execute the task
        return asyncio.create_task(update_media_release_webhook_async(message))
    except RuntimeError:
        # not in an async context, run the async function synchronously
        asyncio.run(update_media_release_webhook_async(message))
        return
