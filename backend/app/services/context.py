from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.github import github_client
from app.models import EvidenceItem, Incident, Runbook
from app.models.enums import EventType, EvidenceSource
from app.services.common import log_event

logger = get_logger(__name__)


def _parse_github_repo(repo: str | None) -> tuple[str, str] | None:
    if not repo:
        return None
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return owner, name
    if settings.github_default_owner and settings.github_default_repo:
        return settings.github_default_owner, settings.github_default_repo
    return None


async def fetch_github_context(db: Session, incident: Incident) -> list[EvidenceItem]:
    repo_ref = incident.service.github_repo if incident.service else None
    parsed = _parse_github_repo(repo_ref)
    if not parsed:
        logger.info("github_context_skipped", incident_id=str(incident.id))
        return []

    owner, repo = parsed
    commits = await github_client.recent_commits(owner, repo)
    prs = await github_client.recent_prs(owner, repo)
    items: list[EvidenceItem] = []

    for commit in commits:
        item = EvidenceItem(
            incident_id=incident.id,
            source=EvidenceSource.GITHUB,
            title=f"Commit {commit['sha']}",
            content=commit["message"],
            metadata_={"type": "commit", **commit},
        )
        db.add(item)
        items.append(item)

    for pr in prs:
        item = EvidenceItem(
            incident_id=incident.id,
            source=EvidenceSource.GITHUB,
            title=f"PR #{pr['number']}: {pr['title']}",
            content=f"State: {pr['state']} by {pr.get('user')}",
            metadata_={"type": "pull_request", **pr},
        )
        db.add(item)
        items.append(item)

    log_event(
        db,
        incident.id,
        EventType.GITHUB_CONTEXT,
        f"Fetched GitHub context ({len(items)} items)",
        {"owner": owner, "repo": repo},
    )
    db.commit()
    return items


def search_runbooks(db: Session, query: str, limit: int = 3) -> list[Runbook]:
    q = db.query(Runbook)
    if query.strip():
        pattern = f"%{query.strip()}%"
        q = q.filter((Runbook.title.ilike(pattern)) | (Runbook.content.ilike(pattern)))
    return q.order_by(Runbook.updated_at.desc()).limit(limit).all()
