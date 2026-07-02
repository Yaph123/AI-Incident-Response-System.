import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SlackClient:
    async def post_message(self, channel: str, text: str) -> str | None:
        if settings.slack_webhook_url:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    settings.slack_webhook_url,
                    json={"text": text, "channel": channel},
                )
                resp.raise_for_status()
            logger.info("slack_webhook_sent", channel=channel)
            return "webhook"

        if settings.slack_bot_token:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
                    json={"channel": channel, "text": text},
                )
                resp.raise_for_status()
                data = resp.json()
                if not data.get("ok"):
                    raise RuntimeError(data.get("error", "slack_api_error"))
            logger.info("slack_api_sent", channel=channel)
            return data.get("ts")

        logger.warning("slack_not_configured", channel=channel, preview=text[:80])
        return None


slack_client = SlackClient()
