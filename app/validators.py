from datetime import date, time


ATTENDEE_NAME_MAX_LENGTH = 40
PLACE_NAME_MAX_LENGTH = 80
MAPS_URL_MAX_LENGTH = 500


def collapse_spaces(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_name(value: str) -> str:
    return collapse_spaces(value).lower()


def validate_attendee_name(value: str) -> tuple[str, str]:
    cleaned = collapse_spaces(value)
    if not cleaned:
        raise ValueError("Name cannot be empty.")
    if len(cleaned) > ATTENDEE_NAME_MAX_LENGTH:
        raise ValueError("Name must be 40 characters or fewer.")

    normalized = normalize_name(cleaned)
    return cleaned, normalized


def validate_place_name(value: str) -> str:
    cleaned = collapse_spaces(value)
    if not cleaned:
        raise ValueError("Place name cannot be empty.")
    if len(cleaned) > PLACE_NAME_MAX_LENGTH:
        raise ValueError("Place name must be 80 characters or fewer.")
    return cleaned


def validate_maps_url(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > MAPS_URL_MAX_LENGTH:
        raise ValueError("Google Maps link must be 500 characters or fewer.")
    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        raise ValueError("Google Maps link must start with http:// or https://.")
    return cleaned


def parse_id(value: str, message: str) -> int:
    if not value:
        raise ValueError(message)

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(message) from exc


def parse_match_date(value: str) -> date:
    if not value:
        raise ValueError("Please choose a date.")

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Please choose a valid date.") from exc


def parse_start_time(value: str) -> time:
    if not value:
        raise ValueError("Please choose a start time.")

    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Please choose a valid start time.") from exc
