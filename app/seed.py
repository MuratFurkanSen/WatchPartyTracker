from sqlmodel import Session, select

from app.models import Country


COUNTRIES = [
    ("Argentina", "🇦🇷"),
    ("Australia", "🇦🇺"),
    ("Belgium", "🇧🇪"),
    ("Brazil", "🇧🇷"),
    ("Canada", "🇨🇦"),
    ("Croatia", "🇭🇷"),
    ("Denmark", "🇩🇰"),
    ("England", "🏴"),
    ("France", "🇫🇷"),
    ("Germany", "🇩🇪"),
    ("Italy", "🇮🇹"),
    ("Japan", "🇯🇵"),
    ("Mexico", "🇲🇽"),
    ("Morocco", "🇲🇦"),
    ("Netherlands", "🇳🇱"),
    ("Poland", "🇵🇱"),
    ("Portugal", "🇵🇹"),
    ("South Korea", "🇰🇷"),
    ("Spain", "🇪🇸"),
    ("Switzerland", "🇨🇭"),
    ("Turkey", "🇹🇷"),
    ("USA", "🇺🇸"),
]


def seed_countries(session: Session) -> None:
    existing_country = session.exec(select(Country)).first()
    if existing_country:
        return

    session.add_all(
        Country(name=name, flag_emoji=flag_emoji)
        for name, flag_emoji in COUNTRIES
    )
    session.commit()
