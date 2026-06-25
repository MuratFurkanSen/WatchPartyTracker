# World Cup Watch Party Board — Implementation Guideline

## 1. Project Goal

Build a very simple public website for organizing World Cup match watch parties.

The website allows people to:

1. View upcoming watch parties.
2. Create a watch party between two countries.
3. Select the watch party place from a predefined dropdown.
4. Add their name to a watch party.
5. Remove names freely.
6. Add/delete places from a separate places page.
7. Open an optional Google Maps directions link for a place.

The two highest priorities are:

- Ease of use
- Almost zero maintenance
- Mobile and desktop compatibility

The app must work well on both mobile and desktop.

Do not over-engineer this. No login, no admin users, no OAuth, no React, no permissions system, no complex dashboard.

---

## 2. Final Scope

### Included

- Public homepage with all upcoming watch parties.
- Public party creation page.
- Public places management page.
- Country dropdowns using a predefined country list.
- Place dropdown using places stored in the database.
- Optional Google Maps URL per place.
- Join party by typing a name.
- Remove attendee names freely.
- Delete places only if they are not used by any upcoming party.
- Automatically delete old parties after their match date has passed.
- Fully responsive mobile/desktop UI.
- SQLite database.
- Server-rendered HTML using Jinja2.
- FastAPI backend.
- Plain CSS.

### Not Included

Do not add these:

- Login
- User accounts
- Admin PIN
- Roles/permissions
- Edit party
- Edit place
- Comments/chat
- “Maybe coming” status
- Email notifications
- Match API integration
- React/Vue/Svelte
- Complex admin panel
- QR codes
- Image uploads
- Embedded Google Maps
- Public API unless needed internally

This should remain a tiny shared bulletin board.

---

## 3. Recommended Tech Stack

Use:

```text
FastAPI
Jinja2
SQLite
SQLModel
Plain CSS
Uvicorn
```

Recommended Python packages:

```text
fastapi
uvicorn
jinja2
sqlmodel
python-multipart
```

Optional but not required:

```text
httpx
```

Do not use React. Do not use a SPA. Server-rendered pages are enough and easier to maintain.

---

## 4. Suggested Project Structure

```text
watch-party-board/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── seed.py
│   ├── cleanup.py
│   ├── validators.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── party_new.html
│   │   ├── party_detail.html
│   │   └── places.html
│   └── static/
│       └── styles.css
├── data/
│   └── app.db
├── requirements.txt
└── README.md
```

Keep the structure small. Do not split into many layers unless needed.

---

## 5. Database Models

Use SQLModel.

There are only four main tables:

1. `Country`
2. `Place`
3. `Party`
4. `Attendee`

---

### 5.1 Country

Countries are predefined and seeded automatically.

Fields:

```text
id: int primary key
name: str unique
flag_emoji: str
```

Example values:

```text
Turkey 🇹🇷
Germany 🇩🇪
France 🇫🇷
Brazil 🇧🇷
Argentina 🇦🇷
Portugal 🇵🇹
Spain 🇪🇸
England 🏴
Netherlands 🇳🇱
Italy 🇮🇹
Croatia 🇭🇷
Belgium 🇧🇪
Morocco 🇲🇦
Japan 🇯🇵
South Korea 🇰🇷
USA 🇺🇸
Mexico 🇲🇽
```

The exact list can be expanded later in the seed file.

Important:

- Countries should not be user-editable from the UI.
- Country dropdowns should show flag + name.

---

### 5.2 Place

Fields:

```text
id: int primary key
name: str unique
maps_url: str | null
created_at: datetime
```

Rules:

- Place name is required.
- Google Maps URL is optional.
- Place names should be unique case-insensitively.
- Do not allow empty names.
- Trim whitespace.
- Do not implement edit.
- If a place is wrong, user deletes it and adds a new one.
- Places can only be deleted if not used by upcoming parties.

Example:

```text
Irish Pub
Wohnheim Lounge
Mensa Area
Friend's Kitchen
```

---

### 5.3 Party

Fields:

```text
id: int primary key
country_a_id: foreign key Country.id
country_b_id: foreign key Country.id
place_id: foreign key Place.id
match_date: date
start_time: time
created_at: datetime
```

Relationships:

```text
country_a -> Country
country_b -> Country
place -> Place
attendees -> list[Attendee]
```

Rules:

- Country A is required.
- Country B is required.
- Country A and Country B cannot be the same.
- Place is required.
- Date is required.
- Start time is required.
- Old parties are deleted automatically once `match_date < today`.

Do not add editing.

---

### 5.4 Attendee

Fields:

```text
id: int primary key
party_id: foreign key Party.id
name: str
normalized_name: str
created_at: datetime
```

Rules:

- Name is required.
- Name is trimmed.
- Empty names are rejected.
- Duplicate names within the same party are rejected.
- Duplicate detection should use `normalized_name`.
- Names can be removed freely by anyone.

Normalization:

```text
trim leading/trailing whitespace
collapse repeated spaces
lowercase
```

Examples:

```text
" Murat " -> "murat"
"MURAT" -> "murat"
"Murat   Furkan" -> "murat furkan"
```

---

## 6. Cascading Deletes

When deleting a party, delete its attendees too.

This is important for cleanup.

Expected behavior:

```text
delete old party -> attendees for that party also disappear
```

Do not leave orphan attendee records.

---

## 7. Automatic Cleanup of Old Parties

Old parties should be deleted automatically after their match day.

Definition:

```text
If party.match_date < today, delete it.
```

Example:

```text
Match date: 2026-06-26
Visible during: 2026-06-26
Deleted/hidden from: 2026-06-27
```

The simplest implementation:

Run cleanup at the beginning of these routes:

```text
GET /
GET /parties/new
GET /places
```

At minimum, run it on homepage load.

This avoids needing cron, systemd timers, background workers, Celery, APScheduler, or other maintenance goblins.

Pseudo-logic:

```python
def cleanup_old_parties(session):
    today = date.today()
    old_parties = session.exec(
        select(Party).where(Party.match_date < today)
    ).all()

    for party in old_parties:
        session.delete(party)

    session.commit()
```

Make sure attendee records are deleted too, either through relationship cascade handling or explicit deletion.

---

## 8. Routes

Keep routes minimal.

### 8.1 Homepage

```text
GET /
```

Purpose:

- Run cleanup for old parties.
- Show all current/future parties.
- Sort by date and time ascending.
- Show cards.

Data required per card:

```text
party id
country A name + flag
country B name + flag
match date
start time
place name
place maps URL if available
attendee names
attendee ids for delete buttons
```

---

### 8.2 New Party Form

```text
GET /parties/new
```

Purpose:

- Show create party form.
- Load all countries.
- Load all places.
- If there are no places, show a helpful message and link to places page.

Important UX:

If no places exist, do not show a broken form. Show:

```text
No places yet. Add a place first.
[Go to Places]
```

---

### 8.3 Create Party

```text
POST /parties
```

Form fields:

```text
country_a_id
country_b_id
match_date
start_time
place_id
```

Validation:

- All fields required.
- Countries must exist.
- Place must exist.
- Countries cannot be same.
- Date must parse.
- Time must parse.

After successful creation:

```text
Redirect to /
```

or optionally:

```text
Redirect to /parties/{id}
```

Recommended:

```text
Redirect to /
```

because the homepage is the main board.

---

### 8.4 Party Detail Page

```text
GET /parties/{party_id}
```

Optional but recommended.

Purpose:

- Show a single party card.
- Useful for WhatsApp sharing.
- Same join/remove functionality as homepage.

If party not found:

- Show 404 page or redirect to homepage with message.

This route is useful because someone can send:

```text
https://domain.com/parties/12
```

in WhatsApp.

---

### 8.5 Join Party

```text
POST /parties/{party_id}/join
```

Form fields:

```text
name
```

Validation:

- Party must exist.
- Name cannot be empty.
- Normalized name must not already exist for this party.

On success:

- Add attendee.
- Redirect back to referrer if available.
- Otherwise redirect to homepage.

Duplicate name message:

```text
This name is already on the list.
```

For simplicity, error messages can be shown through query parameters or server-side template context.

Do not add JavaScript-heavy behavior.

---

### 8.6 Delete Attendee

```text
POST /attendees/{attendee_id}/delete
```

Purpose:

- Remove one attendee name freely.

Rules:

- Anyone can delete any attendee name.
- No confirmation required on backend.
- Frontend may use a simple browser confirm.

After deletion:

- Redirect back to referrer if available.
- Otherwise redirect to homepage.

---

### 8.7 Places Page

```text
GET /places
```

Purpose:

- Show add-place form.
- Show current places.
- Each place shows:
  - name
  - optional directions link
  - delete button

---

### 8.8 Add Place

```text
POST /places
```

Form fields:

```text
name
maps_url optional
```

Validation:

- Name required.
- Trim whitespace.
- Reject duplicate names case-insensitively.
- If maps URL is provided, trim it.
- Optional: validate that URL starts with `http://` or `https://`.

Recommended behavior:

- If maps URL does not start with `http://` or `https://`, reject it.
- Do not try to auto-fix URLs.

Success:

```text
Redirect to /places
```

---

### 8.9 Delete Place

```text
POST /places/{place_id}/delete
```

Rules:

- Place must exist.
- If any current/future party uses this place, reject deletion.
- If no current/future party uses this place, delete it.

Important:

Since old parties are cleaned automatically, only check current/future parties.

Pseudo-logic:

```python
today = date.today()

used = session.exec(
    select(Party).where(
        Party.place_id == place_id,
        Party.match_date >= today
    )
).first()

if used:
    reject deletion
else:
    delete place
```

Error message:

```text
This place is used by an upcoming party. Delete is not allowed yet.
```

Do not cascade delete parties when deleting places. That is dangerous and too easy to misuse.

---

## 9. UI Pages

There are three main pages:

1. Homepage
2. Create Party
3. Places

Optional:

4. Party Detail

---

## 10. Base Layout

All pages should use `base.html`.

Base layout should include:

```text
doctype
html lang="en"
head
viewport meta tag
title
stylesheet link
body
header/nav
main container
footer optional
```

Required viewport tag:

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

Navigation:

```text
World Cup Watch Parties ⚽

[Parties] [Create Party] [Places]
```

On mobile, nav should wrap naturally. Do not build a hamburger menu.

---

## 11. Homepage UI

### Header

Text:

```text
World Cup Watch Parties ⚽
Pick a match, add your name, show up.
```

Buttons:

```text
Create Party
Places
```

### Empty State

If no parties exist:

```text
No watch parties yet ⚽
Create the first one and make WhatsApp slightly less cursed.

[Create Party]
```

### Party Card

Each card should show:

```text
🇹🇷 Turkey
vs
🇵🇹 Portugal

Fri, 26 Jun · 21:00
📍 Irish Pub
Directions

Coming 4
[Murat ×] [Ali ×] [Zeynep ×]

Your name
[__________]
[I'm coming]
```

Design rules:

- Use cards.
- Use flag emojis.
- Keep text large enough for mobile.
- Attendee names should be chips.
- Delete name button should be inside or next to the chip.
- Join form should be inside the card.

Desktop:

- Cards in responsive grid.
- Multiple cards per row if space allows.

Mobile:

- Cards full width.
- Input and join button stacked.

---

## 12. Create Party Page UI

Use a single centered form card.

Fields:

```text
Country 1
[dropdown]

Country 2
[dropdown]

Date
[date input]

Start time
[time input]

Place
[dropdown]

[Create Party]
```

Rules:

- Labels must be visible above inputs.
- Do not rely only on placeholder text.
- Submit button full width on mobile.
- If there are no places, show message and link to `/places`.

Do not allow adding places from this page.

---

## 13. Places Page UI

Use a single page with two sections.

### Add Place Section

```text
Add Place

Place name
[__________]

Google Maps link optional
[__________]

[Add Place]
```

### Existing Places Section

Each place row:

```text
Irish Pub
Directions
[Delete]
```

If no maps URL exists:

```text
Wohnheim Lounge
[Delete]
```

Rules:

- No edit button.
- Delete button should be visible but not massive.
- Use a simple browser confirm on delete:

```html
onclick="return confirm('Delete this place?')"
```

If delete fails because the place is in use, show an error message.

---

## 14. Color Palette

Use a dark “stadium night” palette.

```text
Background:        #0B1020
Surface/Card:      #151B2E
Surface hover:     #1D2540

Primary green:     #22C55E
Primary hover:     #16A34A

Accent gold:       #FACC15
Danger red:        #EF4444

Text main:         #F8FAFC
Text muted:        #94A3B8
Border:            #2A3554
Input background:  #0F172A
```

CSS variables:

```css
:root {
  --bg: #0B1020;
  --surface: #151B2E;
  --surface-hover: #1D2540;

  --primary: #22C55E;
  --primary-hover: #16A34A;

  --accent: #FACC15;
  --danger: #EF4444;

  --text: #F8FAFC;
  --muted: #94A3B8;
  --border: #2A3554;
  --input-bg: #0F172A;

  --radius-md: 0.75rem;
  --radius-lg: 1.25rem;

  --space-xs: 0.35rem;
  --space-sm: 0.6rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
}
```

---

## 15. CSS Layout Requirements

Use mobile-first CSS.

### Global

```css
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
```

### Main Container

```css
.container {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: var(--space-md);
}
```

### Responsive Card Grid

```css
.party-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-md);
}

@media (min-width: 720px) {
  .party-grid {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  }
}
```

### Cards

```css
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
}

@media (hover: hover) {
  .card {
    transition: border-color 0.15s ease, transform 0.15s ease;
  }

  .card:hover {
    border-color: rgba(34, 197, 94, 0.45);
    transform: translateY(-2px);
  }
}
```

### Forms

```css
.form-card {
  max-width: 520px;
  margin: 0 auto;
}

.form-group {
  display: grid;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
}

label {
  font-weight: 700;
}

input,
select {
  width: 100%;
  background: var(--input-bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0.75rem 0.9rem;
  font: inherit;
}

input:focus,
select:focus {
  outline: 2px solid var(--primary);
  border-color: var(--primary);
}
```

### Buttons

```css
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem;
  font: inherit;
  font-weight: 800;
  text-decoration: none;
  border: 1px solid transparent;
  cursor: pointer;
}

.button-primary {
  background: var(--primary);
  color: #04130A;
}

.button-primary:hover {
  background: var(--primary-hover);
}

.button-secondary {
  background: transparent;
  color: var(--text);
  border-color: var(--border);
}

.button-danger {
  background: transparent;
  color: var(--danger);
  border-color: rgba(239, 68, 68, 0.35);
}
```

On mobile, form buttons can be full width:

```css
.form-card .button {
  width: 100%;
}
```

### Attendee Chips

```css
.attendee-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.attendee-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  background: var(--surface-hover);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.35rem 0.6rem;
}

.attendee-delete {
  border: 0;
  background: transparent;
  color: var(--danger);
  cursor: pointer;
  font-weight: 900;
  padding: 0.1rem 0.25rem;
}
```

---

## 16. UX Rules

The app should be understandable in under 10 seconds.

Important UX rules:

1. Homepage is the main page.
2. Create Party and Places should be one click away.
3. No hidden menus.
4. No modal-heavy UI.
5. No tiny tap targets.
6. Use normal HTML forms.
7. Use clear error messages.
8. Use dropdowns for countries and places.
9. Do not allow free-text places while creating parties.
10. Keep all forms short.

---

## 17. Validation Rules

### Party Creation

Reject if:

```text
country_a_id missing
country_b_id missing
country_a_id == country_b_id
place_id missing
match_date missing
start_time missing
country does not exist
place does not exist
```

Message examples:

```text
Choose two different countries.
Please select a place.
Please choose a date.
Please choose a start time.
```

### Add Place

Reject if:

```text
name empty after trimming
duplicate place name case-insensitively
maps_url provided but not starting with http:// or https://
```

Message examples:

```text
Place name cannot be empty.
This place already exists.
Google Maps link must start with http:// or https://.
```

### Join Party

Reject if:

```text
party does not exist
name empty after trimming
normalized name already exists for the party
```

Message examples:

```text
Name cannot be empty.
This name is already on the list.
```

---

## 18. Error/Success Messaging

Use simple flash-style messages.

Possible implementation options:

1. Query parameters, e.g. `?error=...`
2. Session-based flash messages
3. Server-side context after failed validation

Simplest acceptable approach:

- On validation error, re-render the same template with an error string.
- On success, redirect.

For POST redirects, use status code:

```text
303 See Other
```

Example:

```python
return RedirectResponse("/", status_code=303)
```

Visual styles:

```css
.alert {
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
}

.alert-error {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.35);
  color: #FCA5A5;
}

.alert-success {
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.35);
  color: #BBF7D0;
}
```

---

## 19. Date and Time Display

Store:

```text
match_date as date
start_time as time
```

Display format:

```text
Fri, 26 Jun · 21:00
```

Keep it simple.

Timezone handling:

- Do not build complex timezone logic.
- The app is for local friend-group use.
- Use server local date for cleanup.
- Date/time input is interpreted as local event date/time.

---

## 20. Country Seed Data

Create a seed function that runs on app startup.

Requirements:

- Create database tables.
- Insert countries if table is empty.
- Optionally insert a few default places if places table is empty.

Example countries:

```python
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
```

Default places are optional. If added, keep them generic:

```python
DEFAULT_PLACES = [
    ("Wohnheim Lounge", None),
    ("Irish Pub", None),
]
```

---

## 21. Maintainability Rules

Follow these rules strictly:

1. Keep route handlers small.
2. Put database models in `models.py`.
3. Put database/session setup in `database.py`.
4. Put cleanup logic in `cleanup.py`.
5. Put normalization/validation helpers in `validators.py`.
6. Do not introduce a service layer unless the file gets genuinely messy.
7. Do not create frontend build tooling.
8. Do not add JavaScript unless absolutely necessary.
9. Prefer HTML form behavior over custom JS.
10. Do not add dependencies without a clear reason.

This project should remain easy to understand by opening `main.py`.

---

## 22. Security Expectations

This is a public no-login app.

Accepted tradeoffs:

- Anyone with the URL can create parties.
- Anyone with the URL can join.
- Anyone with the URL can remove names.
- Anyone with the URL can add places.
- Anyone with the URL can delete unused places.

Do not add authentication.

Basic safety still required:

- Escape all user-provided text in templates.
- Jinja2 escapes by default; do not disable escaping.
- Validate URLs.
- Do not render raw HTML from users.
- Limit input lengths.

Recommended limits:

```text
attendee name max length: 40 chars
place name max length: 80 chars
maps_url max length: 500 chars
```

If exceeded, reject.

---

## 23. Input Length Limits

Use conservative length limits:

```text
Place.name: 80
Place.maps_url: 500
Attendee.name: 40
Attendee.normalized_name: 40
Country.name: 80
Country.flag_emoji: 8
```

Reasons:

- Prevent ugly UI.
- Prevent accidental spam.
- Keep database clean.
- Avoid cursed 400-character attendee names.

---

## 24. Deletion Behavior

### Attendee Deletion

Anyone can delete any attendee.

Frontend:

```html
<button onclick="return confirm('Remove this name?')">×</button>
```

Backend:

- Delete attendee if exists.
- Redirect back.

If attendee does not exist:

- Redirect back gracefully.
- Do not crash.

### Place Deletion

Anyone can delete an unused place.

Frontend:

```html
<button onclick="return confirm('Delete this place?')">Delete</button>
```

Backend:

- Check if place exists.
- Check if used by current/future parties.
- If used, reject with error.
- If unused, delete.

Do not delete parties automatically when deleting places.

---

## 25. Accessibility Basics

Do at least this:

- Use real `<button>` elements for actions.
- Use real `<label>` elements for form fields.
- Inputs must have associated labels.
- Links should have meaningful text.
- Do not use color alone for important information.
- Buttons should be large enough for mobile tapping.
- Use good contrast.

Directions link text should be:

```text
Directions
```

not just an icon.

---

## 26. Mobile/Desktop Compatibility

Mobile-first requirements:

- Page container has side padding.
- Cards are full-width on small screens.
- Forms are single-column.
- Buttons inside forms are full-width on mobile.
- Attendee chips wrap.
- Navigation wraps instead of overflowing.
- No horizontal scrolling.

Desktop requirements:

- Cards use responsive grid.
- Container max width around `1100px`.
- Form cards stay narrow, around `520px`.
- Content does not stretch awkwardly across entire screen.

---

## 27. HTML Template Expectations

### `base.html`

Contains:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title or "World Cup Watch Parties" }}</title>
  <link rel="stylesheet" href="{{ url_for('static', path='styles.css') }}">
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <a href="/" class="brand">World Cup Watch Parties ⚽</a>
      <nav class="nav">
        <a href="/">Parties</a>
        <a href="/parties/new">Create Party</a>
        <a href="/places">Places</a>
      </nav>
    </div>
  </header>

  <main class="container">
    {% if error %}
      <div class="alert alert-error">{{ error }}</div>
    {% endif %}

    {% if success %}
      <div class="alert alert-success">{{ success }}</div>
    {% endif %}

    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

Adjust implementation as needed.

---

### `index.html`

Should include:

- Hero/header section.
- Empty state if no parties.
- Party grid if parties exist.

Each party card should include:

- Country A
- VS
- Country B
- Date/time
- Place
- Directions if available
- Attendee count
- Attendee chips with delete buttons
- Join form

---

### `party_new.html`

Should include:

- Create party form.
- Country dropdowns.
- Date input.
- Time input.
- Place dropdown.
- Submit button.
- If no places, show link to `/places`.

---

### `places.html`

Should include:

- Add place form.
- Existing places list.
- Delete button for each place.
- Directions link if available.

---

### `party_detail.html`

Optional but recommended.

Should show:

- One party card.
- Same join/delete behavior as homepage.
- Back to all parties link.

---

## 28. Redirect Behavior

After POST requests:

```text
POST /parties -> redirect GET /
POST /parties/{id}/join -> redirect back or GET /
POST /attendees/{id}/delete -> redirect back or GET /
POST /places -> redirect GET /places
POST /places/{id}/delete -> redirect GET /places
```

Use:

```python
RedirectResponse(url, status_code=303)
```

---

## 29. Referrer Handling

For join/delete attendee routes, redirecting back is useful.

Pseudo-logic:

```python
def redirect_back(request: Request, fallback: str = "/"):
    referrer = request.headers.get("referer")
    if referrer:
        return RedirectResponse(referrer, status_code=303)
    return RedirectResponse(fallback, status_code=303)
```

Be careful not to rely on referrer for security. It is only a convenience.

---

## 30. Recommended Implementation Order

Implement in this order:

1. Create project structure.
2. Add dependencies.
3. Create database setup.
4. Create SQLModel models.
5. Create table creation on startup.
6. Seed countries.
7. Add base template and CSS.
8. Implement homepage with empty state.
9. Implement places page.
10. Implement add place.
11. Implement delete place with “unused only” rule.
12. Implement create party form.
13. Implement create party POST.
14. Implement party cards on homepage.
15. Implement join attendee.
16. Implement delete attendee.
17. Implement cleanup old parties.
18. Add optional party detail page.
19. Polish responsive CSS.
20. Manual test.

Do not start with CSS perfection. Build functionality first, then polish.

---

## 31. Manual Test Checklist

### Homepage

- [ ] Homepage loads with no parties.
- [ ] Empty state appears.
- [ ] Create Party button works.
- [ ] Places button works.
- [ ] Party cards appear after creating a party.
- [ ] Cards are sorted by date/time ascending.
- [ ] Mobile layout has no horizontal scroll.

### Places

- [ ] Can add place with name only.
- [ ] Can add place with Google Maps URL.
- [ ] Empty place name is rejected.
- [ ] Duplicate place name is rejected.
- [ ] Duplicate with different case is rejected.
- [ ] Invalid URL is rejected.
- [ ] Unused place can be deleted.
- [ ] Place used by upcoming party cannot be deleted.
- [ ] Directions link opens if maps URL exists.

### Create Party

- [ ] Cannot create party with same country twice.
- [ ] Cannot create party without date.
- [ ] Cannot create party without time.
- [ ] Cannot create party without place.
- [ ] Party appears after creation.
- [ ] If no places exist, form shows “add place first” message.

### Attendees

- [ ] Can join party with name.
- [ ] Empty name is rejected.
- [ ] Duplicate name is rejected.
- [ ] Duplicate with different case is rejected.
- [ ] Duplicate with extra spaces is rejected.
- [ ] Name appears as chip.
- [ ] Name can be removed freely.
- [ ] Removing nonexistent attendee does not crash.

### Cleanup

- [ ] Party with yesterday’s date is deleted/hidden.
- [ ] Party with today’s date remains visible.
- [ ] Party with future date remains visible.
- [ ] Attendees of deleted old party are removed.

### Responsive UI

- [ ] Works on mobile width around 375px.
- [ ] Works on tablet width around 768px.
- [ ] Works on desktop width around 1200px.
- [ ] Forms are readable and tappable.
- [ ] Buttons are not tiny.
- [ ] Attendee chips wrap properly.

---

## 32. README Requirements

Create a simple README with:

```text
Project name
Short description
Setup instructions
Run instructions
Database location
How old-party cleanup works
No-login public-board warning
```

Example run instructions:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 33. Deployment Notes

Keep deployment simple.

Acceptable deployment targets:

- Raspberry Pi
- Small VPS
- Render
- Fly.io
- Railway
- Docker on any server

For lowest maintenance on a personal server:

- Use SQLite file stored in `data/app.db`.
- Run with systemd.
- Reverse proxy with Nginx/Caddy/Cloudflare Tunnel if needed.

Do not require PostgreSQL unless deployment platform forces it.

---

## 34. Final Product Behavior Summary

The final website should behave like this:

1. User opens public URL.
2. User sees upcoming match watch parties.
3. User can create a new party using dropdowns.
4. User can add their name to a party.
5. User can remove any name.
6. User can manage places separately.
7. Old parties disappear automatically after their match day.
8. Everything works smoothly on phone and laptop.

The app should feel instant, obvious, and boringly reliable.

If a feature makes the app harder to understand or maintain, do not add it.
