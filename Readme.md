# Test rozumowania

Prosta aplikacja internetowa do rozwiązywania autorskiego quizu z rozumowania. Uczestnik podaje imię lub pseudonim i przedział wiekowy, przechodzi pytania pojedynczo, może wracać do poprzednich, a na końcu zapisuje wynik. Aplikacja pokazuje zdobyte punkty, procent oraz średnią wcześniejszych wyników z tej samej grupy wiekowej.

> Quiz ma charakter edukacyjny i rozrywkowy. Nie jest standaryzowanym testem psychologicznym, testem IQ ani diagnozą.

## Uruchomienie

Aplikacja wymaga Python 3 i nie potrzebuje dodatkowych bibliotek. Wybierz jedną z poniższych metod i uruchamiaj tylko jedną instancję na danej bazie.

### Windows (PowerShell)

1. Zainstaluj Python 3 dla Windows i zaznacz podczas instalacji opcję **Add python.exe to PATH**.
2. Umieść projekt w zwykłym lokalnym katalogu Windows, np. `C:\Users\TwojaNazwa\test-inteligencji`. Nie uruchamiaj Windowsowego Pythona ze ścieżki `\\wsl.localhost\...`; SQLite powinno trzymać bazę lokalnie na dysku Windows.
3. W PowerShellu przejdź do katalogu projektu i uruchom serwer:

```powershell
cd "$env:USERPROFILE\test-inteligencji"
$env:ADMIN_PASSWORD = "ustaw-wlasne-haslo"
py -3 app.py
```

Jeśli polecenie `py` nie jest dostępne, użyj `python app.py`.

### WSL (serwer działa w Linuksie, przeglądarka w Windows)

1. Umieść projekt na linuksowym dysku WSL, np. w `/home/TwojaNazwa/test-inteligencji`. Unikaj katalogu `/mnt/c` dla pliku bazy.
2. Otwórz terminal WSL i uruchom:

```bash
cd ~/test-inteligencji
ADMIN_PASSWORD='ustaw-wlasne-haslo' python3 app.py
```

3. Pozostaw terminal z serwerem otwarty i w przeglądarce Windows wejdź na `http://localhost:8000`.
4. Jeśli `localhost` z Windows nie przekierowuje do WSL, zatrzymaj serwer (`Ctrl+C`), uruchom go ponownie z nasłuchem na interfejsach WSL i otwórz adres IP WSL:

```bash
HOST=0.0.0.0 ADMIN_PASSWORD='ustaw-wlasne-haslo' python3 app.py
hostname -I
```

W Windows otwórz `http://ADRES_IP_WSL:8000` (wstaw adres pokazany przez `hostname -I`). Przy tym wariancie port jest dostępny w sieci WSL; używaj go tylko w zaufanej sieci i zatrzymuj serwer po zakończeniu pracy.

W obu wariantach zatrzymaj serwer klawiszem `Ctrl+C`. Domyślny port to `8000`; można go zmienić przez zmienną `PORT`, np. `PORT=8080` w WSL albo `$env:PORT = "8080"` w PowerShellu.

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

### Pomiar czasu

Po kliknięciu „Rozpocznij test” (po uzupełnieniu danych uczestnika) uruchamia się widoczny licznik w formacie minuty:sekundy. Pomiar kończy kliknięcie „Wyślij test” przy komplecie odpowiedzi. Obejmuje przechodzenie wstecz, przerwy i czas spędzony w innej karcie; nie obejmuje oczekiwania na zapis wyniku. Po błędzie wysyłania pomiar jest wznawiany i obejmuje czas do kolejnej próby. Nowe rozpoczęcie testu zeruje licznik, a odświeżenie strony wymaga rozpoczęcia od nowa.

Czas jest wyświetlany w podsumowaniu i panelu „Wyniki” oraz zapisywany w bazie jako `duration_ms` (milisekundy). Kolumna jest dodawana automatycznie do istniejącej bazy; wcześniejsze wyniki mają brak czasu, wyświetlany jako „—”. Pomiar korzysta z zegara monotonicznego przeglądarki i jest przesyłany przez klienta, więc nie jest zabezpieczony przed manipulacją. Obecna punktacja i średnie procentowe pozostają bez zmian.

### Propozycja punktacji uwzględniającej czas — do rozważenia

Proponowany dodatkowy wskaźnik sprawności: `W = P × (0,8 + 0,2 × min(1, T_ref / T))`, gdzie `P` to obecny wynik procentowy, `T` to czas testu, a `T_ref` to czas referencyjny. Dla czasu zerowego nie wyliczamy wskaźnika. Wynik mieści się w zakresie 0–100; szybkość nie daje punktów za błędne odpowiedzi. Przy czasie do `T_ref` wskaźnik jest równy `P`, a dłuższy czas obniża go najwyżej o 20% wartości `P`.

Przykład wyłącznie ilustracyjny: dla `T_ref = 10 minut` i wyniku 80% wskaźnik wyniesie 80 przy czasie 8 lub 10 minut, 74,7 przy 15 minutach oraz 72 przy 20 minutach. Wagę 20% i czas referencyjny trzeba sprawdzić na zebranych danych; 10 minut nie jest ustaloną normą. Można wyznaczać `T_ref` jako medianę czasu kompletnych, poprawnie zapisanych prób w danej grupie wiekowej i tej samej wersji testu, po zebraniu np. 30 takich prób, z wykluczeniem udokumentowanych zakłóceń pomiaru. Do tego czasu prezentować wyłącznie punkty i czas osobno.

Przed wdrożeniem należy ustalić sposób traktowania przerw, potrzeb dostępności oraz wersjonowania wzoru i czasu referencyjnego. Należy zachować osobno surowe punkty, procent i czas, aby porównania były czytelne i możliwe do ponownego przeliczenia. To propozycja wskaźnika dla quizu edukacyjnego, a nie norma psychologiczna ani pomiar IQ. **Wzór nie jest obecnie zaimplementowany.**

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
