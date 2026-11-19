# Test rozumowania

Prosta aplikacja internetowa do rozwiązywania autorskiego quizu z rozumowania. Uczestnik podaje imię lub pseudonim i przedział wiekowy, przechodzi pytania pojedynczo, może wracać do poprzednich, a na końcu zapisuje wynik. Aplikacja pokazuje zdobyte punkty, procent oraz średnią wcześniejszych wyników z tej samej grupy wiekowej.

> Quiz ma charakter edukacyjny i rozrywkowy. Nie jest standaryzowanym testem psychologicznym, testem IQ ani diagnozą.

## Uruchomienie

Wymagany jest Python 3. Nie są potrzebne dodatkowe biblioteki.

```bash
ADMIN_PASSWORD='ustaw-wlasne-haslo' python3 app.py
```

Otwórz `http://127.0.0.1:8000`. Port można zmienić zmienną `PORT`, a adres nasłuchiwania zmienną `HOST`, na przykład:

```bash
HOST=0.0.0.0 PORT=8080 ADMIN_PASSWORD='ustaw-wlasne-haslo' python3 app.py
```

Panel „Wyniki” wymaga hasła ustawionego przez `ADMIN_PASSWORD`. Jeśli hasło nie jest ustawione, dostęp do wyników jest zamknięty. Przy wystawianiu aplikacji poza lokalną maszynę należy używać HTTPS i mocnego hasła.

## Pytania i punktacja

Każde podejście zawiera 20 pytań: z każdej z czterech kategorii losowane są trzy łatwe i dwa umiarkowane pytania. Test korzysta z banku pytań tekstowych i autorskich macierzy obrazkowych w SVG.

Kategorie:

- ciągi i reguły,
- matematyka,
- wzory i uzupełnianie,
- wyobraźnia przestrzenna.

Pytania łatwe dają 1 punkt, umiarkowane — 2 punkty. Maksimum w każdym podejściu wynosi `12 × 1 + 8 × 2 = 28 punktów`; procent jest liczony jako zdobyte punkty podzielone przez 28.

Test jest celowo łagodniejszy niż pierwotna propozycja: nie losuje poziomów „bardzo trudny” i „ekspert”.

## Dane i średnia grupy

Wyniki są przechowywane w pliku `results.db` w katalogu aplikacji (SQLite). Można wskazać inną lokalizację przez `TEST_DB_PATH`. Uruchamiaj aplikację i bazę na tym samym systemie plików co interpreter: przy Windows trzymaj projekt na dysku Windows, a przy WSL na linuksowym dysku WSL. Unikaj ścieżek `\\wsl.localhost\...` dla procesu Windows oraz OneDrive i dysków sieciowych. Baza zapisuje imię/pseudonim, grupę wiekową, punkty, procent, odpowiedzi i czas wysłania.

SQLite czeka do 15 sekund na zwolnienie chwilowej blokady. Uruchamiaj tylko jedną kopię aplikacji na tej samej bazie. Przy pracy z Windows i WSL trzymaj bazę na lokalnym dysku systemu, na którym działa serwer; nie kieruj `TEST_DB_PATH` do folderu synchronizowanego z OneDrive ani do sieciowego dysku. W WSL ustaw bazę np. na `~/test-inteligencji/results.db`; w Windows używaj folderu lokalnego, np. `C:\\Users\\<nazwa>\\test-inteligencji\\results.db`.

Przed zapisaniem nowego podejścia aplikacja pobiera średnią procentową z wcześniejszych podejść tej grupy wiekowej. Nowy wynik nie wpływa na średnią wyświetloną temu uczestnikowi. Dla pierwszej osoby w grupie pokazuje się informacja, że brak wcześniejszych wyników. Średnia nie jest normą populacyjną — zależy wyłącznie od osób, które wypełniły ten quiz w tej bazie.

## Prywatność i ograniczenia

- Panel wyników chroni hasło administratora; nie należy udostępniać aplikacji publicznie bez HTTPS.
- Nie zbieraj danych osobowych, jeśli wystarczy pseudonim. Ustal własną politykę retencji i kasowania bazy stosownie do sposobu użycia.
- Obecna wersja nie ma kont użytkowników, limitu prób ani ochrony przed wielokrotnymi zgłoszeniami. Zapisane odpowiedzi nie są pokazywane w panelu.
- Macierze obrazkowe są autorskimi, osadzonymi grafikami SVG; aplikacja nie pobiera cudzych ilustracji z testów ani nie zależy od zewnętrznych obrazów.

## Pliki

- `app.py` — serwer HTTP, API, pula pytań, logika punktacji i schemat SQLite; cały interfejs jest osadzony w pliku.
- `results.db` — baza tworzona automatycznie po pierwszym uruchomieniu.
