from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GitHubClient:
    def __init__(self) -> None:
        self._headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            self._headers["Authorization"] = f"Bearer {settings.github_token}"

    @property
    def enabled(self) -> bool:
        return bool(settings.github_token)

    async def recent_commits(self, owner: str, repo: str, limit: int = 5) -> list[dict]:
        if not self.enabled:
            return []
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        params = {"per_page": limit}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers=self._headers, params=params)
            if resp.status_code != 200:
                logger.warning("github_commits_failed", status=resp.status_code)
                return []
            commits = resp.json()
        return [
            {
                "sha": c["sha"][:7],
                "message": (c.get("commit") or {}).get("message", ""),
                "author": ((c.get("commit") or {}).get("author") or {}).get("name"),
                "date": ((c.get("commit") or {}).get("author") or {}).get("date"),
            }
            for c in commits
        ]

    async def recent_prs(self, owner: str, repo: str, limit: int = 5) -> list[dict]:
        if not self.enabled:
            return []
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        params = {"state": "all", "sort": "updated", "direction": "desc", "per_page": limit}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers=self._headers, params=params)
            if resp.status_code != 200:
                logger.warning("github_prs_failed", status=resp.status_code)
                return []
            prs = resp.json()
        return [
            {
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "user": (pr.get("user") or {}).get("login"),
                "updated_at": pr.get("updated_at"),
            }
            for pr in prs
            if pr.get("updated_at", "") >= since or True
        ][:limit]


github_client = GitHubClient()
