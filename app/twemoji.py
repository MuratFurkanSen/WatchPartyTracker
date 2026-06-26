from typing import Protocol


TWEMOJI_BASE_URL = "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg"
SOCCER_BALL_CODEPOINT = "26bd"

COUNTRY_FLAG_EMOJI_OVERRIDES = {
    "England": "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F",
    "Scotland": "\U0001F3F4\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F",
}


class CountryLike(Protocol):
    name: str
    flag_emoji: str


def country_flag_emoji(name: str, fallback: str) -> str:
    return COUNTRY_FLAG_EMOJI_OVERRIDES.get(name, fallback)


def emoji_to_codepoint(value: str) -> str:
    return "-".join(f"{ord(character):x}" for character in value if ord(character) != 0xFE0F)


def twemoji_asset_url(codepoint: str) -> str:
    return f"{TWEMOJI_BASE_URL}/{codepoint}.svg"


def emoji_url(value: str) -> str:
    return twemoji_asset_url(emoji_to_codepoint(value))


def soccer_ball_url() -> str:
    return twemoji_asset_url(SOCCER_BALL_CODEPOINT)


def country_flag_url(country: CountryLike | None) -> str:
    if country is None:
        return ""

    flag_emoji = country_flag_emoji(country.name, country.flag_emoji)
    return emoji_url(flag_emoji)
