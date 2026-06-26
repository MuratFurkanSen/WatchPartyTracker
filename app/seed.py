from sqlmodel import Session, select

from app.models import Country
from app.twemoji import country_flag_emoji

COUNTRIES = [
    ("TBD", "❔"),
    ("Algeria", "🇩🇿"),
    ("Argentina", "🇦🇷"),
    ("Australia", "🇦🇺"),
    ("Austria", "🇦🇹"),
    ("Belgium", "🇧🇪"),
    ("Bosnia and Herzegovina", "🇧🇦"),
    ("Brazil", "🇧🇷"),
    ("Canada", "🇨🇦"),
    ("Cape Verde", "🇨🇻"),
    ("Colombia", "🇨🇴"),
    ("Croatia", "🇭🇷"),
    ("Curaçao", "🇨🇼"),
    ("Czechia", "🇨🇿"),
    ("DR Congo", "🇨🇩"),
    ("Ecuador", "🇪🇨"),
    ("Egypt", "🇪🇬"),
    ("England", "🏴"),
    ("France", "🇫🇷"),
    ("Germany", "🇩🇪"),
    ("Ghana", "🇬🇭"),
    ("Haiti", "🇭🇹"),
    ("Iran", "🇮🇷"),
    ("Iraq", "🇮🇶"),
    ("Ivory Coast", "🇨🇮"),
    ("Japan", "🇯🇵"),
    ("Jordan", "🇯🇴"),
    ("Mexico", "🇲🇽"),
    ("Morocco", "🇲🇦"),
    ("Netherlands", "🇳🇱"),
    ("New Zealand", "🇳🇿"),
    ("Norway", "🇳🇴"),
    ("Panama", "🇵🇦"),
    ("Paraguay", "🇵🇾"),
    ("Portugal", "🇵🇹"),
    ("Qatar", "🇶🇦"),
    ("Saudi Arabia", "🇸🇦"),
    ("Scotland", "🏴"),
    ("Senegal", "🇸🇳"),
    ("South Africa", "🇿🇦"),
    ("South Korea", "🇰🇷"),
    ("Spain", "🇪🇸"),
    ("Sweden", "🇸🇪"),
    ("Switzerland", "🇨🇭"),
    ("Tunisia", "🇹🇳"),
    ("Turkey", "🇹🇷"),
    ("United States", "🇺🇸"),
    ("Uruguay", "🇺🇾"),
    ("Uzbekistan", "🇺🇿"),
]


def seed_countries(session: Session) -> None:
    existing_countries = {
        country.name: country
        for country in session.exec(select(Country)).all()
    }
    changed = False

    for name, flag_emoji in COUNTRIES:
        stable_flag_emoji = country_flag_emoji(name, flag_emoji)
        country = existing_countries.get(name)

        if country is None:
            session.add(Country(name=name, flag_emoji=stable_flag_emoji))
            changed = True
        elif country.flag_emoji != stable_flag_emoji:
            country.flag_emoji = stable_flag_emoji
            changed = True

    if changed:
        session.commit()
