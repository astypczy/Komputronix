# Komputronix
## Wstęp
Cel projektu

Celem tego projektu było zaprojektowanie i wdrożenie bazy danych dla magazynu części zamiennych. Baza miała wspierać stronę internetową, umożliwiając pełne zarządzanie magazynem i zakupami zarówno dla klientów, jak i administratorów. Strona internetowa jest zaprojektowana w sposób przyjazny dla użytkownika, co pozwala korzystać z niej osobom bez specjalistycznej wiedzy programistycznej.

Projekt obejmował:

    Tworzenie diagramu encji, projektowanie tabel, zależności i funkcjonalności.
    Implementację bazy danych w wybranym środowisku.
    Przygotowanie strony WWW umożliwiającej pełne korzystanie z systemu.

## Analiza wymagań

Strona umożliwia:

    Klientowi: przeglądanie produktów oraz składanie zamówień.
    Administratorowi: zarządzanie zamówieniami, klientami, produktami (CRUD) oraz przeglądanie statystyk sprzedaży.

## Wymagania funkcjonalne

Dla klienta:

    Przeglądanie produktów.
    Składanie zamówienia.

Dla administratora:

    Akceptowanie zamówień.
    Zarządzanie produktami (CRUD).
    Przeglądanie statystyk sprzedaży.

## Wymagania niefunkcjonalne

Technologie użyte w projekcie:

    SQLite: jako system zarządzania bazą danych.
    Python (Flask): do obsługi strony internetowej.
    HTML/CSS: do tworzenia interfejsu użytkownika.

Zabezpieczenia systemu obejmują: brak dostępu do edycji bazy danych przez klientów oraz haszowanie haseł za pomocą bcrypt.
## Projekt systemu
Projekt bazy danych

Model bazy danych opiera się na kluczach głównych i obcych, które definiują relacje między tabelami. Diagram encji oraz relacji został załączony w formie graficznej.
Architektura strony internetowej

Strona opiera się na wzorcu MVC (Model-Widok-Kontroler):

    Modele: struktura danych przechowywana w SQLite.
    Widoki: funkcje obsługujące żądania HTTP i renderujące szablony HTML.
    Kontrolery: logika biznesowa, np. dodawanie produktów do koszyka.

Projekt zabezpieczeń

    Autoryzacja: dostęp do stron administracyjnych jest chroniony logowaniem.
    Haszowanie haseł: za pomocą bcrypt.
    Zabezpieczenia przed atakami SQL Injection: poprzez parametryzowane zapytania.
    Zabezpieczenia CSRF: wykorzystanie tokenów CSRF w formularzach.
    Ograniczenia sesji: dane sesji przechowywane po stronie serwera.

Do uruchomienia projektu wymagane jest zainstalowanie:

    Python (3.10.6),
    Flask,
    Flask-Bcrypt,
    Flask-Login,
    SQLite.

Instrukcja użytkowania

    Otwórz stronę główną.
    Przeglądaj produkty i dodawaj je do koszyka.
    Złóż zamówienie (bez konieczności logowania).
    Administrator może się zalogować (login: admin, hasło: admin), aby zarządzać produktami i zamówieniami.
