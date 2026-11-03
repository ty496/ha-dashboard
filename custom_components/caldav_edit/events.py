"""Find, change and delete one event in caldav calendars. No Home Assistant imports, so it can be tested alone.

An event is found by its title and the local day it is on. Copies of the same event (same UID) in several
calendars count as one event and are changed together. Repeating events are refused: changing the master would
move every occurrence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone, tzinfo
import re
from typing import Any


class EventError(Exception):
    """The request can't be carried out as asked: nothing matched, more than one did, a repeating event, a bad time."""


def norm(text: Any) -> str:
    """Letters and digits only, lower case, single spaces: 'Date Night 💖' -> 'date night'."""
    return " ".join(re.sub(r"[^0-9a-z]+", " ", str(text).lower()).split())


def parse_when(value: str, tz: tzinfo) -> date | datetime:
    """'YYYY-MM-DD' is an all-day date; 'YYYY-MM-DD HH:MM' is a time in the home time zone."""
    text = str(value).strip().replace("T", " ")
    try:
        if len(text) == 10:
            return date.fromisoformat(text)
        when = datetime.fromisoformat(text)
    except ValueError as err:
        raise EventError(f"Can't read the time '{value}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM.") from err
    return when if when.tzinfo else when.replace(tzinfo=tz)


def _timed(value: Any) -> bool:
    return isinstance(value, datetime)


def _aware(value: date | datetime, tz: tzinfo) -> date | datetime:
    """Floating times (no zone) are read as home time."""
    return value.replace(tzinfo=tz) if _timed(value) and value.tzinfo is None else value


def span(comp: Any, tz: tzinfo) -> tuple[date | datetime, date | datetime]:
    """Start and end of a VEVENT. No DTEND: DURATION, else one day (all-day) or zero length (timed)."""
    start = _aware(comp.decoded("DTSTART"), tz)
    if "DTEND" in comp:
        end = _aware(comp.decoded("DTEND"), tz)
    elif "DURATION" in comp:
        end = start + comp.decoded("DURATION")
    else:
        end = start if _timed(start) else start + timedelta(days=1)
    return start, end


def _day(value: date | datetime, tz: tzinfo) -> date:
    return value.astimezone(tz).date() if _timed(value) else value


def occurs_on(comp: Any, day: date, tz: tzinfo) -> bool:
    """True when the event covers any part of the local day (all-day ends are exclusive)."""
    start, end = span(comp, tz)
    first = _day(start, tz)
    if _timed(end):
        last = _day(end - timedelta(microseconds=1), tz) if end > start else first
    else:
        last = end - timedelta(days=1)
    return first <= day <= max(first, last)


def say_day(day: date) -> str:
    return f"{day:%A, %B} {day.day}"


def say_time(value: date | datetime, tz: tzinfo) -> str:
    if not _timed(value):
        return "all day"
    local = value.astimezone(tz)
    hour = local.hour % 12 or 12
    return f"{hour}:{local.minute:02d} {'AM' if local.hour < 12 else 'PM'}"


@dataclass
class Match:
    """One copy of the event: the caldav object, its VEVENT, and the calendar's name."""

    obj: Any
    comp: Any
    calendar: str


def find(calendars: list[tuple[Any, str]], day: date, title: str, tz: tzinfo) -> list[Match]:
    """All copies of the one event called `title` on `day`. Raises EventError unless exactly one event matches."""
    want = norm(title)
    if not want:
        raise EventError("Say which event, by its title.")
    # A day either side, then filter here: servers place all-day events by UTC days.
    low = datetime.combine(day - timedelta(days=1), time.min, tz)
    high = datetime.combine(day + timedelta(days=2), time.min, tz)
    found: list[Match] = []
    for calendar, name in calendars:
        for obj in calendar.search(start=low, end=high, event=True, expand=False):
            comp = obj.icalendar_component
            if comp is None or comp.name != "VEVENT" or "DTSTART" not in comp:
                continue
            have = norm(comp.get("SUMMARY", ""))
            if not have or not (want in have or have in want):
                continue
            if "RRULE" in comp or "RECURRENCE-ID" in comp or occurs_on(comp, day, tz):
                found.append(Match(obj, comp, name))
    exact = [m for m in found if norm(m.comp.get("SUMMARY", "")) == want]
    found = exact or found
    if not found:
        raise EventError(f"There's no event called '{title}' on {say_day(day)}.")
    events: dict[str, list[Match]] = {}
    for m in found:
        events.setdefault(str(m.comp.get("UID", id(m.obj))), []).append(m)
    if len(events) > 1:
        options = "; ".join(
            f"{group[0].comp.get('SUMMARY', '')} at {say_time(span(group[0].comp, tz)[0], tz)} in {group[0].calendar}"
            for group in events.values()
        )
        raise EventError(f"More than one event matches '{title}' on {say_day(day)}: {options}. Say which one.")
    copies = next(iter(events.values()))
    first = copies[0].comp
    if "RRULE" in first or "RECURRENCE-ID" in first:
        raise EventError(
            f"'{first.get('SUMMARY', '')}' is a repeating event. Change it on a phone so the other dates stay right."
        )
    return copies


def _wire(value: date | datetime) -> date | datetime:
    """Timed values go out in UTC (no time zone definition needed); dates stay dates."""
    return value.astimezone(timezone.utc) if _timed(value) else value


def _save(obj: Any) -> None:
    """Save a just-re-read event. If the server still rejects the cached ETag / Schedule-Tag (412), drop the tag
    and save once more: the event was read a moment ago, so there is no stale copy to overwrite."""
    try:
        obj.save(no_create=True, obj_type="event")
    except Exception as err:  # caldav's ETagMismatchError / ScheduleTagMismatchError; no caldav import here
        if type(err).__name__ not in ("ETagMismatchError", "ScheduleTagMismatchError"):
            raise
        for key in [k for k in obj.props if str(k).endswith(("getetag", "schedule-tag"))]:
            obj.props.pop(key, None)
        obj.save(no_create=True, obj_type="event")


def describe(m: Match, tz: tzinfo) -> dict[str, str]:
    start, end = span(m.comp, tz)
    out = {"title": str(m.comp.get("SUMMARY", "")), "calendar": m.calendar, "day": say_day(_day(start, tz))}
    if _timed(start):
        out["start"] = say_time(start, tz)
        out["end"] = say_time(end, tz)
    else:
        out["all_day"] = "yes"
    return out


def update(
    copies: list[Match],
    tz: tzinfo,
    new_title: str | None = None,
    new_start: str | None = None,
    new_end: str | None = None,
    new_location: str | None = None,
    new_description: str | None = None,
) -> dict[str, str]:
    """Change the event in every copy and save. A new start without an end keeps the event's length."""
    if not any((new_title, new_start, new_end, new_location, new_description)):
        raise EventError("Say what to change: the title, the time, the place or the notes.")
    start, end = span(copies[0].comp, tz)
    begin = parse_when(new_start, tz) if new_start else None
    finish = parse_when(new_end, tz) if new_end else None
    if begin is not None or finish is not None:
        if begin is None:
            begin = start
        if finish is None:
            if _timed(begin) == _timed(start):
                finish = begin + (end - start)
            else:
                finish = begin + (timedelta(hours=1) if _timed(begin) else timedelta(days=1))
        if _timed(begin) != _timed(finish):
            raise EventError("The start and end both need a time, or both be whole days.")
        if finish <= begin:
            raise EventError("The end has to be after the start.")
    for m in copies:
        # Re-read the event first: iCloud answers a save carrying the ETag from a search report with 412
        # Precondition Failed; a plain GET returns the ETag it expects back.
        m.obj.load()
        comp = m.comp = m.obj.icalendar_component
        if new_title:
            comp["SUMMARY"] = new_title
        if new_location:
            comp["LOCATION"] = new_location
        if new_description:
            comp["DESCRIPTION"] = new_description
        if begin is not None:
            for key in ("DTSTART", "DTEND", "DURATION"):
                comp.pop(key, None)
            comp.add("DTSTART", _wire(begin))
            comp.add("DTEND", _wire(finish))
        _save(m.obj)
    return describe(copies[0], tz)


def delete(copies: list[Match], tz: tzinfo) -> dict[str, str]:
    """Delete every copy of the event."""
    info = describe(copies[0], tz)
    for m in copies:
        m.obj.delete()
    return info
