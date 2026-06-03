"""
Athlete Model manager — CRUD, versioning, auto-update from daily summaries.
The Athlete Model is a living JSON document injected into every LLM prompt.
"""
import copy
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Priority hierarchy for source resolution
SOURCE_PRIORITY = {
    "corrected_by_human": 5,
    "measured": 4,
    "reported": 3,
    "estimated": 2,
    "auto_extracted": 1,
}


def create_initial_model() -> dict:
    """Returns the initial empty Athlete Model structure."""
    return {
        "physique": {},
        "etat_actuel": {},
        "blessures": [],
        "patterns": [],
        "preferences": {},
        "objectifs": {
            "actuel": None,
            "jalons_atteints": [],
            "prochains_jalons": [],
        },
        "contradictions": [],
        "meta": {
            "derniere_mise_a_jour": datetime.now(timezone.utc).isoformat(),
            "nb_sessions_totales": 0,
            "date_premiere_session": datetime.now(timezone.utc).isoformat(),
            "version_modele": 1,
        },
    }


def get_priority_value(existing: dict, new: dict) -> dict:
    """
    Returns the value with highest priority source.
    Priority: corrected_by_human > measured > reported > estimated > auto_extracted
    """
    existing_source = existing.get("source", "auto_extracted")
    new_source = new.get("source", "auto_extracted")

    existing_priority = SOURCE_PRIORITY.get(existing_source, 0)
    new_priority = SOURCE_PRIORITY.get(new_source, 0)

    if new_priority > existing_priority:
        return new
    if new_priority < existing_priority:
        return existing
    # Same priority → keep the most recent
    return new if new.get("date", "") > existing.get("date", "") else existing


def merge_contradictions(
    contradictions: list,
    sujet: str,
    new_value: any,
    source: str,
    date_str: str,
) -> None:
    """
    Detects and records contradictions between different sources for the same field.
    """
    tag = f"{new_value} ({source}, {date_str})"

    for c in contradictions:
        if c["sujet"] == sujet:
            existing_tags = [v for v in c["valeurs"]]
            if tag not in existing_tags:
                c["valeurs"].append(tag)
                c["derniere_valeur_utilisee"] = tag
                c["resolution"] = (
                    "Valeur humaine prioritaire" if source == "corrected_by_human"
                    else None
                )
            return


async def update_model_from_summary(
    current_model: dict,
    daily_summary: dict,
) -> dict:
    """
    Updates the Athlete Model with new information from a daily summary.
    Returns the updated model.
    """
    model = copy.deepcopy(current_model)

    # Update meta
    model["meta"]["derniere_mise_a_jour"] = datetime.now(timezone.utc).isoformat()
    model["meta"]["version_modele"] += 1
    model["meta"]["nb_sessions_totales"] += 1

    # Merge metrics into physique
    for metric in daily_summary.get("metrics_extracted", []):
        name = metric["name"].lower().replace(" ", "_")
        if name in ("ftp_estimé", "ftp", "ftp_estime"):
            new_entry = {
                "value": metric["value"],
                "unit": metric.get("unit", "W"),
                "source": metric.get("confidence", "estimated"),
                "date": daily_summary["date"],
            }
            existing = model["physique"].get("ftp_estime")
            if existing and isinstance(existing, dict):
                chosen = get_priority_value(existing, new_entry)
                if chosen != existing:
                    merge_contradictions(
                        model["contradictions"], "FTP",
                        new_entry["value"], new_entry["source"], new_entry["date"],
                    )
                model["physique"]["ftp_estime"] = chosen
            else:
                model["physique"]["ftp_estime"] = new_entry

        elif name in ("fc_max", "fcmax", "fc_max_séance"):
            model["physique"]["fcmax"] = {
                "value": metric["value"],
                "unit": "bpm",
                "source": metric.get("confidence", "estimated"),
                "date": daily_summary["date"],
            }

    # Merge injuries
    for injury in daily_summary.get("injuries_reported", []):
        existing_injury = None
        for existing in model["blessures"]:
            if (existing.get("body_part") == injury.get("body_part") and
                    existing.get("type") == injury.get("type")):
                existing_injury = existing
                break

        if existing_injury:
            existing_injury["status"] = injury.get("status", "à surveiller")
            existing_injury["severity"] = injury.get("severity", existing_injury.get("severity"))
        else:
            model["blessures"].append({
                "type": f"{injury.get('type', 'douleur')} {injury.get('body_part', '')}",
                "date_signalement": daily_summary["date"],
                "statut": injury.get("status", "à surveiller"),
                "trigger": injury.get("trigger", ""),
                "severity": injury.get("severity", "légère"),
            })

    return model
