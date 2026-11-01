"""Canonical, provider-independent team identity matching.

Names are labels, not identifiers. This module tolerates formatting changes,
known aliases and one-character typos while preserving gender and reserve-team
qualifiers. Match number and home/away order must still be checked by callers.
"""

from __future__ import annotations

import re
import unicodedata

# Aliases observed in WIN1X2, Quinielista, ESPN and published scrutiny pages.
# Values are canonical compact names. Keep this registry in one place.
TEAM_ALIASES = {
    "ANDORRAFC": "ANDORRA",
    "ATHCLUBBILBAO": "ATHCLUB",
    "ATHLETICCLUB": "ATHCLUB",
    "ATHLETIC": "ATHCLUB",
    "ATH": "ATHCLUB",
    "ATHLETICBILBAO": "ATHCLUB",
    "ATHLETICCLUBBILBAO": "ATHCLUB",
    "ATLETICOMADRID": "ATMADRID",
    "ATLETICODEMADRID": "ATMADRID",
    "RAYOVALLECANO": "RAYO",
    "REALSOCIEDAD": "RSOCIEDAD",
    "REALMADRID": "RMADRID",
    "REALMADRIDCF": "RMADRID",
    "RACING": "RACINGS",
    "RACINGSANTANDER": "RACINGS",
    "DEPORTIVOCORUNA": "DEPORTIVO",
    "DEPORTIVOLACORUNA": "DEPORTIVO",
    "MANCHUNITED": "MANUNITED",
    "MANCHESTERUNITED": "MANUNITED",
    "BAYERNMUNICH": "BMUNICH",
    "BORDORTMUND": "BDORTMUND",
    "BORUSSIADORTMUND": "BDORTMUND",
    "MANCHESTCITY": "MANCITY",
    "MANCHESTERCITY": "MANCITY",
    "CSUCRAIOVA": "UCRAIOVA",
    "PSV": "PSVEINDHOVEN",
    "PSVEIDHOVEN": "PSVEINDHOVEN",
    "SHAKTARDONETSK": "SHAKHTARDONETSK",
    "RBLEIPZIG": "LEIPZIG",
    "REALBETIS": "BETIS",
    "REALBETISBALOMPIE": "BETIS",
    "CELTAVIGO": "CELTA",
    "RCCELTADEVIGO": "CELTA",
    "CDCASTELLON": "CASTELLON",
    "CDSABADELL": "SABADELL",
    "RCDMALLORCA": "MALLORCA",
    "CDTENERIFE": "TENERIFE",
    "UDALMERIA": "ALMERIA",
    "REALOVIEDO": "ROVIEDO",
    "DUXLOGRONO": "LOGRONO",
    "LOGRONOUNITED": "LOGRONO",
    "FCBADALONA": "BADALONA",
    "LEVANTEBADALONA": "BADALONA",
    # WIN1X2 historically contains the typo "Sevila" in some calendars.
    "SEVILA": "SEVILLA",
    "SEVILLAF": "SEVILLA",
    # Madrid CCF/CFF is a known typo in the WIN1X2 women's team code/name.
    "MADRIDCCF": "MADRIDCFF",
    "MADRIDCFF": "MADRIDCFF",
}

_FEMALE_SUFFIX = re.compile(
    r"(?:\s*W\.?\s*\(\s*F\s*\)|\s*\(\s*(?:F|FEM|FEMENINO|W|WOMEN)\s*\)|\s+(?:FEMENINO|WOMEN))\s*$",
    re.IGNORECASE,
)
_MALE_SUFFIX = re.compile(r"\s*\(\s*(?:M|MASCULINO)\s*\)\s*$", re.IGNORECASE)
_LEGAL_SUFFIXES = {"FC", "CF", "SAD", "CDE", "CLUB"}


def _parts(name: str) -> tuple[tuple[str, ...], str | None]:
    if not isinstance(name, str) or not name.strip():
        return (), None
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    gender = None
    female = _FEMALE_SUFFIX.search(text)
    male = _MALE_SUFFIX.search(text)
    if female:
        text = text[: female.start()]
        gender = "F"
    elif male:
        text = text[: male.start()]
        gender = "M"
    tokens = tuple(re.findall(r"[A-Z0-9]+", text.upper()))
    while tokens and tokens[-1] in _LEGAL_SUFFIXES:
        tokens = tokens[:-1]
    return tokens, gender


def _canonical_base(name: str) -> tuple[str, tuple[str, ...], str | None]:
    tokens, gender = _parts(name)
    compact = "".join(tokens)
    canonical = TEAM_ALIASES.get(compact, compact)
    # Resolve a second alias hop, but guard against malformed cycles.
    canonical = TEAM_ALIASES.get(canonical, canonical)
    canonical_tokens = (canonical,) if canonical != compact else tokens
    return canonical, canonical_tokens, gender


def team_key(name: str, *, include_gender: bool = True) -> str:
    """Return a canonical comparison key; preserve women's identity by default."""
    base, _tokens, gender = _canonical_base(name)
    return base + (gender or "") if include_gender else base


def _edit_distance_at_most_one(left: str, right: str) -> bool:
    """Check one insertion, deletion or substitution without a fuzzy dependency."""
    if left == right:
        return True
    if min(len(left), len(right)) < 5 or abs(len(left) - len(right)) > 1:
        return False
    if len(left) > len(right):
        left, right = right, left
    i = j = differences = 0
    while i < len(left) and j < len(right):
        if left[i] == right[j]:
            i += 1
            j += 1
            continue
        differences += 1
        if differences > 1:
            return False
        if len(left) == len(right):
            i += 1
        j += 1
    if j < len(right) or i < len(left):
        differences += 1
    return differences <= 1


def same_team_name(
    first: str,
    second: str,
    *,
    allow_missing_gender: bool = False,
    ignore_gender: bool = False,
) -> bool:
    """Compare names after canonicalization and conservative typo tolerance.

    ``allow_missing_gender`` is only appropriate when the caller has already
    established the competition (for example, ESPN's women's league endpoint).
    It never allows an explicit male/female conflict. Fuzzy matching preserves
    token count/order, which keeps first teams separate from B/II/reserve teams.
    """
    left_base, left_tokens, left_gender = _canonical_base(first)
    right_base, right_tokens, right_gender = _canonical_base(second)
    if not left_base or not right_base:
        return False
    if not ignore_gender:
        if left_gender and right_gender and left_gender != right_gender:
            return False
        if (left_gender is None) != (right_gender is None) and not allow_missing_gender:
            return False
    if left_base == right_base:
        return True
    if len(left_tokens) != len(right_tokens):
        return False
    return all(
        a == b or _edit_distance_at_most_one(a, b)
        for a, b in zip(left_tokens, right_tokens)
    )


def same_team_pair(
    expected: tuple[str, str],
    actual: tuple[str, str],
    *,
    allow_missing_gender: bool = False,
    ignore_gender: bool = False,
) -> bool:
    """Compare one fixture without allowing home/away reversal."""
    return (
        len(expected) == 2
        and len(actual) == 2
        and same_team_name(expected[0], actual[0], allow_missing_gender=allow_missing_gender,
                           ignore_gender=ignore_gender)
        and same_team_name(expected[1], actual[1], allow_missing_gender=allow_missing_gender,
                           ignore_gender=ignore_gender)
    )


def uniquely_matches_team(
    expected: str,
    actual: str,
    candidates: tuple[str, ...] | list[str],
    *,
    allow_missing_gender: bool = False,
) -> bool:
    """Match a typo only when it resolves to one distinct team in context."""
    if team_key(expected) == team_key(actual):
        return True
    if not same_team_name(expected, actual, allow_missing_gender=allow_missing_gender):
        return False
    matches = {
        team_key(candidate)
        for candidate in candidates
        if same_team_name(candidate, actual, allow_missing_gender=allow_missing_gender)
    }
    return matches == {team_key(expected)}


def same_fixtures(
    expected: tuple[tuple[str, str], ...] | list[tuple[str, str]],
    actual: tuple[tuple[str, str], ...] | list[tuple[str, str]],
    *,
    allow_missing_gender: bool = False,
) -> bool:
    """Compare ordered fixtures with contextual, unambiguous typo matching."""
    if len(expected) != len(actual):
        return False
    homes = [pair[0] for pair in expected]
    aways = [pair[1] for pair in expected]
    return all(
        uniquely_matches_team(home, received_home, homes, allow_missing_gender=allow_missing_gender)
        and uniquely_matches_team(away, received_away, aways, allow_missing_gender=allow_missing_gender)
        for (home, away), (received_home, received_away) in zip(expected, actual)
    )
