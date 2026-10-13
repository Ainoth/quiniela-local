"""Agrupación de apuestas existentes: nunca reasigna un Pleno ni añade apuestas."""
import math
from collections import Counter
from dataclasses import dataclass

from .models import Bet


@dataclass(frozen=True)
class ChannelRules:
    name: str = 'TuLotero · sencillas · revisión 13/10/2026'
    minimum: int = 2
    maximum: int = 8
    source: str = 'https://tulotero.es/jugar-quiniela/'

    def __post_init__(self):
        if type(self.minimum) is not int or type(self.maximum) is not int or not 1<=self.minimum<=self.maximum<=100:
            raise ValueError('Mínimo/máximo del canal entre 1 y 100 requeridos.')


@dataclass(frozen=True)
class Ticket:
    number: int
    bets: tuple[Bet, ...]

    @property
    def pleno(self):return self.bets[0].pleno


def group_tickets(bets, rules=ChannelRules()):
    grouped={}
    if sum(b.quantity for b in bets)>200000:
        raise ValueError('Asistente limitado a 200.000 apuestas; divide el sistema conservando Plenos.')
    for bet in bets:
        if not bet.pleno:raise ValueError('Todas las apuestas necesitan Pleno para este canal.')
        grouped.setdefault(bet.pleno,[]).extend(Bet(bet.column,bet.pleno) for _ in range(bet.quantity))
    if not grouped:raise ValueError('No hay apuestas que agrupar.')
    tickets=[]
    for pleno,group in sorted(grouped.items()):
        bins=math.ceil(len(group)/rules.maximum)
        if len(group)<bins*rules.minimum:
            raise ValueError(f'Pleno {pleno[0]}-{pleno[1]}: {len(group)} apuestas no se pueden repartir entre {rules.minimum} y {rules.maximum} por boleto. No se cambian goles ni se duplican apuestas. Elige otra selección o un canal compatible.')
        sizes=[rules.minimum]*bins;remaining=len(group)-sum(sizes)
        for i in range(bins):
            extra=min(remaining,rules.maximum-sizes[i]);sizes[i]+=extra;remaining-=extra
        start=0
        for size in sizes:
            tickets.append(Ticket(len(tickets)+1,tuple(group[start:start+size])));start+=size
    original=Counter()
    for b in bets:original[(b.column,b.pleno)]+=b.quantity
    if Counter((b.column,b.pleno) for t in tickets for b in t.bets)!=original:
        raise ValueError('La agrupación no conserva todas las apuestas.')
    return tuple(tickets)
