from datetime import date, datetime, time, timezone

from sqlalchemy import Column, String, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Country(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String(80), nullable=False, unique=True))
    flag_emoji: str = Field(sa_column=Column(String(8), nullable=False))


class Place(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(
        sa_column=Column(String(80, collation="NOCASE"), nullable=False, unique=True)
    )
    maps_url: str | None = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
    )
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    parties: list["Party"] = Relationship(back_populates="place")


class Party(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    country_a_id: int = Field(foreign_key="country.id", nullable=False)
    country_b_id: int = Field(foreign_key="country.id", nullable=False)
    place_id: int = Field(foreign_key="place.id", nullable=False)
    match_date: date = Field(nullable=False)
    start_time: time = Field(nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    country_a: Country | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Party.country_a_id"}
    )
    country_b: Country | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Party.country_b_id"}
    )
    place: Place | None = Relationship(back_populates="parties")
    attendees: list["Attendee"] = Relationship(
        back_populates="party",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Attendee(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "party_id",
            "normalized_name",
            name="uq_attendee_party_normalized_name",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    party_id: int = Field(foreign_key="party.id", nullable=False)
    name: str = Field(sa_column=Column(String(40), nullable=False))
    normalized_name: str = Field(sa_column=Column(String(40), nullable=False))
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    party: Party | None = Relationship(back_populates="attendees")
