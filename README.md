# Skan zgodności MCP

Serwer MCP z autorską skalą przesiewową oceny bezpieczeństwa informacji i zgodności (RODO, NIS2) dla małych i średnich firm w Polsce. Bez klucza API, bez rejestracji, bez wysyłania danych na zewnątrz: cała punktacja liczy się lokalnie.

Asystent AI podłączony do tego serwera potrafi przeprowadzić firmę przez 30 pytań, policzyć wynik w ośmiu obszarach, wskazać luki z podstawą prawną i podać kolejność pierwszych kroków.

**Wersja przeglądarkowa:** [skanujfirme.pl/skan-bezpieczenstwa-firmy.html](https://skanujfirme.pl/skan-bezpieczenstwa-firmy.html)

## Co robi

| Narzędzie | Do czego służy |
|---|---|
| `get_methodology` | Metadane skali: obszary, progi, podstawy prawne, zasady cytowania |
| `get_questionnaire` | 30 pytań punktowanych plus 12 pytań o potrzeby, opcjonalnie tylko jeden obszar |
| `score_scan` | Wynik: punkty, poziom dojrzałości, procent per obszar, luki, rekomendacje |
| `explain_area` | Jeden obszar: co sprawdza audytor, typowa luka, podstawa prawna |
| `next_steps` | Lista pierwszych kroków naprawczych, od najsłabszego miejsca |

## Osiem obszarów

1. Inwentaryzacja i zakres, RODO art. 30, NIS2 art. 21 ust. 2 lit. a
2. Kontrola dostępu i konta, RODO art. 32 ust. 1 lit. b
3. Kopie zapasowe i odtwarzanie, RODO art. 32 ust. 1 lit. c i d
4. Incydenty i zgłaszanie, RODO art. 33 i 34, NIS2 art. 23
5. Dokumentacja RODO, RODO art. 5 ust. 2, 30, 32, 35
6. Dostawcy i powierzenie, RODO art. 28
7. Ludzie i świadomość, NIS2 art. 20 ust. 2
8. Minimum techniczne, RODO art. 32 ust. 1, NIS2 art. 21 ust. 2

Punktacja: tak 2, częściowo 1, nie 0, nie wiem 0. Maksimum 60 punktów. Progi: 50 dojrzałość wysoka, 38 dobry poziom z brakami w dowodach, 22 podstawy z dużymi lukami, poniżej luka krytyczna. Obszar poniżej 60 procent jest oznaczany jako luka.

Odpowiedź "nie wiem" liczy się jak "nie", bo brak wiedzy o własnym zabezpieczeniu jest brakiem zabezpieczenia. To założenie metodologiczne, nie uproszczenie.

## Instalacja

```bash
git clone https://github.com/BrokerBusiness-ai/skan-zgodnosci-mcp.git
cd skan-zgodnosci-mcp
pip install -e .
```

Konfiguracja w kliencie MCP (Claude Desktop, `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "skan-zgodnosci": {
      "command": "skan-zgodnosci-mcp"
    }
  }
}
```

Albo bez instalacji pakietu:

```json
{
  "mcpServers": {
    "skan-zgodnosci": {
      "command": "python",
      "args": ["-m", "skan_mcp.server"],
      "cwd": "/sciezka/do/skan-zgodnosci-mcp"
    }
  }
}
```

## Przykład

```python
score_scan(
  odpowiedzi={"1": "tak", "2": "czesciowo", "3": "nie", ...},
  potrzeby={"4": "tak", "6": "tak"}
)
```

Zwraca punkty, poziom, tabelę ośmiu obszarów z procentami, opisy luk dla obszarów poniżej 60 procent i rekomendacje dopasowane do zgłoszonych potrzeb.

## Prywatność

Serwer nie ma połączenia sieciowego. Nie wysyła odpowiedzi nigdzie, nie zapisuje ich na dysku i nie prowadzi telemetrii. Odpowiedzi istnieją tylko w kontekście rozmowy z asystentem.

## Autor

**Marek Porycki**, psycholog (specjalność kliniczna), mediator sądowy, prezes zarządu Broker Business sp. z o.o. w Białymstoku. Prowadzi audyty i szkolenia z RODO oraz bezpieczeństwa informacji, buduje narzędzia AI dla firm.

- [skanujfirme.pl](https://skanujfirme.pl), narzędzia i artykuły o audycie firmy
- [archaios.ai](https://archaios.ai), platforma produktów AI do zgodności
- [brokerbusiness.eu](https://brokerbusiness.eu), szkolenia i doradztwo

Skala powstała z praktyki audytowej: te pytania zadaje się w pierwszej godzinie audytu i to na nie najczęściej nie ma odpowiedzi.

## Licencja

Korzystanie bezpłatne z zachowaniem atrybucji. Wdrożenia komercyjne i redystrybucja zmodyfikowanej skali wymagają pisemnej zgody autora. Szczegóły w pliku [LICENSE](LICENSE).

Serwer weryfikuje sumę kontrolną metodologii. Jeśli plik z pytaniami został zmieniony, każda odpowiedź zawiera ostrzeżenie, że wynik nie pochodzi z wersji autorskiej.

---

# Compliance Scan MCP (English)

MCP server exposing a screening scale for information security and regulatory compliance (GDPR, NIS2) aimed at small and medium companies in Poland. No API key, no registration, no network calls: scoring runs locally.

Thirty scored questions across eight areas, plus twelve needs questions that drive recommendations. Answers map to 2 / 1 / 0 points, maximum 60. "Don't know" scores zero by design, because not knowing whether a control exists is the same risk as not having it.

Tools: `get_methodology`, `get_questionnaire`, `score_scan`, `explain_area`, `next_steps`.

Each response carries attribution and a checksum of the methodology file, so a modified scale cannot be presented as the original.

Author: **Marek Porycki**, psychologist (clinical track), court mediator, CEO of Broker Business sp. z o.o., Białystok. Runs GDPR and security audits and training, builds AI tools for companies. Free to use with attribution; commercial deployment requires written permission, see [LICENSE](LICENSE).
