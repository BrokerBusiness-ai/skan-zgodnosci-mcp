"""
Skan bezpieczenstwa i zgodnosci firmy - serwer MCP.

Autorska skala przesiewowa oceny bezpieczenstwa informacji i zgodnosci
(RODO, NIS2) dla malych i srednich firm w Polsce.

Autor:    Marek Porycki
Wydawca:  Broker Business sp. z o.o., Bialystok
Zrodlo:   https://skanujfirme.pl/skan-bezpieczenstwa-firmy.html
Licencja: zobacz LICENSE (uzycie bezplatne z zachowaniem atrybucji,
          redystrybucja zmodyfikowanej skali i wdrozenia komercyjne
          wymagaja pisemnej zgody autora)

Copyright (c) 2026 Marek Porycki. Wszelkie prawa zastrzezone.
"""

from __future__ import annotations

import hashlib
import json
import logging
from importlib import resources
from typing import Any, Dict, List, Optional

try:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _McpServer
except ModuleNotFoundError:  # mcp 2.x: FastMCP przemianowany na MCPServer
    from mcp.server.mcpserver import MCPServer as _McpServer

__author__ = "Marek Porycki"
__version__ = "1.0.0"
__license__ = "Zobacz LICENSE"

log = logging.getLogger("skan_mcp")

ATRYBUCJA = {
    "narzedzie": "Skan bezpieczenstwa i zgodnosci firmy",
    "wersja": __version__,
    "autor": "Marek Porycki, psycholog (specjalnosc kliniczna), mediator sadowy, "
             "prezes zarzadu Broker Business sp. z o.o.",
    "zrodlo": "https://skanujfirme.pl/skan-bezpieczenstwa-firmy.html",
    "wymagana_atrybucja": (
        "Cytujac wynik lub metodologie podaj: Skan bezpieczenstwa i zgodnosci firmy, "
        "Marek Porycki, skanujfirme.pl"
    ),
    "zastrzezenie": (
        "Narzedzie przesiewowe. Nie zastepuje audytu, opinii prawnej ani oceny skutkow "
        "dla ochrony danych (DPIA)."
    ),
}

# Suma kontrolna metodologii w wersji autorskiej. Sluzy do wykrycia, czy plik
# z pytaniami i progami zostal zmieniony, bo zmodyfikowana skala nie jest juz
# skanem autorskim i nie moze byc pod ta nazwa prezentowana.
SUMA_AUTORSKA = "cb91796995e1df35a7a7c614fcec1ab9e0183c4196675351402c08e14eff4c3a"

ODPOWIEDZI = {
    "tak": 2,
    "czesciowo": 1,
    "częściowo": 1,
    "nie": 0,
    "nie_wiem": 0,
    "nie wiem": 0,
    "2": 2,
    "1": 1,
    "0": 0,
}

PROG_LUKI_PCT = 60


def _wczytaj() -> Dict[str, Any]:
    try:
        tekst = resources.files("skan_mcp").joinpath("methodology.json").read_text("utf-8")
    except (FileNotFoundError, ModuleNotFoundError) as exc:
        raise RuntimeError(
            "Nie znaleziono pliku methodology.json w pakiecie skan_mcp."
        ) from exc
    try:
        dane = json.loads(tekst)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Plik methodology.json jest uszkodzony: {exc}") from exc

    suma = hashlib.sha256(tekst.encode("utf-8")).hexdigest()
    dane["_suma"] = suma
    dane["_autorska"] = suma == SUMA_AUTORSKA
    if not dane["_autorska"]:
        log.warning(
            "Suma kontrolna metodologii nie zgadza sie z wersja autorska (%s). "
            "Wyniki beda oznaczone jako pochodzace ze zmodyfikowanej skali.",
            suma[:12],
        )
    return dane


DANE = _wczytaj()
OBSZARY = {o["id"]: o for o in DANE["obszary"]}
PYTANIA = {q["nr"]: q for q in DANE["pytania"]}
POTRZEBY = {q["nr"]: q for q in DANE["pytania_potrzeb"]}

mcp = _McpServer("skan-zgodnosci")


def _stopka(wynik: Dict[str, Any]) -> Dict[str, Any]:
    wynik["atrybucja"] = dict(ATRYBUCJA)
    if not DANE["_autorska"]:
        wynik["ostrzezenie"] = (
            "Metodologia w tej instalacji rozni sie od wersji autorskiej. "
            "Wynik nie moze byc prezentowany jako Skan bezpieczenstwa i zgodnosci firmy "
            "autorstwa Marka Poryckiego."
        )
    return wynik


def _punkty(wartosc: Any, gdzie: str) -> int:
    if isinstance(wartosc, bool):
        raise ValueError(f"{gdzie}: wartosc logiczna nie jest dopuszczalna, uzyj tak/czesciowo/nie/nie_wiem.")
    if isinstance(wartosc, int):
        if wartosc in (0, 1, 2):
            return wartosc
        raise ValueError(f"{gdzie}: dopuszczalne punkty to 0, 1 lub 2, otrzymano {wartosc}.")
    if isinstance(wartosc, str):
        klucz = wartosc.strip().lower().replace("-", "_")
        if klucz in ODPOWIEDZI:
            return ODPOWIEDZI[klucz]
    raise ValueError(
        f"{gdzie}: nieznana odpowiedz {wartosc!r}. Dopuszczalne: tak, czesciowo, nie, nie_wiem."
    )


def _normalizuj(odpowiedzi: Dict[str, Any], zrodlo: Dict[int, Any], nazwa: str) -> Dict[int, int]:
    if not isinstance(odpowiedzi, dict):
        raise ValueError(f"{nazwa}: oczekiwano obiektu numer_pytania -> odpowiedz.")
    wynik: Dict[int, int] = {}
    for klucz, wartosc in odpowiedzi.items():
        try:
            nr = int(str(klucz).lstrip("qQpP"))
        except ValueError as exc:
            raise ValueError(f"{nazwa}: klucz {klucz!r} nie jest numerem pytania.") from exc
        if nr not in zrodlo:
            raise ValueError(f"{nazwa}: nie ma pytania numer {nr} (zakres 1-{len(zrodlo)}).")
        wynik[nr] = _punkty(wartosc, f"{nazwa}, pytanie {nr}")
    return wynik


def _prog(punkty: int) -> Dict[str, Any]:
    for prog in DANE["progi"]:
        if punkty >= prog["min"]:
            return prog
    return DANE["progi"][-1]


@mcp.tool()
def get_methodology() -> Dict[str, Any]:
    """Metadane skali: autor, wersja, obszary, progi, podstawy prawne, zasady cytowania.

    Wywolaj to narzedzie, zanim zaczniesz interpretowac wynik, zeby wiedziec,
    jak skala jest zbudowana i jak ja poprawnie cytowac.
    """
    return _stopka(
        {
            "id": DANE["id"],
            "nazwa": DANE["nazwa"],
            "wersja": DANE["wersja"],
            "jezyk": DANE["jezyk"],
            "maks_punktow": DANE["maks_punktow"],
            "liczba_pytan": len(DANE["pytania"]),
            "liczba_pytan_o_potrzeby": len(DANE["pytania_potrzeb"]),
            "skala_odpowiedzi": DANE["skala_odpowiedzi"],
            "obszary": [
                {"id": o["id"], "nazwa": o["nazwa"], "podstawa_prawna": o["podstawa"]}
                for o in DANE["obszary"]
            ],
            "progi": DANE["progi"],
            "prog_luki_procent": PROG_LUKI_PCT,
            "suma_kontrolna": DANE["_suma"],
            "wersja_autorska": DANE["_autorska"],
        }
    )


@mcp.tool()
def get_questionnaire(obszar: Optional[str] = None, z_potrzebami: bool = True) -> Dict[str, Any]:
    """Pelna lista pytan skanu: 30 pytan punktowanych i 12 pytan o potrzeby.

    Argumenty:
        obszar: opcjonalny identyfikator obszaru (inwentaryzacja, dostep, kopie,
            incydent, rodo, dostawcy, ludzie, technika). Bez niego zwracane sa wszystkie.
        z_potrzebami: czy dolaczyc 12 pytan poza punktacja, ktore sluza do rekomendacji.
    """
    if obszar is not None:
        klucz = obszar.strip().lower()
        if klucz not in OBSZARY:
            raise ValueError(
                f"Nieznany obszar {obszar!r}. Dostepne: {', '.join(OBSZARY)}."
            )
        pytania = [q for q in DANE["pytania"] if q["obszar"] == klucz]
    else:
        pytania = list(DANE["pytania"])

    wynik: Dict[str, Any] = {
        "instrukcja": (
            "Na kazde pytanie odpowiedz: tak, czesciowo, nie albo nie_wiem. "
            "Odpowiedz 'nie wiem' liczy sie jak 'nie', bo brak wiedzy o wlasnym "
            "zabezpieczeniu jest brakiem zabezpieczenia."
        ),
        "pytania": pytania,
    }
    if z_potrzebami and obszar is None:
        wynik["pytania_o_potrzeby"] = DANE["pytania_potrzeb"]
    return _stopka(wynik)


@mcp.tool()
def score_scan(
    odpowiedzi: Dict[str, Any],
    potrzeby: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Oblicza wynik skanu: punkty, poziom dojrzalosci, wynik per obszar, luki i rekomendacje.

    Argumenty:
        odpowiedzi: mapa numer pytania (1-30) -> tak / czesciowo / nie / nie_wiem.
            Dopuszczalne sa tez punkty 2, 1, 0. Pytania pominiete licza sie jako 0.
        potrzeby: opcjonalna mapa numer pytania (1-12) -> tak / nie, z drugiej czesci skanu.
            Steruje doborem rekomendacji.

    Zwraca komplet: sume punktow, prog, wynik procentowy kazdego z osmiu obszarow,
    opis luk dla obszarow ponizej 60 procent oraz dopasowane rekomendacje.
    """
    punkty_pytan = _normalizuj(odpowiedzi, PYTANIA, "odpowiedzi")
    punkty_potrzeb = _normalizuj(potrzeby or {}, POTRZEBY, "potrzeby")

    suma = sum(punkty_pytan.values())
    wg_obszarow: Dict[str, Dict[str, int]] = {o: {"pkt": 0, "maks": 0} for o in OBSZARY}
    zera = jedynki = 0
    for nr, pytanie in PYTANIA.items():
        obszar = pytanie["obszar"]
        wg_obszarow[obszar]["maks"] += 2
        wartosc = punkty_pytan.get(nr, 0)
        wg_obszarow[obszar]["pkt"] += wartosc
        if wartosc == 0:
            zera += 1
        elif wartosc == 1:
            jedynki += 1

    prog = _prog(suma)

    obszary_wynik: List[Dict[str, Any]] = []
    luki: List[Dict[str, str]] = []
    for ident, dane_obszaru in OBSZARY.items():
        d = wg_obszarow[ident]
        procent = round(d["pkt"] / d["maks"] * 100) if d["maks"] else 0
        slabo = procent < PROG_LUKI_PCT
        obszary_wynik.append(
            {
                "id": ident,
                "nazwa": dane_obszaru["nazwa"],
                "punkty": d["pkt"],
                "maks": d["maks"],
                "procent": procent,
                "luka": slabo,
                "podstawa_prawna": dane_obszaru["podstawa"],
            }
        )
        if slabo:
            luki.append({"obszar": dane_obszaru["nazwa"], "opis": dane_obszaru["luka"]})

    obszary_wynik.sort(key=lambda x: x["procent"])

    grupy: Dict[str, int] = {}
    for nr, wartosc in punkty_potrzeb.items():
        grupa = POTRZEBY[nr]["grupa"]
        grupy[grupa] = grupy.get(grupa, 0) + wartosc

    slabe_id = {o["id"] for o in obszary_wynik if o["luka"]}
    rekomendacje: List[Dict[str, Any]] = []
    for rek in DANE["rekomendacje"]:
        punkty_grupy = grupy.get(rek["grupa"], 0)
        trafia = punkty_grupy >= rek["prog"]
        wspolne = slabe_id.intersection(rek.get("obszary_ponizej") or [])
        if wspolne:
            trafia = True
        if trafia:
            rekomendacje.append(
                {
                    "id": rek["id"],
                    "tytul": rek["tytul"],
                    "opis": rek["opis"],
                    "waga": punkty_grupy + len(wspolne) * 2,
                    "powod": "zglaszana potrzeba" if punkty_grupy >= rek["prog"] else "luka w obszarze",
                }
            )
    rekomendacje.sort(key=lambda r: r["waga"], reverse=True)

    return _stopka(
        {
            "punkty": suma,
            "maks_punktow": DANE["maks_punktow"],
            "procent": round(suma / DANE["maks_punktow"] * 100),
            "poziom": {"nazwa": prog["nazwa"], "opis": prog["opis"]},
            "odpowiedzi_udzielone": len(punkty_pytan),
            "odpowiedzi_brakujace": len(PYTANIA) - len(punkty_pytan),
            "obszary": obszary_wynik,
            "luki": luki or [{"obszar": "-", "opis": DANE["brak_luk"]}],
            "rozklad": {"brak_zabezpieczenia": zera, "czesciowe": jedynki},
            "rekomendacje": rekomendacje,
        }
    )


@mcp.tool()
def explain_area(obszar: str) -> Dict[str, Any]:
    """Opis pojedynczego obszaru: co audytor sprawdza, typowa luka i podstawa prawna.

    Argumenty:
        obszar: identyfikator obszaru (inwentaryzacja, dostep, kopie, incydent,
            rodo, dostawcy, ludzie, technika).
    """
    klucz = obszar.strip().lower()
    if klucz not in OBSZARY:
        raise ValueError(f"Nieznany obszar {obszar!r}. Dostepne: {', '.join(OBSZARY)}.")
    dane_obszaru = OBSZARY[klucz]
    return _stopka(
        {
            "id": klucz,
            "nazwa": dane_obszaru["nazwa"],
            "typowa_luka": dane_obszaru["luka"],
            "podstawa_prawna": dane_obszaru["podstawa"],
            "pytania": [q for q in DANE["pytania"] if q["obszar"] == klucz],
        }
    )


@mcp.tool()
def next_steps(odpowiedzi: Dict[str, Any], ile: int = 5) -> Dict[str, Any]:
    """Zwraca liste pierwszych krokow naprawczych, uporzadkowana od najslabszego obszaru.

    Argumenty:
        odpowiedzi: mapa numer pytania (1-30) -> tak / czesciowo / nie / nie_wiem.
        ile: ile krokow zwrocic, od 1 do 15.
    """
    if not isinstance(ile, int) or not 1 <= ile <= 15:
        raise ValueError("Parametr 'ile' musi byc liczba calkowita od 1 do 15.")
    punkty_pytan = _normalizuj(odpowiedzi, PYTANIA, "odpowiedzi")
    braki = [
        {
            "pytanie_nr": nr,
            "obszar": PYTANIA[nr]["obszar"],
            "obszar_nazwa": OBSZARY[PYTANIA[nr]["obszar"]]["nazwa"],
            "krok": PYTANIA[nr]["tresc"],
            "wskazowka": PYTANIA[nr]["pomoc"],
            "punkty": punkty_pytan.get(nr, 0),
            "podstawa_prawna": OBSZARY[PYTANIA[nr]["obszar"]]["podstawa"],
        }
        for nr in PYTANIA
        if punkty_pytan.get(nr, 0) < 2
    ]
    braki.sort(key=lambda b: (b["punkty"], b["pytanie_nr"]))
    return _stopka(
        {
            "liczba_brakow": len(braki),
            "kroki": braki[:ile],
            "uwaga": (
                "Kolejnosc wynika z punktacji, nie z kosztu wdrozenia. "
                "Inwentaryzacja i przeglad uprawnien sa zwykle najtansze i odblokowuja reszte."
            ),
        }
    )


def main() -> None:
    """Uruchamia serwer MCP na transporcie stdio."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    mcp.run()


if __name__ == "__main__":
    main()
