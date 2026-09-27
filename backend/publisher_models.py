"""Reviewed publisher evidence, not keyword guesses or provider moderation flags."""
import json
from pathlib import Path

AUDITED_MODELS = json.loads(Path(__file__).with_name('model_allowlist.json').read_text())


def publisher_evidence(model_id: str) -> dict | None:
    return AUDITED_MODELS.get(model_id)


def catalogue_evidence(item: dict) -> dict | None:
    evidence = publisher_evidence(item.get('id', ''))
    if not evidence or item.get('canonical_slug') != evidence['canonical_slug']:
        return None
    artifact = item.get('hugging_face_id')
    if not isinstance(artifact, str) or artifact.casefold() not in {value.casefold() for value in evidence['hugging_face_ids']}:
        return None
    return evidence


def verified_response_model(requested: str, reported) -> bool:
    evidence = publisher_evidence(requested)
    return bool(evidence and isinstance(reported, str) and reported.strip() in {requested, evidence['canonical_slug']})