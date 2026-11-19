"""Shared date helpers for patentassist scripts (stdlib only, Python 3.9+).

Exports:
    add_months(d, n)        calendar-month arithmetic, day clamped to month end
    is_weekend(d)
    federal_holidays(year)  {date: name} of OBSERVED federal holidays in that year
    is_federal_holiday(d)
    is_business_day(d)
    roll_forward(d)         next day that is not a Saturday, Sunday, or federal holiday
    parse_date(s)           'YYYY-MM-DD' -> date (raises ValueError)

35 USC 21(b): when the last day for taking an action or paying a fee falls on a
Saturday, Sunday, or a Federal holiday within the District of Columbia, the action
may be taken on the next succeeding business day.

Federal holidays per 5 USC 6103(a). Observance per 5 USC 6103(b) / OPM practice for
a Monday-Friday schedule: a holiday on Saturday is observed the Friday before; a
holiday on Sunday is observed the Monday after. New Year's Day falling on a Saturday
is observed on Friday, December 31 of the previous year. Inauguration Day (Jan 20
after a presidential election year) is a holiday within the District of Columbia
under 5 USC 6103(c); it is included because 35 USC 21 refers to DC holidays.

Not covered: one-off closures by executive order or unscheduled USPTO closures
(weather, shutdowns). Check the USPTO closure notices for those.
"""

import calendar
import datetime as _dt

__all__ = [
    "add_months",
    "is_weekend",
    "federal_holidays",
    "is_federal_holiday",
    "is_business_day",
    "roll_forward",
    "parse_date",
    "holiday_name",
]


def parse_date(s):
    """Parse an ISO 'YYYY-MM-DD' string (or pass a date through)."""
    if isinstance(s, _dt.datetime):
        return s.date()
    if isinstance(s, _dt.date):
        return s
    if not isinstance(s, str):
        raise ValueError("not a date: %r" % (s,))
    return _dt.datetime.strptime(s.strip()[:10], "%Y-%m-%d").date()


def add_months(d, n):
    """Add n calendar months (n may be negative). Day is clamped to the month end,
    so add_months(2024-01-31, 1) == 2024-02-29 and add_months(2024-02-29, 12) ==
    2025-02-28."""
    d = parse_date(d)
    total = d.year * 12 + (d.month - 1) + int(n)
    year, month0 = divmod(total, 12)
    month = month0 + 1
    last = calendar.monthrange(year, month)[1]
    return _dt.date(year, month, min(d.day, last))


def is_weekend(d):
    return parse_date(d).weekday() >= 5


def _nth_weekday(year, month, weekday, n):
    """n-th (1-based) weekday (Mon=0) of a month."""
    first = _dt.date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + _dt.timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year, month, weekday):
    last = _dt.date(year, month, calendar.monthrange(year, month)[1])
    offset = (last.weekday() - weekday) % 7
    return last - _dt.timedelta(days=offset)


def _observed(d):
    if d.weekday() == 5:  # Saturday -> Friday
        return d - _dt.timedelta(days=1)
    if d.weekday() == 6:  # Sunday -> Monday
        return d + _dt.timedelta(days=1)
    return d


def _actual_holidays(year):
    """List of (actual_date, name, observe_shift) for holidays defined by date in `year`."""
    hol = []
    hol.append((_dt.date(year, 1, 1), "New Year's Day", True))
    if year >= 1986:
        hol.append((_nth_weekday(year, 1, 0, 3), "Birthday of Martin Luther King, Jr.", False))
    hol.append((_nth_weekday(year, 2, 0, 3), "Washington's Birthday", False))
    hol.append((_last_weekday(year, 5, 0), "Memorial Day", False))
    if year >= 2021:
        hol.append((_dt.date(year, 6, 19), "Juneteenth National Independence Day", True))
    hol.append((_dt.date(year, 7, 4), "Independence Day", True))
    hol.append((_nth_weekday(year, 9, 0, 1), "Labor Day", False))
    hol.append((_nth_weekday(year, 10, 0, 2), "Columbus Day", False))
    hol.append((_dt.date(year, 11, 11), "Veterans Day", True))
    hol.append((_nth_weekday(year, 11, 3, 4), "Thanksgiving Day", False))
    hol.append((_dt.date(year, 12, 25), "Christmas Day", True))
    # Inauguration Day (DC only, 5 USC 6103(c)): Jan 20 of the year after a
    # presidential election (years where year % 4 == 1), moved to Jan 21 if Sunday.
    if year >= 1965 and year % 4 == 1:
        inaug = _dt.date(year, 1, 20)
        if inaug.weekday() == 6:
            inaug = _dt.date(year, 1, 21)
        hol.append((inaug, "Inauguration Day (District of Columbia)", False))
    return hol


_CACHE = {}


def federal_holidays(year):
    """Observed federal holidays (DC) that fall in calendar `year`, as {date: name}.

    Includes the next year's New Year's Day when it is observed on Dec 31 of `year`.
    Inauguration Day on a Saturday is not moved (it is not a 6103(b) holiday shift)."""
    year = int(year)
    if year in _CACHE:
        return dict(_CACHE[year])
    out = {}
    for y in (year, year + 1):
        for actual, name, shift in _actual_holidays(y):
            obs = _observed(actual) if shift else actual
            if obs.year == year:
                if obs != actual:
                    name = "%s (observed)" % name
                # Keep the first name if two land on one day (e.g. Inauguration + MLK).
                if obs in out:
                    out[obs] = out[obs] + " / " + name
                else:
                    out[obs] = name
    _CACHE[year] = dict(out)
    return out


def holiday_name(d):
    d = parse_date(d)
    return federal_holidays(d.year).get(d)


def is_federal_holiday(d):
    return holiday_name(d) is not None


def is_business_day(d):
    d = parse_date(d)
    return not is_weekend(d) and not is_federal_holiday(d)


def roll_forward(d):
    """Return d if it is a business day, else the next business day (35 USC 21(b))."""
    d = parse_date(d)
    while not is_business_day(d):
        d = d + _dt.timedelta(days=1)
    return d


if __name__ == "__main__":  # tiny self-check / helper
    import sys

    if len(sys.argv) > 1:
        y = int(sys.argv[1])
        for k in sorted(federal_holidays(y)):
            print(k.isoformat(), k.strftime("%a"), federal_holidays(y)[k])
    else:
        print(__doc__)
