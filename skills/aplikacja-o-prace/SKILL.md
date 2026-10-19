---
name: aplikacja-o-prace
description: Use when sending a job application through a web form in the browser on someone's behalf (pracuj.pl, justjoin.it, Traffit, Recruitify, eRecruiter, Lever, Ashby, Greenhouse, Workday, LinkedIn Easy Apply, PeopleForce), or when asked to "aplikuj", "wyślij CV", "złóż aplikację", "wypełnij formularz rekrutacyjny", write a cover letter or message for a specific offer, or when the user hands back after uploading a CV ("wgrane", "wgrałem").
---

# Aplikacja o pracę przez formularz ATS

## Zasada

Formularz aplikacyjny **kłamie o swoim stanie**: podstawia odpowiedzi z poprzednich aplikacji, parser CV
nadpisuje pola, limit znaków nie ma `maxlength`, listing na boardzie żyje, a ATS jest martwy, a człowiek po
uploadzie sam klika „Aplikuj”. Prawdą jest tylko to, co odczytasz z DOM i z URL-a **w chwili decyzji**.

**Naruszenie litery tych kroków jest naruszeniem ich sensu.** „Marcin się spieszy” i „ufam ci” nie skracają żadnego kroku.

## Karta aplikacji (WYMAGANA przed napisaniem jakiegokolwiek tekstu)

Pokaż ją Marcinowi w pierwszej wiadomości o ofercie (w tej samej wiadomości może być tekst pisany pod nią).

```text
Oferta:         <firma, stanowisko, link do listingu>
Kanał:          <URL formularza u pracodawcy / w ATS>  źródło: <applyUrl | regex HTML | już ATS | przycisk>
Żyje:           <tak: formularz się renderuje | nie: komunikat>
Pola:           <nazwa, typ, required> | „za pierwszym klikiem” (pracuj „Aplikuj szybko”: kwestionariusz po nim)
Wiadomość:      <brak | pole X, limit N (maxlength albo licznik „0 / N” z tekstu strony)>
Stawka/widełki: <brak | pole, typ (liczba? select? opcje)>
Plik(i):        <inputy file, jakie CV/list>
Odpowiedzi:     <pole = wartość zatwierdzona | pole = „?” + Twoja propozycja i skąd (prefill z formularza to nie źródło)>
Klik rejestrujący: <pierwszy klik, po którym aplikacja istnieje>
```

Pusta linijka bez wyjaśnienia = nie przechodzisz dalej. Wymagane zgody (RODO, przetwarzanie) też idą do
„Odpowiedzi”: zaznaczasz je w imieniu Marcina, więc on je widzi. Tekst (list, wiadomość, odpowiedzi) piszesz pod realne
pole i realny limit (policz `len`). Fakty o Marcinie bierzesz z CV i z `D:/SecondBrain/praca/` (np.
`cv-ai-interview-defense.md`); zdanie bez źródła oznacz `[do potwierdzenia]`. Formularz bez pola na wiadomość,
a Marcin chce list: powiedz to i zaproponuj list jako drugi plik, jeśli jest input na plik.

## Kroki (każdy to bramka)

**1. Kanał u źródła.** Listing to warstwa pośrednia. Przeglądarka w aplikacji blokuje nowe karty, więc URL
formularza wyciągasz kodem, potem `navigate`:

```js
// justjoin (z karty justjoin.it); slug = końcówka /job-offer/<slug>
(await (await fetch('https://justjoin.it/api/candidate-api/offers/<slug>')).json()).applyUrl
// pracuj; <id> = liczba po "oferta," w URL-u oferty
(await (await fetch(location.origin+'/aplikowanie/formularz-pracodawcy/<id>')).text())
  .match(/https?:\/\/[^"'\s<>]+/g).filter(u=>!/pracuj\.pl|gpcdn|google|facebook/.test(u))
```

Pusta lista na pracuj = formularz pracuj (kwestionariusz po „Aplikuj szybko”). Pracuj z formularzem
pracodawcy: URL z HTML służy do sondy pól PRZED zgodą; po zgodzie klikasz „Aplikuj” na pracuj (rejestruje
aplikację na pracuj, „Dziękujemy”, widać ją w „Moich aplikacjach”), a ATS, który chce się otworzyć w nowej
karcie, otwierasz przez `navigate`. Klik rejestrujący = ten na pracuj (sukces: URL `dziekujemy.pracuj.pl`
albo „Zaaplikowano” przy ofercie); dane do pracodawcy wysyła dopiero „Wyślij” w ATS, na które bierzesz zgodę nr 2. Nazwa formularza bywa inna niż tytuł
ogłoszenia (CLOUDFIDE „Mid Fullstack”): to nie dowód złego linku, ale napisz o tym w karcie. „Oferta nie
została odnaleziona”, „formularz nieaktywny”, 404 = kanał martwy: mówisz Marcinowi, nie piszesz tekstów.

**2. Sonda pól** (wypełnia kartę). Bez filtra widoczności, bo zgody i kolejne kroki bywają zwinięte:

```js
[...document.querySelectorAll('input,textarea,select')].map(e=>({n:e.name||e.id,l:e.labels?.[0]?.innerText,
 t:e.type,vis:!!e.offsetParent,max:e.maxLength,len:e.value?.length,req:e.required,
 o:e.tagName==='SELECT'?[...e.options].map(x=>x.text):undefined}))
```

Do tego `get_page_text`: licznik „0 / 1000” w tekście to limit egzekwowany dopiero przy wysyłce, po cichu.

**3. Zgoda nr 1, przed klikiem rejestrującym** („Aplikuj szybko”, „Kontynuuj aplikowanie”, „Easy Apply”):
na kartę i tekst, które Marcin widział. Na pracuj.pl „Aplikuj szybko” **od razu wysyła** CV z konta.
Gdy jedynym klikiem rejestrującym jest finalne „Wyślij” w ATS, ten krok przesuwa się za krok 5.

**4. Hand-off uploadu.** Przeglądarka w aplikacji nie wgrywa plików. **Upload PRZED wypełnieniem pól**: parser
i tak je nadpisze, a puste pola wymagane zatrzymają walidacją odruchowe „Aplikuj”. Prośba zawsze dosłownie:
> Wgraj `<plik>` w pole `<nazwa>` i **NIE klikaj Aplikuj / Wyślij / Submit / Dalej** (przycisk stoi `<gdzie>`). Napisz „wgrane”, sprawdzę.

Po „wgrane” **pierwsze** wywołanie:

```js
({url:location.href, files:[...document.querySelectorAll('input[type=file]')].map(i=>[...i.files].map(f=>f.name+' '+f.size)),
 shown:['<nazwa pliku 1>','<nazwa pliku 2>'].map(n=>[n,document.body.innerText.includes(n)])})
```

| Wynik | Znaczy | Robisz |
|---|---|---|
| URL `/thanks`, `thankyou`, `dziekujemy`, „submitted” | Marcin już wysłał | NIE proś o ponowny upload (druga aplikacja). Tracker: „wysłane bez weryfikacji”. Powiedz wprost. |
| URL formularza, plik w `files` albo `shown` = true | upload OK (AJAX-owe ATS, np. Traffit, zerują input i pokazują nazwę obok) | krok 5 |
| URL formularza, brak pliku i w `files`, i w `shown` | upload nie doszedł | ponów prośbę, to samo zdanie |
| URL kolejnego kroku (`/step-2`, „Dalej”) | aplikacja NIE wysłana | wróć do kroku 2 na nowym kroku |

**5. Pełny odczyt przed „Wyślij”**: po uploadzie, po własnych poprawkach i jeszcze raz tuż przed klikiem,
jeśli między odczytem a klikiem czekałeś na Marcina (panel jest wspólny). Do kodu poniżej dołącz `shown`
z kroku 4: przy AJAX-owym uploadzie tylko on pokaże, że plik zniknął.

```js
[...document.querySelectorAll('input,textarea,select')].map(e=>({n:e.name||e.id,l:e.labels?.[0]?.innerText,
 v:e.type==='file'?[...e.files].map(f=>f.name+' '+f.size):e.type==='checkbox'||e.type==='radio'?e.checked
 :e.tagName==='SELECT'?e.options[e.selectedIndex]?.text:e.value}))
```

Porównaj pole po polu z linijką „Odpowiedzi” karty. Wartość od parsera albo prefillu, której Marcin nie
zatwierdził (także imię, mail, telefon), oraz każde mapowanie nie 1:1 („10–13 tys. netto” vs opcja selecta)
to pytanie do niego. Po `form_input` odczytaj ponownie: React (Lever, Ashby) bywa głuchy na wpis programowy,
wtedy wpisz klawiaturą. Checkboxy zgód zaznaczaj kliknięciem (`computer` po `ref`), nie `form_input`. **Zgoda nr 2** = Marcin widzi listę wartości z odczytu i mówi „tak”. Gdy klik
rejestrujący jest zarazem finalnym „Wyślij”, zgoda nr 1 i 2 to jedna zgoda, ale dopiero po tym kroku.

**6. Sukces = nowy URL** strony podziękowania. Przycisk bywa w 2-3 kopiach: klikaj po `ref` z `find`
ten, który leży w tym samym `<form>` co pola (nie w nagłówku, pasku ani modalu z innym krokiem). Potem
`location.href` + `get_page_text` (zapisz tekst potwierdzenia; numer zgłoszenia albo „brak numeru”).
„Clicked on element” to nie sukces. **URL bez zmian:** nie klikaj ponownie (dubel); odczytaj błędy walidacji
i pełny stan pól z `shown`. Odrzucenie czyści pliki: wtedy znowu krok 4 (prośba z „NIE klikaj”, potem
`location.href`) i krok 5 (parser po ponownym uploadzie może nadpisać Twoje poprawki), łącznie z nową zgodą
nr 2 na wartości z nowego odczytu. Brak błędu i brak
przejścia = status „niepotwierdzone”, do sprawdzenia w „Moich aplikacjach” portalu.

**7. Zapis po każdej aplikacji**, także niepotwierdzonej albo wysłanej bez weryfikacji:
- Tracker: plik przeglądu, w którym oferta była na liście (Grep po id oferty albo firmie w `D:/SecondBrain/praca/oferty-przeglad-*.md`);
  jeśli nie było jej w żadnym, `D:/SecondBrain/praca/oferty-przeglad-<dziś>.md`
  (nowy plik: frontmatter `typ/tagi/powstalo/zrodlo` + `Gałąź: [[praca]]`). Sekcja `## ✅ Wysłane` (utwórz, jeśli
  brak). Wpis: data, firma, stanowisko, status (`wysłane` / `wysłane bez weryfikacji` / `niepotwierdzone`),
  kanał, URL sukcesu + tekst potwierdzenia, pliki (nazwa + rozmiar albo „nieznane”), wysłane wartości, czego
  formularz nie miał.
- `D:/SecondBrain/zadania.md`, na końcu listy otwartych zadań:
  `- [ ] Sprawdzić odpowiedź: <firma>, <stanowisko> (wysłane <data>) [obszar:: praca] [waga:: 3] [czeka-na:: zewnetrzni] [termin:: <data+14 dni>] [zrodlo:: [[<nazwa pliku trackera bez .md>]]]`

## Znane pułapki per kanał

| Kanał | Pułapka |
|---|---|
| pracuj.pl | „Aplikuj szybko” wysyła od razu; kwestionariusz prefilluje doświadczenie, widełki, formy rozmowy z poprzednich aplikacji; textarea z szablonem portalu (wpisanie DOPISUJE, limit 500) |
| Traffit | upload AJAX-em (input pusty, nazwa obok); stawka jako text z etykietą „(liczba)”, „150 zł/h” odrzucone; prefill selectów (okres wypowiedzenia); odrzucenie kasuje plik; „Wyślij” tuż pod polem CV |
| justjoin | wiadomość limit 1000 bez `maxlength`; za długa blokuje „Apply” bez komunikatu |
| Lever | parser CV wpisuje starą firmę i lokalizację, resetuje zgodę na przyszłe kontakty |
| Ashby | „Missing entry” mimo wartości w DOM: wgraj plik ponownie, wpisz tekst klawiaturą |
| LinkedIn Easy Apply | zaznaczone ostatnie CV (nie to); „Obserwuj firmę” zaznaczone na podglądzie |
| PeopleForce | pole liczbowe bez `type=number`; odrzucenie czyści input z CV |
| Workday | wymaga konta z hasłem: hand-off, nie zakładaj kont |

## Racjonalizacje

| Myśl | Rzeczywistość |
|---|---|
| „Napiszę list od razu, potem wkleję” | Formularz może nie mieć pola, mieć limit 500 albo nie żyć. Karta najpierw. |
| „Marcin napisał »ufam ci« / »dawaj szybko«” | To nie zgoda na klik, który wysyła CV, ani na wartości, których nie widział. |
| „Wypełnię pola, potem poproszę o CV” | Parser nadpisze, a gotowy formularz Marcin wyśle odruchowo. Upload najpierw. |
| „Napisał »wgrane«, sprawdzę plik” | Najpierw `location.href`. Mógł już wysłać. |
| „Brak pliku w inpucie, niech wgra ponownie” | Sprawdź URL i nazwę pliku obok inputu. Na `/thanks` to byłaby druga aplikacja. |
| „Screenshot wygląda na wypełniony” | Prefill i parser wyglądają identycznie jak dobre dane. JS odczyt. |
| „Kliknąłem, nic się nie stało, kliknę jeszcze raz” | Dubel albo druga aplikacja. Odczyt błędów i stanu, potem Marcin. |
| „Wpis do trackera zrobię na koniec sesji” | Po trzech aplikacjach nie pamiętasz, co poszło w której. Zapis po każdej. |

## Czerwone flagi: STOP

Piszesz tekst bez karty · klikasz cokolwiek z „Aplikuj” bez zgody na tę ofertę · prośba o upload bez „NIE
klikaj” · wypełniasz pola przed uploadem · po „wgrane” pierwsze wywołanie to nie `location.href` · „Wyślij”
bez odczytu wszystkich pól tuż przed klikiem · drugi klik po braku przejścia · sukces bez nowego URL-a ·
koniec aplikacji bez wpisu w trackerze i w `zadania.md`.
