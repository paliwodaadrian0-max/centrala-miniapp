CENTRALA — TELEGRAM MINI APP (ciemny grafit + złote dodatki)
===========================================================

WAŻNE
- To jest szablon dla legalnych produktów i usług.
- Nie wpisuj tokenu bota do plików ani publicznego repozytorium.
- Formularz wysyła zgłoszenie do prywatnego czatu administratora.
- Wysłanie formularza nie potwierdza automatycznie zamówienia.
- Przed użyciem produkcyjnym skonfiguruj zasady prywatności, regulamin, dane firmy i zgodność z prawem.
- Darmowe plany hostingu mogą usypiać aplikację; pierwsza wiadomość po wybudzeniu może przyjść z opóźnieniem.

CZĘŚĆ A — utwórz bota na iPhonie
1. Otwórz Telegram i wyszukaj @BotFather (sprawdź, czy to oficjalny BotFather).
2. Otwórz czat i wyślij /newbot.
3. Wpisz nazwę, np. Centrala Łódź.
4. Wpisz unikalną nazwę użytkownika zakończoną na bot, np. CentralaLodzOrdersBot.
5. BotFather pokaże TOKEN. Skopiuj go i zachowaj prywatnie. Nie wysyłaj go nikomu.
6. W Telegramie otwórz @userinfobot i naciśnij Start. Zapisz swój numeryczny User ID — to będzie ADMIN_ID.

CZĘŚĆ B — dodaj bota do grupy
1. Otwórz swoją grupę Telegram.
2. Wejdź w nazwę grupy > Edit (lub Manage Group) > Administrators > Add Admin.
3. Dodaj swojego nowego bota.
4. Nadaj mu uprawnienie wysyłania wiadomości (Post Messages / Send Messages).
5. GROUP_CHAT_ID:
   - Najłatwiej użyj publicznej nazwy grupy @nazwa_grupy, jeśli grupa ma publiczny username.
   - Dla prywatnej grupy: dodaj tymczasowo @RawDataBot, wyślij wiadomość na grupie, odczytaj chat.id zaczynający się zwykle od -100, zapisz numer, a potem usuń RawDataBot. Nie udostępniaj nikomu danych grupy.
   - Jeśli nie chcesz dodawać dodatkowego bota, poproś o pomoc z odczytaniem ID; nie zgaduj numeru.

CZĘŚĆ C — wgraj pliki na GitHub z iPhone'a
1. Otwórz Safari i wejdź na https://github.com.
2. Zaloguj się lub utwórz konto.
3. Naciśnij + > New repository.
4. Nazwa: centrala-miniapp. Ustaw Private (prywatne). Naciśnij Create repository.
5. Otwórz repozytorium > Add file > Upload files.
6. Rozpakuj pobrane ZIP w aplikacji Pliki (Files): stuknij ZIP.
7. W GitHub wybierz pliki z rozpakowanego folderu. Wgraj main.py, requirements.txt, render.yaml, README_PL.txt oraz folder static z trzema plikami.
8. Naciśnij Commit changes. Sprawdź, czy static/index.html, static/style.css i static/app.js są w folderze static, a nie obok main.py.

CZĘŚĆ D — uruchom hosting Render
1. Otwórz https://render.com w Safari i utwórz konto.
2. Połącz konto GitHub.
3. W Render wybierz New > Blueprint (lub New Web Service, jeśli Blueprint nie jest dostępny) i wybierz repozytorium centrala-miniapp.
4. Jeśli używasz Blueprint, Render odczyta render.yaml i poprosi o wartości zmiennych.
5. Ustaw:
   BOT_TOKEN = token otrzymany od BotFather
   ADMIN_ID = Twój numeryczny Telegram User ID
   GROUP_CHAT_ID = @username grupy albo ID w formacie -100...
   APP_URL = adres usługi Render, np. https://centrala-miniapp.onrender.com (wpisz dokładny adres pokazany przez Render)
   WEBHOOK_SECRET = wymyśl długi losowy ciąg liter i cyfr (min. 32 znaki); zapisz go prywatnie
6. Zapisz ustawienia i uruchom Deploy.
7. Poczekaj, aż Render pokaże status Live. Otwórz APP_URL w Safari — powinna pokazać się strona CENTRALA.

CZĘŚĆ E — połącz Mini App z botem przez BotFather
1. W Telegramie otwórz @BotFather.
2. Wyślij /mybots i wybierz swojego bota.
3. Wybierz Bot Settings > Menu Button > Configure menu button (nazwy mogą się nieznacznie różnić).
4. Ustaw tekst przycisku, np. CENTRALA.
5. Wklej dokładny APP_URL z Render.
6. Zapisz. Otwórz czat z własnym botem i naciśnij Start. Powinien pojawić się przycisk Otwórz CENTRALA.

CZĘŚĆ F — uzupełnij katalog i ustaw automatyczne posty
W prywatnym czacie z botem:
- /pomoc — lista komend
- /addproduct Nazwa produktu | 60 — dodaje produkt za 60 zł
- /products — pokazuje produkty i ich ID
- /delproduct 1 — wyłącza produkt o ID 1
- /setmessage Treść wiadomości — ustawia tekst postów
- /setinterval 360 — publikuje co 360 minut (6 godzin); minimum 60 minut
- /publish — publikuje post natychmiast

Przykłady (wpisuj własne legalne pozycje):
/addproduct Produkt A | 60
/addproduct Produkt B | 100
/addproduct Produkt C | 200
/products

TEST
1. Dodaj jeden testowy produkt.
2. Otwórz Mini App z poziomu bota.
3. Wypełnij region, miasto, usługę i kontakt testowy.
4. Wyślij zgłoszenie. Powinno przyjść na prywatny czat administratora.
5. Ustaw testowy post /setmessage Testowa wiadomość CENTRALA.
6. Użyj /publish i sprawdź grupę.

WAŻNE O OGRANICZENIACH
- Nie udostępniaj BOT_TOKEN, WEBHOOK_SECRET ani danych administratora.
- Baza SQLite na dysku tymczasowym darmowego hostingu może zostać utracona przy redeploy/restartach. Do stałego używania dodaj trwały dysk lub bazę PostgreSQL i regularne kopie zapasowe.
- Na darmowym hostingu usługa może zasypiać. Automatyczne publikacje nie są gwarantowane, gdy proces jest uśpiony. Do niezawodnej pracy użyj hostingu bez usypiania i trwałego magazynu danych.
- W tej wersji katalog edytuje się komendami Telegram, a nie panelem graficznym.
- W tej wersji harmonogram liczy odstęp od uruchomienia procesu; po restarcie cykl zaczyna się od nowa.
- Mini App wymaga HTTPS i musi być otwierana z Telegrama, żeby serwer mógł zweryfikować użytkownika.
