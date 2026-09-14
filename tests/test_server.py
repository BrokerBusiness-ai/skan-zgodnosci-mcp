"""Testy skanu zgodnosci. Autor: Marek Porycki."""

import pytest

from skan_mcp import server as s


def test_metodologia_autorska():
    m = s.get_methodology()
    assert m["wersja_autorska"] is True
    assert m["liczba_pytan"] == 30
    assert m["maks_punktow"] == 60
    assert len(m["obszary"]) == 8


def test_maksymalny_wynik():
    w = s.score_scan({str(i): "tak" for i in range(1, 31)})
    assert w["punkty"] == 60
    assert w["poziom"]["nazwa"] == "Dojrzałość wysoka"
    assert all(o["luka"] is False for o in w["obszary"])


def test_zerowy_wynik_daje_osiem_luk():
    w = s.score_scan({str(i): "nie" for i in range(1, 31)})
    assert w["punkty"] == 0
    assert len([o for o in w["obszary"] if o["luka"]]) == 8


def test_nie_wiem_liczy_sie_jak_nie():
    a = s.score_scan({str(i): "nie_wiem" for i in range(1, 31)})
    b = s.score_scan({str(i): "nie" for i in range(1, 31)})
    assert a["punkty"] == b["punkty"] == 0


def test_brakujace_odpowiedzi_sa_zerami():
    w = s.score_scan({"1": "tak"})
    assert w["punkty"] == 2
    assert w["odpowiedzi_brakujace"] == 29


def test_potrzeby_wywoluja_rekomendacje():
    odp = {str(i): "tak" for i in range(1, 31)}
    w = s.score_scan(odp, {"1": "tak", "2": "tak"})
    assert any(r["id"] == "ai" for r in w["rekomendacje"])


def test_atrybucja_w_kazdej_odpowiedzi():
    for wynik in (
        s.get_methodology(),
        s.get_questionnaire(),
        s.score_scan({"1": "tak"}),
        s.explain_area("rodo"),
        s.next_steps({"1": "nie"}),
    ):
        assert "skanujfirme.pl" in wynik["atrybucja"]["zrodlo"]


@pytest.mark.parametrize(
    "odpowiedzi",
    [{"99": "tak"}, {"1": "moze"}, {"1": True}, {"abc": "tak"}],
)
def test_walidacja_odrzuca_bledne_dane(odpowiedzi):
    with pytest.raises(ValueError):
        s.score_scan(odpowiedzi)


def test_walidacja_obszaru():
    with pytest.raises(ValueError):
        s.explain_area("nie_ma_takiego")


def test_next_steps_zakres():
    with pytest.raises(ValueError):
        s.next_steps({"1": "nie"}, ile=99)
    kroki = s.next_steps({str(i): "nie" for i in range(1, 31)}, ile=5)
    assert len(kroki["kroki"]) == 5
    assert kroki["liczba_brakow"] == 30
