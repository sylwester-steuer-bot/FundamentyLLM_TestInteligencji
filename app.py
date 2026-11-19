#!/usr/bin/env python3
"""Prosty test rozumowania z lokalnym zapisem wyników do SQLite."""

from __future__ import annotations

import json
import os
import random
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("TEST_DB_PATH", ROOT / "results.db"))
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
AGES = {"0-20", "21-40", "41-60", "61-80", "81-100"}

# Bank ma po pięć zadań dla każdej kombinacji kategorii i poziomu trudności.
# Każde podejście losuje po jednym z nich; dodatkowe pytania są z jednego poziomu.
# Każde pytanie ma dokładnie jedną poprawną odpowiedź.
QUESTIONS = [
    {"category":"Ciągi i reguły", "level":"Łatwe", "points":1, "prompt":"Jaka liczba powinna być następna? 2, 4, 6, 8, …", "options":["9","10","12","16"], "answer":1},
    {"category":"Ciągi i reguły", "level":"Łatwe", "points":1, "prompt":"Jaka litera powinna być następna? A, C, E, G, …", "options":["H","I","J","K"], "answer":1},
    {"category":"Ciągi i reguły", "level":"Łatwe", "points":1, "prompt":"Który element nie pasuje do pozostałych?", "options":["Koło","Kwadrat","Trójkąt","Marchew"], "answer":3},
    {"category":"Ciągi i reguły", "level":"Łatwe", "points":1, "prompt":"Jaka liczba powinna być następna? 5, 10, 15, 20, …", "options":["22","24","25","30"], "answer":2},
    {"category":"Ciągi i reguły", "level":"Łatwe", "points":1, "prompt":"Dokończ wzór: czerwony, niebieski, czerwony, niebieski, …", "options":["Czerwony","Zielony","Niebieski","Żółty"], "answer":0},
    {"category":"Ciągi i reguły", "level":"Trudne", "points":2, "prompt":"Jaka liczba powinna być następna? 3, 6, 12, 24, …", "options":["36","42","48","54"], "answer":2},
    {"category":"Ciągi i reguły", "level":"Trudne", "points":2, "prompt":"Jaka liczba powinna być następna? 1, 4, 9, 16, …", "options":["20","24","25","36"], "answer":2},
    {"category":"Ciągi i reguły", "level":"Trudne", "points":2, "prompt":"Jaka litera powinna być następna? Z, X, U, Q, …", "options":["M","L","N","K"], "answer":1},
    {"category":"Ciągi i reguły", "level":"Trudne", "points":2, "prompt":"Znajdź kolejną liczbę: 2, 5, 11, 23, …", "options":["35","45","46","47"], "answer":3},
    {"category":"Ciągi i reguły", "level":"Trudne", "points":2, "prompt":"Uzupełnij analogię: ręka ma się do dłoni tak, jak noga ma się do …", "options":["Kolana","Stopy","Biodra","Palców"], "answer":1},
    {"category":"Ciągi i reguły", "level":"Bardzo trudne", "points":3, "prompt":"Jaka liczba powinna być następna? 1, 2, 6, 24, 120, …", "options":["480","600","720","840"], "answer":2},
    {"category":"Ciągi i reguły", "level":"Bardzo trudne", "points":3, "prompt":"Znajdź kolejną liczbę: 4, 7, 13, 25, 49, …", "options":["73","95","97","99"], "answer":2},
    {"category":"Ciągi i reguły", "level":"Bardzo trudne", "points":3, "prompt":"Jaka litera powinna być następna? B, E, J, Q, …", "options":["X","Y","Z","A"], "answer":2},
    {"category":"Ciągi i reguły", "level":"Bardzo trudne", "points":3, "prompt":"Znajdź kolejną liczbę: 2, 3, 5, 9, 17, …", "options":["25","31","33","34"], "answer":2},
    {"category":"Ciągi i reguły", "level":"Bardzo trudne", "points":3, "prompt":"Znajdź kolejną liczbę: 1, 3, 6, 10, 15, …", "options":["18","20","21","25"], "answer":2},
    {"category":"Ciągi i reguły", "level":"Ekspert", "points":4, "prompt":"Znajdź kolejną liczbę: 1, 2, 5, 14, 41, …", "options":["82","122","123","124"], "answer":2},
    {"category":"Ciągi i reguły", "level":"Ekspert", "points":4, "prompt":"Znajdź kolejną liczbę: 2, 6, 15, 31, 56, …", "options":["82","87","92","96"], "answer":2},
    {"category":"Ciągi i reguły", "level":"Ekspert", "points":4, "prompt":"Jaka litera powinna być następna? A, B, D, G, K, …", "options":["O","P","Q","R"], "answer":1},
    {"category":"Ciągi i reguły", "level":"Ekspert", "points":4, "prompt":"Znajdź kolejną liczbę: 3, 4, 7, 11, 18, 29, …", "options":["42","45","47","49"], "answer":2},
    {"category":"Ciągi i reguły", "level":"Ekspert", "points":4, "prompt":"Jaka liczba powinna być następna? 2, 3, 5, 9, 17, 33, …", "options":["49","57","64","65"], "answer":3},
    {"category":"Matematyka", "level":"Łatwe", "points":1, "prompt":"Ile wynosi 7 + 5?", "options":["11","12","13","14"], "answer":1},
    {"category":"Matematyka", "level":"Łatwe", "points":1, "prompt":"Ile wynosi 9 × 3?", "options":["18","21","27","36"], "answer":2},
    {"category":"Matematyka", "level":"Łatwe", "points":1, "prompt":"Ile wynosi połowa z 36?", "options":["16","18","20","24"], "answer":1},
    {"category":"Matematyka", "level":"Łatwe", "points":1, "prompt":"Trzy zeszyty kosztują po 4 zł. Ile kosztują razem?", "options":["7 zł","8 zł","12 zł","16 zł"], "answer":2},
    {"category":"Matematyka", "level":"Łatwe", "points":1, "prompt":"Ile wynosi 100 − 37?", "options":["53","63","67","73"], "answer":1},
    {"category":"Matematyka", "level":"Trudne", "points":2, "prompt":"Ile wynosi 15% z 200?", "options":["20","25","30","35"], "answer":2},
    {"category":"Matematyka", "level":"Trudne", "points":2, "prompt":"Rozwiąż: 3x + 5 = 20.", "options":["3","5","7","8"], "answer":1},
    {"category":"Matematyka", "level":"Trudne", "points":2, "prompt":"Samochód jedzie 60 km/h przez 2,5 godziny. Jaki dystans pokona?", "options":["120 km","140 km","150 km","180 km"], "answer":2},
    {"category":"Matematyka", "level":"Trudne", "points":2, "prompt":"Ile wynosi 3/4 z 80?", "options":["40","50","60","70"], "answer":2},
    {"category":"Matematyka", "level":"Trudne", "points":2, "prompt":"Prostokąt ma boki 8 cm i 5 cm. Jaki jest jego obwód?", "options":["13 cm","26 cm","40 cm","80 cm"], "answer":1},
    {"category":"Matematyka", "level":"Bardzo trudne", "points":3, "prompt":"Rozwiąż: 2(x − 3) = 18.", "options":["6","9","12","15"], "answer":2},
    {"category":"Matematyka", "level":"Bardzo trudne", "points":3, "prompt":"Cena 250 zł wzrosła o 20%. Jaka jest nowa cena?", "options":["270 zł","290 zł","300 zł","320 zł"], "answer":2},
    {"category":"Matematyka", "level":"Bardzo trudne", "points":3, "prompt":"Średnia liczb 6, 8, 10 i x wynosi 9. Ile wynosi x?", "options":["10","11","12","13"], "answer":2},
    {"category":"Matematyka", "level":"Bardzo trudne", "points":3, "prompt":"Rzut uczciwą kostką daje wynik parzysty. Jakie jest prawdopodobieństwo, że wynik to 6?", "options":["1/6","1/3","1/2","2/3"], "answer":1},
    {"category":"Matematyka", "level":"Bardzo trudne", "points":3, "prompt":"Trójkąt ma kąty 45° i 65°. Ile wynosi trzeci kąt?", "options":["60°","70°","80°","90°"], "answer":1},
    {"category":"Matematyka", "level":"Ekspert", "points":4, "prompt":"Rozwiąż: x² − 5x + 6 = 0. Która para jest rozwiązaniem?", "options":["1 i 6","2 i 3","−2 i −3","3 i 5"], "answer":1},
    {"category":"Matematyka", "level":"Ekspert", "points":4, "prompt":"Ile wynosi suma kątów wewnętrznych siedmiokąta?", "options":["720°","900°","1080°","1260°"], "answer":1},
    {"category":"Matematyka", "level":"Ekspert", "points":4, "prompt":"W pudełku są 3 czerwone i 2 niebieskie kule. Jakie jest prawdopodobieństwo wylosowania dwóch czerwonych bez zwracania?", "options":["1/5","3/10","2/5","3/5"], "answer":1},
    {"category":"Matematyka", "level":"Ekspert", "points":4, "prompt":"Rozwiąż układ: x + y = 11 oraz 2x − y = 7. Ile wynosi x?", "options":["4","5","6","7"], "answer":2},
    {"category":"Matematyka", "level":"Ekspert", "points":4, "prompt":"W ciągu geometrycznym a₁ = 3, a₄ = 81, a iloraz jest dodatni. Ile wynosi a₆?", "options":["243","486","729","1458"], "answer":2},
    {"category":"Wzory i uzupełnianie", "level":"Łatwe", "points":1, "prompt":"Który kształt uzupełnia wzór? ○, □, ○, □, …", "options":["Koło ○","Kwadrat □","Trójkąt △","Gwiazda ☆"], "answer":0},
    {"category":"Wzory i uzupełnianie", "level":"Łatwe", "points":1, "prompt":"W każdym wierszu jest koło, kwadrat i trójkąt. Wiersz 1: ○ □ △; wiersz 2: □ △ ○; wiersz 3: △ ○ ?", "options":["○","□","△","☆"], "answer":1},
    {"category":"Wzory i uzupełnianie", "level":"Łatwe", "points":1, "prompt":"Uzupełnij sekwencję: ▲, ▲, ●, ▲, ▲, ●, …", "options":["▲","●","■","○"], "answer":0},
    {"category":"Wzory i uzupełnianie", "level":"Łatwe", "points":1, "prompt":"W każdym kroku dodajemy jeden punkt: •, ••, •••, … Co będzie dalej?", "options":["••","•••","••••","•••••"], "answer":2},
    {"category":"Wzory i uzupełnianie", "level":"Łatwe", "points":1, "prompt":"Strzałka obraca się kolejno w prawo, w dół, w lewo. Co dalej? →, ↓, ←, …", "options":["↑","→","↓","←"], "answer":0},
    {"category":"Wzory i uzupełnianie", "level":"Trudne", "points":2, "prompt":"Liczba elementów rośnie o 1 w każdym wierszu: ■; ■■; ■■■; … Co w czwartym?", "options":["■■","■■■","■■■■","■■■■■"], "answer":2},
    {"category":"Wzory i uzupełnianie", "level":"Trudne", "points":2, "prompt":"Każdy kolejny symbol ma o jedno ramię więcej: +, ✳ (6 ramion), ✴ (8 ramion). Jaki symbol powinien być następny?", "options":["Symbol z 9 ramionami","Symbol z 10 ramionami","Symbol z 11 ramionami","Symbol z 12 ramionami"], "answer":1},
    {"category":"Wzory i uzupełnianie", "level":"Trudne", "points":2, "prompt":"W każdej kolumnie symbol przesuwa się o jedno pole w dół: ○ □ △ / △ ○ □ / □ △ ?", "options":["○","□","△","☆"], "answer":0},
    {"category":"Wzory i uzupełnianie", "level":"Trudne", "points":2, "prompt":"W każdym kolejnym kroku zamalowujemy jeszcze jeden z czterech pól. Ile pól zostanie pustych po trzech krokach?", "options":["0","1","2","3"], "answer":1},
    {"category":"Wzory i uzupełnianie", "level":"Trudne", "points":2, "prompt":"Wzór powtarza się co trzy symbole: ○ △ □ ○ △ □ … Który będzie 8. symbolem?", "options":["○","△","□","☆"], "answer":1},
    {"category":"Wzory i uzupełnianie", "level":"Bardzo trudne", "points":3, "prompt":"W każdym wierszu trzeci symbol łączy cechy dwóch pierwszych: małe koło + duży kwadrat = mały kwadrat; duży trójkąt + małe koło = duże koło; mały kwadrat + duży trójkąt = ?", "options":["Mały trójkąt","Duży kwadrat","Mały kwadrat","Duże koło"], "answer":0},
    {"category":"Wzory i uzupełnianie", "level":"Bardzo trudne", "points":3, "prompt":"W każdym wierszu liczba kropek w trzeciej figurze jest sumą kropek w dwóch pierwszych: 1 + 2 = 3; 2 + 3 = 5; 4 + 1 = ?", "options":["4","5","6","7"], "answer":1},
    {"category":"Wzory i uzupełnianie", "level":"Bardzo trudne", "points":3, "prompt":"W kratownicy 2×2 czarne pola przesuwają się o jedno pole zgodnie z ruchem wskazówek zegara. Zaczynamy od pola górnego lewego. Gdzie będzie czarne pole w czwartym kroku?", "options":["Górne lewe","Górne prawe","Dolne lewe","Dolne prawe"], "answer":0},
    {"category":"Wzory i uzupełnianie", "level":"Bardzo trudne", "points":3, "prompt":"W szeregu liczba kresek rośnie: |, ||, ||||, |||||||. Ile kresek będzie w następnym elemencie?", "options":["9","10","11","12"], "answer":2},
    {"category":"Wzory i uzupełnianie", "level":"Bardzo trudne", "points":3, "prompt":"Symbole w wierszu zmieniają się kolejno: koło, trójkąt, kwadrat. Wiersze przesuwają wzór o jedną pozycję: ○ △ □ / △ □ ○ / □ ○ ?", "options":["○","△","□","☆"], "answer":1},
    {"category":"Wzory i uzupełnianie", "level":"Ekspert", "points":4, "prompt":"W kratownicy 3×3 symbol przesuwa się o jedno pole w prawo w każdym wierszu, z zawijaniem do początku. Jeśli startuje w górnym lewym polu, gdzie będzie w trzecim wierszu?", "options":["Górne lewe","Środkowe prawe","Dolne prawe","Dolne lewe"], "answer":2},
    {"category":"Wzory i uzupełnianie", "level":"Ekspert", "points":4, "prompt":"W każdym kroku zamieniamy kolor na przeciwny i obracamy figurę o 90°. Start: czarny trójkąt skierowany w górę. Jaki będzie po 3 krokach?", "options":["Czarny, w prawo","Biały, w dół","Czarny, w lewo","Biały, w prawo"], "answer":3},
    {"category":"Wzory i uzupełnianie", "level":"Ekspert", "points":4, "prompt":"Wzór siatki: ○ ● ● / ● ○ ● / ● ● ? W każdym wierszu i kolumnie jest jedno puste koło. Co zastępuje znak zapytania?", "options":["○","●","□","△"], "answer":0},
    {"category":"Wzory i uzupełnianie", "level":"Ekspert", "points":4, "prompt":"Liczby w trójkącie: na górze 2; w następnym rzędzie 3, 5; na dole 4, 8, 13. Każda liczba powstaje przez dodanie liczby nad nią do poprzedniej liczby z rzędu. Jaka liczba powinna być na końcu kolejnego rzędu?", "options":["18","20","21","26"], "answer":2},
    {"category":"Wzory i uzupełnianie", "level":"Ekspert", "points":4, "prompt":"Sekwencja symboli i liczb: ○1, △2, □4, ○8, △16, … Który będzie kolejny element?", "options":["□24","○32","□32","△32"], "answer":2},
    {"category":"Wyobraźnia przestrzenna", "level":"Łatwe", "points":1, "prompt":"Strzałkę → obrócono o 90° w prawo. W którą stronę wskazuje?", "options":["↑","↓","←","→"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Łatwe", "points":1, "prompt":"Kwadrat obrócono o 45°. Jaki kształt widzisz?", "options":["Koło","Wciąż kwadrat, tylko obrócony","Trójkąt","Prostokąt"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Łatwe", "points":1, "prompt":"Na kostce przeciwległe ściany to 1–6, 2–5 i 3–4. Co leży naprzeciw 2?", "options":["3","4","5","6"], "answer":2},
    {"category":"Wyobraźnia przestrzenna", "level":"Łatwe", "points":1, "prompt":"Lustrzane odbicie litery F względem pionowej osi znajduje się po jej prawej stronie. W którą stronę skierowane są krótkie kreski?", "options":["W prawo","W lewo","W dół","Nie zmieniają kierunku"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Łatwe", "points":1, "prompt":"Ile wierzchołków ma sześcian?", "options":["6","8","10","12"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Trudne", "points":2, "prompt":"Strzałkę ↑ obrócono o 180°. W którą stronę wskazuje?", "options":["↑","→","↓","←"], "answer":2},
    {"category":"Wyobraźnia przestrzenna", "level":"Trudne", "points":2, "prompt":"Złożono papier na pół, przebito jeden otwór z dala od zgięcia, a potem rozłożono. Ile będzie otworów?", "options":["1","2","3","4"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Trudne", "points":2, "prompt":"Duży sześcian pomalowano z zewnątrz i podzielono na 27 równych małych sześcianów. Ile małych kostek ma dokładnie dwie pomalowane ściany?", "options":["8","12","16","20"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Trudne", "points":2, "prompt":"Który kształt po obrocie o 180° wygląda identycznie?", "options":["Litera F","Litera N","Litera L","Strzałka →"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Trudne", "points":2, "prompt":"Sześcian ma na górze 1, z przodu 2 i po prawej 3. Ile wynosi liczba na ścianie z tyłu, jeśli jest naprzeciw przedniej, a przeciwległe ściany sumują się do 7?", "options":["4","5","6","Nie da się ustalić"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Bardzo trudne", "points":3, "prompt":"Sześcian pomalowano z zewnątrz i pocięto na 64 jednakowe kostki (4×4×4). Ile kostek nie ma żadnej pomalowanej ściany?", "options":["0","4","8","16"], "answer":2},
    {"category":"Wyobraźnia przestrzenna", "level":"Bardzo trudne", "points":3, "prompt":"Kostka ma na górze 1, z przodu 2, po prawej 3. Obracamy ją tak, że przednia ściana trafia na górę, górna na tył, tylna na dół, a dolna do przodu. Co jest teraz na górze?", "options":["1","2","3","Nie da się ustalić"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Bardzo trudne", "points":3, "prompt":"Prostokąt 2×3 składa się z sześciu kwadratów. Ile krawędzi ma jego obwód jednostkowy?", "options":["8","10","12","14"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Bardzo trudne", "points":3, "prompt":"Sześcian 3×3×3 pomalowano i pocięto. Ile małych kostek ma dokładnie jedną pomalowaną ścianę?", "options":["6","8","12","24"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Bardzo trudne", "points":3, "prompt":"Litera L składa się z dwóch jednakowych odcinków spotykających się pod kątem prostym. Obrócono ją o 90° w prawo. Który kierunek ma teraz pionowy odcinek, który wcześniej był poziomy skierowany w prawo od narożnika?", "options":["W górę","W dół","W lewo","W prawo"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Ekspert", "points":4, "prompt":"Sześcian 5×5×5 pomalowano i pocięto na małe kostki. Ile małych kostek ma dokładnie dwie pomalowane ściany?", "options":["24","36","48","54"], "answer":2},
    {"category":"Wyobraźnia przestrzenna", "level":"Ekspert", "points":4, "prompt":"Sześcian ma 1 na górze, 2 z przodu i 3 po prawej; 6 leży naprzeciw 1, 5 naprzeciw 2, 4 naprzeciw 3. Obróć sześcian tak, by prawa ściana znalazła się na górze. Co będzie na dole?", "options":["1","2","4","6"], "answer":2},
    {"category":"Wyobraźnia przestrzenna", "level":"Ekspert", "points":4, "prompt":"Ile różnych siatek sześcianu istnieje, jeśli odbicia lustrzane i obroty uznajemy za ten sam kształt?", "options":["9","11","12","14"], "answer":1},
    {"category":"Wyobraźnia przestrzenna", "level":"Ekspert", "points":4, "prompt":"Sześcian 6×6×6 pomalowano i pocięto. Ile małych kostek ma dokładnie jedną pomalowaną ścianę?", "options":["48","54","64","96"], "answer":2},
    {"category":"Wyobraźnia przestrzenna", "level":"Ekspert", "points":4, "prompt":"Kostka ma na górze 1, z przodu 2 i po prawej 3; ściany przeciwległe sumują się do 7. Obracamy ją tak, że górna ściana trafia na przód, przednia na dół, a dolna na tył. Co jest teraz na przodzie?", "options":["1","2","3","6"], "answer":0},
]

assert len(QUESTIONS) == 80
LEVELS = ["Łatwe", "Umiarkowane"]

def svg_card(shapes: list[str]) -> str:
    """Render a 3x3 visual matrix with the last cell intentionally missing."""
    cells = []
    for i, shape in enumerate(shapes):
        x, y = 8 + (i % 3) * 62, 8 + (i // 3) * 62
        if shape == "?":
            content = '<text x="31" y="41" text-anchor="middle" font-size="27" font-weight="700" fill="#65748a">?</text>'
        elif shape == "circle":
            content = '<circle cx="31" cy="31" r="13" fill="#4d70db"/>'
        elif shape == "square":
            content = '<rect x="18" y="18" width="26" height="26" rx="3" fill="#4d70db"/>'
        elif shape == "triangle":
            content = '<path d="M31 15 L47 45 H15 Z" fill="#4d70db"/>'
        elif shape == "diamond":
            content = '<path d="M31 14 L48 31 L31 48 L14 31 Z" fill="#4d70db"/>'
        elif shape == "bars":
            content = '<path d="M18 18v26 M27 18v26 M36 18v26 M45 18v26" stroke="#4d70db" stroke-width="5"/>'
        elif shape == "dots":
            content = '<circle cx="23" cy="23" r="4" fill="#4d70db"/><circle cx="39" cy="23" r="4" fill="#4d70db"/><circle cx="23" cy="39" r="4" fill="#4d70db"/><circle cx="39" cy="39" r="4" fill="#4d70db"/>'
        elif shape == "hollow":
            content = '<circle cx="31" cy="31" r="13" fill="none" stroke="#4d70db" stroke-width="4"/>'
        elif shape == "half":
            content = '<path d="M31 17a14 14 0 1 0 0 28z" fill="#4d70db"/><path d="M31 17a14 14 0 0 1 0 28z" fill="#b5c6fa"/>'
        else:
            content = '<path d="M31 16 L35 27 L47 27 L38 34 L41 46 L31 39 L21 46 L24 34 L15 27 L27 27 Z" fill="#4d70db"/>'
        cells.append(f'<g transform="translate({x},{y})"><rect width="56" height="56" rx="7" fill="#f3f6fc" stroke="#cbd5e3"/>{content}</g>')
    return '<svg viewBox="0 0 196 196" role="img" aria-label="Macierz obrazkowa z brakującym polem" style="display:block;width:min(100%,260px);margin:18px auto">' + ''.join(cells) + '</svg>'


def add_matrix_questions() -> None:
    matrix_bank = [
        ("Koło, kwadrat, koło / kwadrat, koło, kwadrat / koło, kwadrat, ?", ["circle","square","circle","square","circle","square","circle","square","?"], ["Koło", "Kwadrat", "Trójkąt", "Gwiazda"], 0),
        ("W każdym wierszu występuje kolejno koło, kwadrat i trójkąt. Jaki kształt uzupełnia pole?", ["circle","square","triangle","square","triangle","circle","triangle","circle","?"], ["Koło", "Kwadrat", "Trójkąt", "Gwiazda"], 2),
        ("W każdej kolumnie występują te same kształty od góry: koło, kwadrat, trójkąt. Co powinno być na dole ostatniej kolumny?", ["circle","square","triangle","circle","square","triangle","circle","square","?"], ["Koło", "Kwadrat", "Trójkąt", "Gwiazda"], 2),
        ("W każdym wierszu figura przesuwa się z lewej kolumny do środkowej, a potem prawej. Które pole jest brakujące?", ["circle","square","triangle","square","triangle","circle","triangle","circle","?"], ["Koło", "Kwadrat", "Trójkąt", "Gwiazda"], 0),
        ("W każdym wierszu pojawia się kolejno figura pełna, pusta i półkolorowa. Co powinno być w ostatnim polu?", ["circle","hollow","half","square","hollow","half","triangle","hollow","?"], ["Figura pełna", "Figura pusta", "Figura półkolorowa", "Cztery kropki"], 2),
        ("W każdym wierszu symbol przesuwa się o jedno pole w prawo. Który symbol powinien znaleźć się na końcu?", ["triangle","circle","square","circle","square","triangle","square","triangle","?"], ["Koło", "Kwadrat", "Trójkąt", "Gwiazda"], 0),
        ("W każdym wierszu są kolejno koło, romb i kwadrat. Wybierz brakujący kształt.", ["circle","diamond","square","diamond","square","circle","square","circle","?"], ["Koło", "Romb", "Kwadrat", "Trójkąt"], 1),
        ("Liczba pionowych kresek rośnie w kolejnych wierszach: 1, 2, 3. Ile kresek jest w ostatnim polu?", ["bars","circle","square","bars","triangle","diamond","bars","hollow","?"], ["Jedna", "Dwie", "Trzy", "Cztery"], 3),
        ("Każdy wiersz zaczyna się od koła, potem ma trójkąt, a na końcu kwadrat. Co uzupełnia macierz?", ["circle","triangle","square","triangle","square","circle","square","circle","?"], ["Koło", "Trójkąt", "Kwadrat", "Romb"], 1),
        ("W każdym kolejnym wierszu figura przesuwa się o jedną kolumnę w prawo. Która figura trafia do ostatniego pola?", ["star","circle","square","circle","square","star","square","star","?"], ["Gwiazda", "Koło", "Kwadrat", "Trójkąt"], 1),
        ("W każdym wierszu są kolejno kwadrat, koło i romb. Jaki kształt brakuje?", ["square","circle","diamond","circle","diamond","square","diamond","square","?"], ["Kwadrat", "Koło", "Romb", "Trójkąt"], 2),
        ("W każdym wierszu pojawia się kolejno figura półkolorowa, pełna i pusta. Wybierz ostatni element.", ["half","circle","hollow","square","triangle","hollow","diamond","star","?"], ["Pełna figura", "Pusta figura", "Półkolorowa figura", "Cztery kropki"], 1),
    ]
    for n, (prompt, shapes, options, answer) in enumerate(matrix_bank):
        level = "Łatwe" if n < 6 else "Umiarkowane"
        QUESTIONS.append({"category":"Wzory i uzupełnianie", "level":level, "points":1 if level=="Łatwe" else 2,
                          "prompt":prompt, "options":options, "answer":answer, "image_svg":svg_card(shapes)})


add_matrix_questions()

# Each attempt has 3 easy and 2 moderate questions per category (20 total).
CATEGORIES = list(dict.fromkeys(q["category"] for q in QUESTIONS))
QUESTION_BANK = {
    (category, level): [q for q in QUESTIONS if q["category"] == category and
                        (q["level"] == level if level == "Łatwe" else q["level"] in ("Trudne", "Umiarkowane"))]
    for category in CATEGORIES for level in LEVELS
}
assert all(len(pool) >= 5 for pool in QUESTION_BANK.values())


def draw_questions() -> list[dict]:
    chosen = []
    for category in CATEGORIES:
        chosen.extend(q.copy() for q in random.sample(QUESTION_BANK[(category, "Łatwe")], 3))
        chosen.extend(q.copy() for q in random.sample(QUESTION_BANK[(category, "Umiarkowane")], 2))
    for q in chosen:
        if q["level"] == "Trudne":
            q["level"] = "Umiarkowane"
    random.SystemRandom().shuffle(chosen)
    return chosen

HTML = r'''<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Test rozumowania</title>
<style>
:root{--ink:#162235;--muted:#65748a;--line:#dbe3ee;--blue:#2856d8;--pale:#f3f6fc;--green:#17734c;--red:#ad3b3b}*{box-sizing:border-box}body{margin:0;background:#f6f8fc;color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}header{background:#fff;border-bottom:1px solid var(--line);padding:17px max(20px,calc((100% - 920px)/2));display:flex;justify-content:space-between;gap:16px;align-items:center}header strong{font-size:18px}nav{display:flex;gap:8px}button,.button{font:inherit;border:0;border-radius:10px;padding:11px 17px;cursor:pointer;background:var(--blue);color:white;font-weight:650}button:disabled{opacity:.45;cursor:not-allowed}.secondary{background:#e9eef9;color:#253a62}.link{background:transparent;color:var(--blue);padding:10px}.wrap{max-width:760px;margin:40px auto;padding:0 18px}.card{background:white;border:1px solid var(--line);border-radius:18px;padding:clamp(22px,5vw,40px);box-shadow:0 8px 28px #243b5a0b}.eyebrow{color:var(--blue);font-weight:700;font-size:13px;text-transform:uppercase;letter-spacing:.07em}.muted{color:var(--muted)}h1{font-size:clamp(26px,4vw,36px);line-height:1.18;margin:9px 0 14px}h2{margin:0 0 10px}.row{display:grid;grid-template-columns:1fr 1fr;gap:14px}label{display:block;font-weight:650;margin:17px 0 6px}input,select{font:inherit;width:100%;padding:12px;border:1px solid #cbd5e3;border-radius:9px;background:#fff;color:var(--ink)}.actions{display:flex;justify-content:space-between;gap:12px;margin-top:26px}.progress{height:8px;background:#e8edf6;border-radius:8px;margin:21px 0 26px;overflow:hidden}.progress span{display:block;height:100%;background:var(--blue);transition:width .2s}.question{font-size:23px;font-weight:680;line-height:1.35;margin:22px 0}.option{display:flex;gap:12px;align-items:flex-start;padding:13px 15px;margin:10px 0;border:1px solid var(--line);border-radius:10px;cursor:pointer;font-weight:500}.option:has(input:checked){border-color:var(--blue);background:#f4f7ff}.option input{width:auto;margin-top:5px;accent-color:var(--blue)}.result{text-align:center}.score{font-size:54px;font-weight:800;color:var(--blue);line-height:1.15;margin:20px}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;margin-top:20px;font-size:14px}th,td{padding:11px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}th{color:var(--muted);font-size:12px;text-transform:uppercase}.notice{padding:12px 15px;background:#fff8df;border-radius:9px;color:#695411;margin:18px 0}.hidden{display:none!important}.category{font-size:13px;color:var(--muted)}footer{max-width:760px;margin:0 auto 30px;padding:0 18px;color:var(--muted);font-size:13px}@media(max-width:580px){header{align-items:flex-start;flex-direction:column}.row{grid-template-columns:1fr}.actions button{padding:10px 12px}.question{font-size:20px}}
</style></head><body>
<header><strong>Test rozumowania</strong><nav><button id="homeBtn" class="link">Test</button><button id="resultsBtn" class="link">Wyniki</button></nav></header>
<main class="wrap">
<section id="intro" class="card"><div class="eyebrow">20 pytań · około 10–15 minut</div><h1>Sprawdź swoje rozumowanie</h1><p class="muted">Test obejmuje ciągi i reguły, matematykę, wzory oraz wyobraźnię przestrzenną. Podaj imię lub pseudonim i przedział wiekowy, aby porównać wynik z dotychczasową średnią w tej grupie.</p><div class="notice">To autorski quiz edukacyjny, a nie standaryzowany test psychologiczny ani diagnoza inteligencji.</div><div class="row"><div><label for="name">Imię lub pseudonim</label><input id="name" maxlength="60" autocomplete="name" placeholder="Np. Alex"></div><div><label for="age">Przedział wiekowy</label><select id="age"><option value="">Wybierz przedział</option><option>0-20</option><option>21-40</option><option>41-60</option><option>61-80</option><option>81-100</option></select></div></div><div class="actions"><span></span><button id="start">Rozpocznij test</button></div></section>
<section id="quiz" class="card hidden"><div class="eyebrow" id="level"></div><h1 id="quizTitle">Pytanie</h1><div class="category" id="category"></div><div class="progress"><span id="bar"></span></div><div id="prompt" class="question"></div><div id="questionImage"></div><div id="options"></div><div class="actions"><button id="prev" class="secondary">← Wstecz</button><button id="next">Dalej →</button><button id="submit" class="hidden">Wyślij test</button></div><p id="unanswered" class="muted hidden" style="font-size:13px">Możesz wrócić do pytań przyciskami Wstecz i Dalej.</p></section>
<section id="result" class="card result hidden"></section>
<section id="results" class="card hidden"><div class="eyebrow">Panel wyników</div><h1>Wyniki uczestników</h1><p class="muted">Zestawienie zapisanych podejść. Średnie w porównaniu uczestnika liczone są dla jego grupy wiekowej.</p><div id="adminLogin"><label for="adminPassword">Hasło administratora</label><input type="password" id="adminPassword" autocomplete="current-password"><div class="actions"><span></span><button id="loadResults">Pokaż wyniki</button></div><p id="adminError" class="muted"></p></div><div id="resultsContent"></div><div class="actions"><span></span><button class="secondary" id="backTest">Wróć do testu</button></div></section>
</main><footer>Wyniki są przechowywane lokalnie w bazie SQLite na serwerze tej aplikacji.</footer>
<script>
const $=s=>document.querySelector(s);let questions=[],answers={},index=0,participant={};
function show(which){for(const id of ['intro','quiz','result','results'])$('#'+id).classList.toggle('hidden',id!==which)}
$('#homeBtn').onclick=()=>show('intro');$('#backTest').onclick=()=>show('intro');
$('#start').onclick=async()=>{const name=$('#name').value.trim(),age=$('#age').value;if(!name){$('#name').focus();return}if(!age){$('#age').focus();return}participant={name,age};const res=await fetch('/api/questions');questions=await res.json();answers={};index=0;render();show('quiz')};
function render(){const q=questions[index];$('#level').textContent=`Pytanie ${index+1} z ${questions.length} · ${q.level} · ${q.points} pkt`;$('#quizTitle').textContent=q.category;$('#category').textContent='Wybierz jedną odpowiedź';$('#prompt').textContent=q.prompt;$('#questionImage').innerHTML=q.image_svg||'';$('#bar').style.width=`${(index+1)/questions.length*100}%`;$('#options').replaceChildren(...q.options.map((v,i)=>{const l=document.createElement('label');l.className='option';const r=document.createElement('input');r.type='radio';r.name='answer';r.value=i;r.checked=answers[index]===i;r.onchange=()=>answers[index]=i;l.append(r,document.createTextNode(v));return l}));$('#prev').disabled=index===0;$('#next').classList.toggle('hidden',index===questions.length-1);$('#submit').classList.toggle('hidden',index!==questions.length-1);$('#unanswered').classList.toggle('hidden',Object.keys(answers).length===questions.length)}
$('#prev').onclick=()=>{if(index>0){index--;render()}};$('#next').onclick=()=>{if(index<questions.length-1){index++;render()}};
$('#submit').onclick=async()=>{if(Object.keys(answers).length!==questions.length){$('#unanswered').classList.remove('hidden');return}const res=await fetch('/api/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:participant.name,age_group:participant.age,answers})});const data=await res.json();if(!res.ok){alert(data.error||'Nie udało się zapisać wyniku.');return}$('#result').innerHTML=`<div class="eyebrow">Test zakończony</div><h1>Twój wynik</h1><div class="score">${data.percentage}%</div><p>Zdobyte punkty: <strong>${data.score} / ${data.max_score}</strong></p><p>Średnia w grupie ${escapeHtml(participant.age)}: <strong>${data.group_average === null?'brak wcześniejszych wyników':data.group_average+'%'}</strong></p><p class="muted">${data.group_count?`Średnia na podstawie ${data.group_count} wcześniejszych podejść.`:'Będziesz pierwszą osobą w tej grupie wiekowej.'}</p><div class="notice">Wynik opisuje rezultat tego quizu. Nie jest pomiarem IQ ani oceną kliniczną.</div><button id="again">Wróć na początek</button>`;$('#again').onclick=()=>show('intro');show('result')};
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
$('#resultsBtn').onclick=()=>{show('results');$('#adminPassword').value='';$('#resultsContent').replaceChildren();$('#adminError').textContent=''};
$('#loadResults').onclick=async()=>{const password=$('#adminPassword').value;$('#resultsContent').textContent='Ładowanie…';try{const r=await fetch('/api/results',{headers:{'X-Admin-Password':password}});const d=await r.json();if(!r.ok){$('#resultsContent').replaceChildren();$('#adminError').textContent=d.error||'Brak dostępu';return}$('#adminError').textContent='';if(!d.results.length){$('#resultsContent').textContent='Nie zapisano jeszcze żadnych wyników.';return}const t=document.createElement('table');t.innerHTML='<thead><tr><th>Data</th><th>Uczestnik</th><th>Wiek</th><th>Punkty</th><th>Wynik</th></tr></thead>';const b=document.createElement('tbody');for(const x of d.results){const tr=document.createElement('tr');for(const v of [new Date(x.created_at).toLocaleString('pl-PL'),x.name,x.age_group,`${x.score} / ${x.max_score}`,`${x.percentage}%`]){const td=document.createElement('td');td.textContent=v;tr.append(td)}b.append(tr)}t.append(b);const wrap=document.createElement('div');wrap.className='table-wrap';wrap.append(t);$('#resultsContent').replaceChildren(wrap)}catch(e){$('#resultsContent').textContent='Nie można pobrać wyników.'}};
</script></body></html>'''


def connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Windows/WSL lub równoległy request mogą chwilowo trzymać blokadę zapisu.
    # Poczekaj na zwolnienie bazy zamiast natychmiast kończyć błędem.
    db = sqlite3.connect(DB_PATH, timeout=15)
    db.execute("PRAGMA busy_timeout = 15000")
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age_group TEXT NOT NULL,
        score INTEGER NOT NULL,
        max_score INTEGER NOT NULL,
        percentage REAL NOT NULL,
        answers_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    return db


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data: object, status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            raw = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        elif path == "/api/questions":
            drawn = draw_questions()
            # Sesja jest identyfikowana przez ciasteczko; pytania są wysyłane bez kluczy odpowiedzi.
            token = os.urandom(18).hex()
            self.server.sessions[token] = drawn
            self.send_response(200)
            self.send_header("Set-Cookie", f"quiz_session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=3600")
            raw = json.dumps([{k: q[k] for k in ("category", "level", "points", "prompt", "options", "image_svg")} for q in drawn], ensure_ascii=False).encode()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        elif path == "/api/results":
            if not ADMIN_PASSWORD or self.headers.get("X-Admin-Password", "") != ADMIN_PASSWORD:
                self.send_json({"error": "Hasło administratora jest nieprawidłowe albo nie zostało skonfigurowane."}, 401)
                return
            with connect_db() as db:
                rows = db.execute("SELECT name,age_group,score,max_score,percentage,created_at FROM results ORDER BY id DESC").fetchall()
            self.send_json({"results": [dict(row) for row in rows]})
        else:
            self.send_json({"error": "Nie znaleziono strony."}, 404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/submit":
            self.send_json({"error": "Nie znaleziono endpointu."}, 404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 200_000:
                self.send_json({"error": "Przesłane dane są zbyt duże."}, 413)
                return
            data = json.loads(self.rfile.read(size))
            name = str(data.get("name", "")).strip()[:60]
            age = data.get("age_group")
            answers = data.get("answers")
            if not name or age not in AGES or not isinstance(answers, dict) or len(answers) != 20:
                raise ValueError
            cookie = self.headers.get("Cookie", "")
            token = next((part.split("=", 1)[1] for part in cookie.split(";") if part.strip().startswith("quiz_session=")), None)
            drawn = self.server.sessions.pop(token, None) if token else None
            if not drawn or len(answers) != len(drawn):
                self.send_json({"error": "Test nie jest już aktywny. Rozpocznij go ponownie."}, 400)
                return
            score = 0
            saved_answers = {}
            for i, question in enumerate(drawn):
                choice = answers.get(str(i))
                if not isinstance(choice, int) or not 0 <= choice < len(question["options"]):
                    raise ValueError
                saved_answers[str(i)] = choice
                if choice == question["answer"]:
                    score += question["points"]
            max_score = sum(q["points"] for q in drawn)
            percent = round(score / max_score * 100, 1)
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            with connect_db() as db:
                previous = db.execute("SELECT AVG(percentage),COUNT(*) FROM results WHERE age_group=?", (age,)).fetchone()
                avg = round(previous[0], 1) if previous[1] else None
                db.execute("INSERT INTO results(name,age_group,score,max_score,percentage,answers_json,created_at) VALUES(?,?,?,?,?,?,?)",
                           (name, age, score, max_score, percent, json.dumps(saved_answers), now))
            self.send_json({"score": score, "max_score": max_score, "percentage": percent,
                            "group_average": avg, "group_count": previous[1]})
        except (ValueError, TypeError, json.JSONDecodeError):
            self.send_json({"error": "Dane są nieprawidłowe. Uzupełnij wszystkie 20 odpowiedzi."}, 400)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    with connect_db():
        pass
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.sessions = {}
    print(f"Test rozumowania działa: http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymano serwer.")
    finally:
        server.server_close()
