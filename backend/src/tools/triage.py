"""Track triage engine — production-style incident detection for SoundCloud catalogs.

Treats each track like a service: monitors health, detects anomalies,
assigns severity, and suggests remediation. This is the "Ops" in CybaOp.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel

from src.shared.logging import get_logger
from src.shared.models import TrackData

logger = get_logger("tools.triage")


class Severity(str, Enum):
    CRITICAL = "critical"  # Track is dying — needs immediate action
    WARNING = "warning"    # Degrading — should investigate
    INFO = "info"          # Notable but not urgent
    HEALTHY = "healthy"    # All good


class IncidentType(str, Enum):
    PLAY_DECAY = "play_decay"
    ENGAGEMENT_DROP = "engagement_drop"
    STALE_CATALOG = "stale_catalog"
    CONCENTRATION_RISK = "concentration_risk"
    UNDERPERFORMER = "underperformer"
    BREAKOUT = "breakout"
    SILENT_TRACK = "silent_track"


class Incident(BaseModel):
    """A single triage incident — like a PagerDuty alert for your music."""
    incident_type: IncidentType
    severity: Severity
    title: str
    detail: str
    track_id: str | None = None
    track_title: str | None = None
    metric_value: float = 0.0
    threshold: float = 0.0
    remediation: str = ""
    detected_at: datetime | None = None


class TriageReport(BaseModel):
    """Full triage report — catalog health at a glance."""
    overall_status: Severity
    incident_count: int = 0
    critical_count: int = 0
    warning_count: int = 0
    incidents: list[Incident] = []
    catalog_uptime: float = 0.0  # % of tracks "healthy"
    last_release_days_ago: int | None = None
    computed_at: datetime | None = None


def run_triage(
    tracks: list[TrackData],
    snapshots: list[dict[str, Any]] | None = None,
) -> TriageReport:
    """Run full triage on a catalog. Pure computation, no I/O."""
    now = datetime.now(timezone.utc)
    incidents: list[Incident] = []

    if not tracks:
        return TriageReport(
            overall_status=Severity.INFO,
            incidents=[Incident(
                incident_type=IncidentType.STALE_CATALOG,
                severity=Severity.INFO,
                title="Empty catalog",
                detail="No tracks found. Upload your first track to start monitoring.",
                remediation="Upload a track to SoundCloud and re-run analytics.",
            )],
            incident_count=1,
            computed_at=now,
        )

    # --- Catalog-level checks ---

    # Stale catalog: no release in 30+ days
    dated = [t for t in tracks if t.created_at]
    if dated:
        latest = max(t.created_at for t in dated)
        days_since = (now - latest).days if latest.tzinfo else (now.replace(tzinfo=None) - latest).days
        if days_since > 60:
            incidents.append(Incident(
                incident_type=IncidentType.STALE_CATALOG,
                severity=Severity.WARNING,
                title="Catalog going cold",
                detail=f"No new releases in {days_since} days. Algorithms deprioritize inactive accounts.",
                metric_value=float(days_since),
                threshold=60.0,
                remediation="Release new material or repost to signal activity. Even a short clip keeps the algorithm warm.",
                detected_at=now,
            ))
        last_release_days = days_since
    else:
        last_release_days = None

    # Concentration risk: top track has >60% of total plays
    total_plays = sum(t.play_count for t in tracks)
    if total_plays > 0 and len(tracks) > 1:
        top_track = max(tracks, key=lambda t: t.play_count)
        top_pct = top_track.play_count / total_plays
        if top_pct > 0.6:
            incidents.append(Incident(
                incident_type=IncidentType.CONCENTRATION_RISK,
                severity=Severity.WARNING if top_pct > 0.8 else Severity.INFO,
                title="Single point of failure",
                detail=f"'{top_track.title}' accounts for {top_pct:.0%} of all plays. If it stops performing, your whole catalog takes the hit.",
                track_id=top_track.platform_track_id,
                track_title=top_track.title,
                metric_value=top_pct,
                threshold=0.6,
                remediation="Diversify by promoting other tracks. Cross-link in descriptions. Create playlists that funnel listeners to your deeper catalog.",
                detected_at=now,
            ))

    # --- Per-track checks ---
    avg_engagement = 0.0
    engagement_rates: list[float] = []
    for t in tracks:
        if t.play_count > 0:
            er = (t.like_count + t.comment_count + t.repost_count) / t.play_count
            engagement_rates.append(er)
    if engagement_rates:
        avg_engagement = sum(engagement_rates) / len(engagement_rates)

    for track in tracks:
        if track.play_count == 0:
            # Silent track — has plays but zero engagement, or just no plays
            if track.created_at and (now - track.created_at).days > 7 if track.created_at.tzinfo else True:
                incidents.append(Incident(
                    incident_type=IncidentType.SILENT_TRACK,
                    severity=Severity.INFO,
                    title=f"Zero plays: {track.title}",
                    detail=f"'{track.title}' has 0 plays. It may not be discoverable.",
                    track_id=track.platform_track_id,
                    track_title=track.title,
                    remediation="Check visibility settings. Add tags and genre. Share on socials to seed initial plays.",
                    detected_at=now,
                ))
            continue

        er = (track.like_count + track.comment_count + track.repost_count) / track.play_count

        # Underperformer: engagement < 50% of catalog average
        if avg_engagement > 0 and er < avg_engagement * 0.5 and track.play_count > 100:
            incidents.append(Incident(
                incident_type=IncidentType.UNDERPERFORMER,
                severity=Severity.WARNING,
                title=f"Low engagement: {track.title}",
                detail=f"'{track.title}' has {er:.2%} engagement vs catalog avg of {avg_engagement:.2%}. People are hearing it but not engaging.",
                track_id=track.platform_track_id,
                track_title=track.title,
                metric_value=er,
                threshold=avg_engagement * 0.5,
                remediation="Check the first 30 seconds — that's where most listeners drop. Consider updating artwork, description, or tags.",
                detected_at=now,
            ))

        # Breakout: engagement > 2x catalog average
        if avg_engagement > 0 and er > avg_engagement * 2.0 and track.play_count > 50:
            incidents.append(Incident(
                incident_type=IncidentType.BREAKOUT,
                severity=Severity.INFO,
                title=f"Breakout track: {track.title}",
                detail=f"'{track.title}' has {er:.2%} engagement — {er / avg_engagement:.1f}x your average. This is resonating.",
                track_id=track.platform_track_id,
                track_title=track.title,
                metric_value=er,
                threshold=avg_engagement * 2.0,
                remediation="Double down. Promote this track. Pin it to your profile. Make more like it.",
                detected_at=now,
            ))

    # --- Snapshot-based checks (play decay) ---
    if snapshots and len(snapshots) >= 2:
        incidents.extend(_detect_play_decay(snapshots, now))

    # --- Compute overall status ---
    critical = sum(1 for i in incidents if i.severity == Severity.CRITICAL)
    warnings = sum(1 for i in incidents if i.severity == Severity.WARNING)

    if critical > 0:
        overall = Severity.CRITICAL
    elif warnings > 0:
        overall = Severity.WARNING
    elif incidents:
        overall = Severity.INFO
    else:
        overall = Severity.HEALTHY

    # Catalog uptime: % of tracks without incidents
    tracks_with_incidents = {i.track_id for i in incidents if i.track_id}
    healthy_count = len(tracks) - len(tracks_with_incidents)
    uptime = healthy_count / len(tracks) if tracks else 0.0

    # Sort: critical first, then warning, then info
    severity_order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2, Severity.HEALTHY: 3}
    incidents.sort(key=lambda i: severity_order.get(i.severity, 3))

    logger.info(
        "triage_complete",
        total_tracks=len(tracks),
        incidents=len(incidents),
        critical=critical,
        warnings=warnings,
        uptime=round(uptime, 2),
    )

    return TriageReport(
        overall_status=overall,
        incident_count=len(incidents),
        critical_count=critical,
        warning_count=warnings,
        incidents=incidents,
        catalog_uptime=round(uptime, 4),
        last_release_days_ago=last_release_days if dated else None,
        computed_at=now,
    )


def _detect_play_decay(
    snapshots: list[dict[str, Any]], now: datetime
) -> list[Incident]:
    """Detect tracks losing plays over time using snapshot history."""
    incidents: list[Incident] = []

    # Group snapshots by track
    by_track: dict[str, list[dict[str, Any]]] = {}
    for s in snapshots:
        tid = s.get("track_id", "")
        if tid:
            by_track.setdefault(tid, []).append(s)

    for track_id, snaps in by_track.items():
        if len(snaps) < 2:
            continue

        # Sort by date ascending
        snaps.sort(key=lambda s: s.get("captured_at", ""))
        first = snaps[0]
        last = snaps[-1]

        first_plays = first.get("play_count", 0)
        last_plays = last.get("play_count", 0)
        title = last.get("title", track_id)

        if first_plays == 0:
            continue

        # Play velocity: are daily plays declining?
        # Compare first half avg to second half avg
        mid = len(snaps) // 2
        if mid < 1:
            continue

        first_half_avg = sum(s.get("play_count", 0) for s in snaps[:mid]) / mid
        second_half_avg = sum(s.get("play_count", 0) for s in snaps[mid:]) / (len(snaps) - mid)

        if first_half_avg == 0:
            continue

        decay_rate = (first_half_avg - second_half_avg) / first_half_avg

        if decay_rate > 0.3:
            severity = Severity.CRITICAL if decay_rate > 0.5 else Severity.WARNING
            incidents.append(Incident(
                incident_type=IncidentType.PLAY_DECAY,
                severity=severity,
                title=f"Play decay: {title}",
                detail=f"'{title}' daily plays dropped {decay_rate:.0%}. Was averaging {first_half_avg:.0f}/day, now {second_half_avg:.0f}/day.",
                track_id=track_id,
                track_title=title,
                metric_value=decay_rate,
                threshold=0.3,
                remediation="Boost with a repost, share to socials, or add to a playlist. Consider a remix or visual to re-engage listeners.",
                detected_at=now,
            ))

    return incidents
