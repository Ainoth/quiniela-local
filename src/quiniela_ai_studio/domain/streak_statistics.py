"""Descriptive statistics for explicitly imported, final 14-sign results."""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Iterable, Sequence


def validate_result_column(column: str) -> str:
    if not isinstance(column,str) or len(column)!=14 or any(sign not in '1X2' for sign in column):
        raise ValueError('Cada resultado histórico debe contener exactamente 14 signos 1/X/2.')
    return column


def run_lengths(column: str, sign: str) -> tuple[int, tuple[int,...]]:
    """Longest maximal run plus counts of exact run lengths 1..14.

    V treats X and 2 as one class. Runs are maximal and counted once, never as
    overlapping windows (e.g. 1111 is one length-4 run, not three pairs).
    """
    validate_result_column(column)
    if sign not in ('1','X','2','V'):
        raise ValueError('El signo de racha debe ser 1, X, 2 o V.')
    counts=[0]*14;current=0;longest=0
    for value in (*column,None):
        matches=False if value is None else (value!='1') if sign=='V' else value==sign
        if matches:
            current+=1;longest=max(longest,current)
        elif current:
            counts[current-1]+=1;current=0
    return longest,tuple(counts)


def run_figure(column: str, sign: str) -> str:
    """Return the partition made by maximal runs, largest first.

    The empty string is the figure for a column with no occurrences of the
    requested class. X and 2 are combined for V; the other classes remain
    distinct. The Pleno is excluded because columns contain 14 signs.
    """
    _longest, counts = run_lengths(column, sign)
    lengths = [length for length, amount in enumerate(counts, 1) for _ in range(amount)]
    return '-'.join(map(str, sorted(lengths, reverse=True)))


def passes_sign_rules(column: str, sign: str, setting: dict) -> bool:
    """Evaluate the guide's optional limits, exact counts and partitions."""
    from collections import Counter

    longest,counts_by_length=run_lengths(column,sign)
    if setting.get('apply_runs',False):
        minimum,maximum=setting.get('min_run'),setting.get('max_run')
        if minimum is not None and longest<minimum:return False
        if maximum is not None and longest>maximum:return False
        counts=Counter({length:amount for length,amount in enumerate(counts_by_length,1) if amount})
        for length,allowed in setting.get('allowed_counts_by_length',{}).items():
            if counts.get(int(length),0) not in allowed:return False
    if setting.get('apply_figures',False):
        total=sum(length*amount for length,amount in enumerate(counts_by_length,1))
        allowed=setting.get('figures_by_total',{}).get(total,set())
        if run_figure(column,sign) not in allowed:return False
    return True


def possible_run_frequency_counts(base: Sequence[str], sign: str, length: int) -> tuple[int, ...]:
    """Exact attainable counts of maximal runs of ``length`` in a base.

    A tiny dynamic program tracks the current run (capped at length+1) and
    the number of closed runs of the requested exact length. It avoids
    expanding a full 3^14 universe and honours each match's allowed signs.
    """
    _validate_streak_base(base, sign)
    if type(length) is not int or not 1 <= length <= 14:
        raise ValueError('La longitud de racha debe estar entre 1 y 14.')

    def belongs(value: str) -> bool:
        return value != '1' if sign == 'V' else value == sign

    states = {(0, 0)}
    for pick in base:
        next_states = set()
        choices = tuple(dict.fromkeys(pick))
        for current, total in states:
            for value in choices:
                if belongs(value):
                    next_states.add((min(length + 1, current + 1), total))
                else:
                    next_states.add((0, total + int(current == length)))
        states = next_states
    return tuple(sorted({total + int(current == length) for current, total in states}))


def possible_run_figures(base: Sequence[str], sign: str) -> dict[int, tuple[str, ...]]:
    """Enumerate reachable maximal-run partitions grouped by occurrence total.

    The state stores only the current run and the multiset of closed run
    lengths. For fourteen positions the partition set is small even when the
    base represents millions of columns.
    """
    _validate_streak_base(base, sign)

    def belongs(value: str) -> bool:
        return value != '1' if sign == 'V' else value == sign

    states = {(0, ())}
    for pick in base:
        next_states = set()
        for current, parts in states:
            for value in dict.fromkeys(pick):
                if belongs(value):
                    next_states.add((current + 1, parts))
                else:
                    next_states.add((0, tuple(sorted((*parts, current), reverse=True)) if current else parts))
        states = next_states
    grouped: dict[int, set[str]] = {}
    for current, parts in states:
        complete = tuple(sorted((*parts, current), reverse=True)) if current else parts
        total = sum(complete)
        grouped.setdefault(total, set()).add('-'.join(map(str, complete)))
    return {total: tuple(sorted(figures, key=lambda figure: tuple(-int(part) for part in figure.split('-')) if figure else ()))
            for total, figures in sorted(grouped.items())}


def _validate_streak_base(base: Sequence[str], sign: str) -> None:
    if len(base) != 14 or any(not isinstance(pick, str) or not pick or set(pick) - set('1X2') for pick in base):
        raise ValueError('La base de rachas debe contener 14 selecciones 1/X/2 válidas.')
    if sign not in ('1', 'X', '2', 'V'):
        raise ValueError('El signo de racha debe ser 1, X, 2 o V.')


def possible_run_length_bounds(base: Sequence[str], sign: str) -> tuple[int, int]:
    """Return minimum/maximum longest runs possible from a 14-match base.

    Picks are independent per match. The lower bound is the longest run forced
    by every available sign at those positions; the upper bound is the longest
    run that can be formed by choosing the class at every possible position.
    `V` treats both `X` and `2` as members of the same class.
    """
    if len(base) != 14 or any(not isinstance(pick,str) or not pick or set(pick)-set('1X2') for pick in base):
        raise ValueError('La base de rachas debe contener 14 selecciones 1/X/2 válidas.')
    if sign not in ('1','X','2','V'):
        raise ValueError('El signo de racha debe ser 1, X, 2 o V.')
    def belongs(value):
        return value != '1' if sign=='V' else value==sign
    forced=[all(belongs(value) for value in pick) for pick in base]
    possible=[any(belongs(value) for value in pick) for pick in base]
    def longest(flags):
        best=current=0
        for flag in (*flags,False):
            if flag:current+=1;best=max(best,current)
            else:current=0
        return best
    return longest(forced),longest(possible)


def count_profile(column: str) -> tuple[int,int,int]:
    validate_result_column(column)
    x=column.count('X');two=column.count('2')
    return x+two,x,two


def streak_profile(column: str) -> tuple[int,...]:
    """Joint vector: longest runs 1/X/2/V then exact run counts for each."""
    stats=[run_lengths(column,sign) for sign in ('1','X','2','V')]
    return tuple(longest for longest,_ in stats)+tuple(value for _,counts in stats for value in counts)


def frequent_profiles(columns: Iterable[str], coverage: float) -> tuple[tuple[tuple[int,...],...],int]:
    """Return deterministic highest-frequency joint profiles covering mass.

    `coverage` is a descriptive sample-mass target, not a forecast confidence.
    Ties break lexicographically and the result is reproducible.
    """
    if not 0 < coverage <= 1:
        raise ValueError('La cobertura histórica debe estar entre 0 y 1.')
    counter=Counter(tuple(profile) for profile in columns)
    if not counter:return (),0
    ordered=sorted(counter.items(),key=lambda item:(-item[1],item[0]))
    target=max(1,int(sum(counter.values())*coverage+0.999999))
    selected=[];accumulated=0
    for profile,count in ordered:
        selected.append(profile);accumulated+=count
        if accumulated>=target:break
    return tuple(selected),sum(counter.values())


def historical_figure_recommendations(columns: Iterable[str], base: Sequence[str], coverage: float):
    """Choose per-sign figure sets from real outcomes, restricted to the base.

    For each sign, the most common attainable total is chosen first; figures at
    that total are added in descending historical frequency until the requested
    sample mass is covered. Returns ``(choices, matched_rows)``. This is a
    descriptive sample rule, not a forecast.
    """
    _validate_streak_base(base,'V')
    if not 0 < coverage <= 1:
        raise ValueError('La cobertura histórica debe estar entre 0 y 1.')
    rows=tuple(validate_result_column(column) for column in columns)
    if not rows:
        raise ValueError('Se necesitan resultados finales para recomendar figuras.')
    choices={};active=[]
    for index,sign in enumerate(('1','X','2','V')):
        reachable=possible_run_figures(base,sign);counter=Counter()
        for column in rows:
            figure=run_figure(column,sign);total=sum(map(int,figure.split('-'))) if figure else 0
            if figure in reachable.get(total,()):counter[(total,figure)]+=1
        totals=Counter()
        for (total,_figure),amount in counter.items():totals[total]+=amount
        if not totals:
            choices[sign]={};continue
        total=max(totals,key=lambda value:(totals[value],-value))
        ordered=sorted(((figure,amount) for (candidate,figure),amount in counter.items() if candidate==total),
                       key=lambda item:(-item[1],tuple(-int(part) for part in item[0].split('-')) if item[0] else ()))
        target=max(1,int(totals[total]*coverage+0.999999));figures=set();collected=0
        for figure,amount in ordered:
            figures.add(figure);collected+=amount
            if collected>=target:break
        choices[sign]={total:figures};active.append(index)
    matched=0
    for column in rows:
        accepted=True
        for index,sign in enumerate(('1','X','2','V')):
            if index not in active:continue
            figure=run_figure(column,sign);total=sum(map(int,figure.split('-'))) if figure else 0
            if figure not in choices[sign].get(total,set()):accepted=False;break
        matched+=accepted
    return choices,matched


def random_figure_recommendations(base: Sequence[str], seed: int, coverage: float, sample_size: int=512):
    """Sample valid columns and project seeded joint profiles to per-sign figures."""
    _validate_streak_base(base,'V')
    if type(seed) is not int or seed < 0 or type(sample_size) is not int or sample_size < 1:
        raise ValueError('Semilla o tamaño de muestra aleatoria no válido.')
    if not 0 < coverage <= 1:
        raise ValueError('La cobertura aleatoria debe estar entre 0 y 1.')
    rng=random.Random(seed)
    columns=tuple(''.join(rng.choice(pick) for pick in base) for _ in range(sample_size))
    profiles=[]
    for column in columns:
        profile=[]
        for sign in ('1','X','2','V'):
            figure=run_figure(column,sign);total=sum(map(int,figure.split('-'))) if figure else 0
            profile.append((total,figure))
        profiles.append(tuple(profile))
    unique=sorted(set(profiles));keep=max(1,min(len(unique),round(len(unique)*coverage)))
    selected=rng.sample(unique,keep);choices={}
    for index,sign in enumerate(('1','X','2','V')):
        totals=Counter(profile[index][0] for profile in selected)
        total=max(totals,key=lambda value:(totals[value],-value))
        choices[sign]={total:{profile[index][1] for profile in selected if profile[index][0]==total}}
    return choices,columns
