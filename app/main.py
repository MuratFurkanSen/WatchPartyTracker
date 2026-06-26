from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.cleanup import cleanup_old_parties
from app.database import create_db_and_tables, engine, get_session
from app.models import Attendee, Country, Party, Place
from app.seed import seed_countries
from app.twemoji import country_flag_url, soccer_ball_url
from app.validators import (
    parse_id,
    parse_match_date,
    parse_start_time,
    validate_attendee_name,
    validate_maps_url,
    validate_place_name,
)


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def format_match_date(value: date) -> str:
    return value.strftime("%a, %d %b")


def format_match_time(value: Any) -> str:
    return value.strftime("%H:%M")


templates.env.filters["match_date"] = format_match_date
templates.env.filters["match_time"] = format_match_time
templates.env.filters["country_flag_url"] = country_flag_url
templates.env.globals["soccer_ball_url"] = soccer_ball_url


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_countries(session)
    yield


app = FastAPI(title="World Cup Watch Parties", lifespan=lifespan)
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


def add_query_message(
    url: str,
    *,
    error: str | None = None,
    success: str | None = None,
) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))

    if error:
        query["error"] = error
        query.pop("success", None)
    elif success:
        query["success"] = success
        query.pop("error", None)

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        )
    )


def redirect(
    url: str,
    *,
    error: str | None = None,
    success: str | None = None,
) -> RedirectResponse:
    return RedirectResponse(
        add_query_message(url, error=error, success=success),
        status_code=303,
    )


def redirect_back(
    request: Request,
    fallback: str = "/",
    *,
    error: str | None = None,
    success: str | None = None,
) -> RedirectResponse:
    referrer = request.headers.get("referer")
    target = fallback

    if referrer:
        referrer_parts = urlsplit(referrer)
        request_host = request.url.netloc
        if not referrer_parts.netloc or referrer_parts.netloc == request_host:
            target = referrer

    return redirect(target, error=error, success=success)


def template_context(
    request: Request,
    *,
    title: str | None = None,
    error: str | None = None,
    success: str | None = None,
) -> dict[str, Any]:
    return {
        "request": request,
        "title": title,
        "error": error or request.query_params.get("error"),
        "success": success or request.query_params.get("success"),
    }


def load_countries(session: Session) -> list[Country]:
    return session.exec(select(Country).order_by(Country.name)).all()


def load_places(session: Session) -> list[Place]:
    return session.exec(select(Place).order_by(Place.name)).all()


def party_query():
    return select(Party).options(
        selectinload(Party.country_a),
        selectinload(Party.country_b),
        selectinload(Party.place),
        selectinload(Party.attendees),
    )


def sort_party_attendees(party: Party) -> Party:
    party.attendees.sort(key=lambda attendee: attendee.created_at)
    return party


def load_upcoming_parties(session: Session) -> list[Party]:
    parties = session.exec(
        party_query()
        .where(Party.match_date >= date.today())
        .order_by(Party.match_date, Party.start_time)
    ).all()
    return [sort_party_attendees(party) for party in parties]


def load_party(session: Session, party_id: int) -> Party | None:
    party = session.exec(party_query().where(Party.id == party_id)).first()
    if party:
        sort_party_attendees(party)
    return party


def render_new_party(
    request: Request,
    session: Session,
    *,
    error: str | None = None,
    form: dict[str, str] | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    context = template_context(
        request,
        title="Create Party",
        error=error,
    )
    context.update(
        {
            "countries": load_countries(session),
            "places": load_places(session),
            "form": form or {},
        }
    )
    return templates.TemplateResponse(
        request,
        "party_new.html",
        context,
        status_code=status_code,
    )


def render_places(
    request: Request,
    session: Session,
    *,
    error: str | None = None,
    form: dict[str, str] | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    context = template_context(
        request,
        title="Places",
        error=error,
    )
    context.update(
        {
            "places": load_places(session),
            "form": form or {},
        }
    )
    return templates.TemplateResponse(
        request,
        "places.html",
        context,
        status_code=status_code,
    )


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request, session: Session = Depends(get_session)):
    cleanup_old_parties(session)
    context = template_context(request)
    context["parties"] = load_upcoming_parties(session)
    return templates.TemplateResponse(request, "index.html", context)


@app.get("/parties/new", response_class=HTMLResponse)
def new_party(request: Request, session: Session = Depends(get_session)):
    cleanup_old_parties(session)
    return render_new_party(request, session)


@app.post("/parties")
def create_party(
    request: Request,
    country_a_id: str = Form(""),
    country_b_id: str = Form(""),
    match_date: str = Form(""),
    start_time: str = Form(""),
    place_id: str = Form(""),
    session: Session = Depends(get_session),
):
    cleanup_old_parties(session)
    form = {
        "country_a_id": country_a_id,
        "country_b_id": country_b_id,
        "match_date": match_date,
        "start_time": start_time,
        "place_id": place_id,
    }

    try:
        parsed_country_a_id = parse_id(country_a_id, "Choose the first country.")
        parsed_country_b_id = parse_id(country_b_id, "Choose the second country.")
        parsed_place_id = parse_id(place_id, "Please select a place.")
        parsed_match_date = parse_match_date(match_date)
        parsed_start_time = parse_start_time(start_time)

        if parsed_country_a_id == parsed_country_b_id:
            raise ValueError("Choose two different countries.")

        country_a = session.get(Country, parsed_country_a_id)
        country_b = session.get(Country, parsed_country_b_id)
        place = session.get(Place, parsed_place_id)

        if not country_a or not country_b:
            raise ValueError("Choose two valid countries.")
        if not place:
            raise ValueError("Please select a place.")
    except ValueError as exc:
        return render_new_party(
            request,
            session,
            error=str(exc),
            form=form,
            status_code=400,
        )

    party = Party(
        country_a_id=parsed_country_a_id,
        country_b_id=parsed_country_b_id,
        place_id=parsed_place_id,
        match_date=parsed_match_date,
        start_time=parsed_start_time,
    )
    session.add(party)
    session.commit()

    return redirect("/", success="Watch party created.")


@app.get("/parties/{party_id}", response_class=HTMLResponse)
def party_detail(
    party_id: int,
    request: Request,
    session: Session = Depends(get_session),
):
    cleanup_old_parties(session)
    party = load_party(session, party_id)
    if not party:
        return redirect("/", error="Watch party not found.")

    context = template_context(request, title="Watch Party")
    context["party"] = party
    return templates.TemplateResponse(request, "party_detail.html", context)


@app.post("/parties/{party_id}/join")
def join_party(
    party_id: int,
    request: Request,
    name: str = Form(""),
    session: Session = Depends(get_session),
):
    cleanup_old_parties(session)
    party = session.get(Party, party_id)
    if not party:
        return redirect_back(request, error="Watch party not found.")

    try:
        cleaned_name, normalized_name = validate_attendee_name(name)
    except ValueError as exc:
        return redirect_back(request, error=str(exc))

    duplicate = session.exec(
        select(Attendee).where(
            Attendee.party_id == party_id,
            Attendee.normalized_name == normalized_name,
        )
    ).first()
    if duplicate:
        return redirect_back(request, error="This name is already on the list.")

    attendee = Attendee(
        party_id=party_id,
        name=cleaned_name,
        normalized_name=normalized_name,
    )
    session.add(attendee)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return redirect_back(request, error="This name is already on the list.")

    return redirect_back(request, success="Name added.")


@app.post("/attendees/{attendee_id}/delete")
def delete_attendee(
    attendee_id: int,
    request: Request,
    session: Session = Depends(get_session),
):
    cleanup_old_parties(session)
    attendee = session.get(Attendee, attendee_id)
    if attendee:
        session.delete(attendee)
        session.commit()

    return redirect_back(request)


@app.get("/places", response_class=HTMLResponse)
def places(request: Request, session: Session = Depends(get_session)):
    cleanup_old_parties(session)
    return render_places(request, session)


@app.post("/places")
def add_place(
    request: Request,
    name: str = Form(""),
    maps_url: str = Form(""),
    session: Session = Depends(get_session),
):
    cleanup_old_parties(session)
    form = {"name": name, "maps_url": maps_url}

    try:
        cleaned_name = validate_place_name(name)
        cleaned_maps_url = validate_maps_url(maps_url)
    except ValueError as exc:
        return render_places(
            request,
            session,
            error=str(exc),
            form=form,
            status_code=400,
        )

    duplicate = session.exec(
        select(Place).where(func.lower(Place.name) == cleaned_name.lower())
    ).first()
    if duplicate:
        return render_places(
            request,
            session,
            error="This place already exists.",
            form=form,
            status_code=400,
        )

    place = Place(name=cleaned_name, maps_url=cleaned_maps_url)
    session.add(place)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return render_places(
            request,
            session,
            error="This place already exists.",
            form=form,
            status_code=400,
        )

    return redirect("/places", success="Place added.")


@app.post("/places/{place_id}/delete")
def delete_place(
    place_id: int,
    request: Request,
    session: Session = Depends(get_session),
):
    cleanup_old_parties(session)
    place = session.get(Place, place_id)
    if not place:
        return redirect("/places", error="Place not found.")

    used_by_upcoming_party = session.exec(
        select(Party).where(
            Party.place_id == place_id,
            Party.match_date >= date.today(),
        )
    ).first()
    if used_by_upcoming_party:
        return redirect(
            "/places",
            error="This place is used by an upcoming party. Delete is not allowed yet.",
        )

    session.delete(place)
    session.commit()
    return redirect("/places", success="Place deleted.")
