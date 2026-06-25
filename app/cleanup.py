from datetime import date

from sqlmodel import Session, select

from app.models import Attendee, Party


def cleanup_old_parties(session: Session) -> None:
    old_parties = session.exec(
        select(Party).where(Party.match_date < date.today())
    ).all()
    old_party_ids = [party.id for party in old_parties if party.id is not None]

    if not old_party_ids:
        return

    old_attendees = session.exec(
        select(Attendee).where(Attendee.party_id.in_(old_party_ids))
    ).all()
    for attendee in old_attendees:
        session.delete(attendee)

    for party in old_parties:
        session.delete(party)

    session.commit()
