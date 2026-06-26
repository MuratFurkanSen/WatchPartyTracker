from sqlmodel import Session, select

from app.models import Country

COUNTRIES = [
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
    existing_country = session.exec(select(Country)).first()
    if existing_country:
        return

    session.add_all(
        Country(name=name, flag_emoji=flag_emoji)
        for name, flag_emoji in COUNTRIES
    )
    session.commit()
