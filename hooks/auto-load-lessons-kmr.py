#!/usr/bin/env python
"""SessionStart hook for the "Kto Ma Rację?" project — ROUTER, nie tresc.

KONTRAKT `karta-v1` (2026-08-08 #2). Auto-load wozi WYLACZNIE rzeczy o stalym
rozmiarze: karte-router + wskazniki `feedback_*` + HOTLIST. `working_memory.md`
NIE jest juz wozony w calosci — jest WSKAZYWANY.

DLACZEGO. Harness zrzuca additionalContext powyzej progu do pliku i wpuszcza do
kontekstu ~2 KB podgladu, czyli sama liste nazw plikow. Prog zmierzono obustronnie
2026-08-08 (tymczasowy hook PostToolUse emitujacy zadana liczbe znakow):

    8 192 / 8 193 / 9 600 znakow          -> DOCIERA w calosci
    9 999 / 10 000 / 20 000 / 40 000 / 47 237 -> ZRZUCANE do pliku
    => prog w (9 600, 9 999] ZNAKOW (jednostka: znaki; komunikat harnessu
       „Output too large (39.1KB)" to len(str)/1024)

Do wersji 0.5.0 hook skladal 47 979 znakow (86% = `working_memory.md`) i konczyl
exit 0, nie wiedzac, ze nie dostarczyl NICZEGO — ~198 sesji cichej awarii.
Objaw: model pytal o pozwolenie na czynnosc, na ktora `feedback_*` dawal standing
zgode od miesiaca.

DWIE WLASNOSCI, KTORYCH NIE WOLNO STRACIC (testy: `tests/test_autoload_budget.py`):
  1. output <= BUDZET_ZNAKI — inaczej nie dociera nic,
  2. przyciecie jest JAWNE w tresci additionalContext. To jedyny kanal do modelu;
     stderr hooka model widzi tylko jako pole w transkrypcie, wiec cicha degradacja
     jest tak samo szkodliwa jak zrzut (`lesson_gate_must_fail_loudly`).

Memory location (v0.1.2): repo `<repo>/memory/` (kanon, wersjonowane), fallback
`~/.claude/projects/<slug>/memory/` tylko dla sesji poza drzewem repo.
"""

import glob
import json
import os
import sys

# Zmierzony prog to (9 600, 9 999] znakow. Trzymamy margines na wypadek, gdyby
# harness liczyl tez prefiks „SessionStart hook additional context: ".
BUDZET_ZNAKI = 9_200

# ⚠️ MUSI byc zgodne z `MAX_SUMMARY` w `scripts/check_autoload_budget.py` w repo
# kto-ma-racje. Rozjazd tej pary sprawia, ze gate mierzy inna wielkosc niz ta,
# ktora realnie leci do kontekstu. Zmieniasz jedno — zmien drugie.
MAX_SUMMARY = 120

# Deklarowany w tresci, zeby z ZEWNATRZ (krok 5b `/session-start`, gate w repo)
# dalo sie SPRAWDZIC, ktora wersja hooka realnie zadzialala, a nie zalozyc.
# Podbijasz przy kazdej zmianie SKLADU auto-loadu.
KONTRAKT = "karta-v1"

# Ile znakow rezerwujemy na komunikat o przycieciu (musi sie zmiescic ZAWSZE).
REZERWA_NA_NOTKE = 320


def find_repo_memory(start: str, max_levels: int = 12):
    """Walk up from `start` looking for a `memory/MEMORY.md` file.

    Why MEMORY.md specifically: any project might have a `memory/` folder for
    unrelated reasons; MEMORY.md is a strong signal that this is the kmr memory dir.
    """
    cur = os.path.abspath(start)
    for _ in range(max_levels):
        candidate = os.path.join(cur, "memory")
        if os.path.isdir(candidate) and os.path.isfile(
            os.path.join(candidate, "MEMORY.md")
        ):
            return candidate
        parent = os.path.dirname(cur)
        if parent == cur:  # filesystem root
            return None
        cur = parent
    return None


def _skroc(s: str) -> str:
    """Ucina na granicy slowa — urwane w polowie slowa summary czyta sie jak blad."""
    if len(s) <= MAX_SUMMARY:
        return s
    return s[:MAX_SUMMARY].rsplit(" ", 1)[0] + "…"


def _fm_fields(path: str):
    """Zwraca (krytyczna: bool, kategoria: str, summary: str) z front-mattera.

    Minimalny, self-contained parser (hook nie importuje recall.py z repo).
    summary = description LUB skrot. Brak front-mattera => nie-krytyczna.
    """
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return False, "", ""
    if not text.startswith("---"):
        return False, "", ""
    end = text.find("\n---", 3)
    header = text[3:end] if end != -1 else text[3:]
    kry, kat, desc, skrot = False, "", "", ""
    for line in header.splitlines():
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k == "krytyczna" and v.lower() == "true":
            kry = True
        elif k == "kategoria":
            kat = v
        elif k == "description":
            desc = v
        elif k == "skrot":
            skrot = v
    return kry, kat, (desc or skrot)


def _najswiezszy_blok(wm_path: str) -> str:
    """Pierwsza linia naglowka bloku sesji z working_memory (`> **...`).

    WYCIAGANE z pliku przy kazdym uruchomieniu, nie przepisywane recznie — tytul
    przepisany do konfiguracji gnije (tak zgnil spis routine i licznik lekcji).
    """
    try:
        with open(wm_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("> **"):
                    return line.strip().lstrip("> ").strip("*: ")[:180]
    except OSError:
        pass
    return ""


def _karta(memory_dir: str, source: str) -> str:
    """Karta-router: WSKAZNIKI o stalym rozmiarze, nie fakty.

    Swiadomie NIE ma tu liczb o produkcji (wersje, vc, liczba edge fns) — takie
    fakty gnija miedzy sesjami, a live stan daje krok 5b/5c `/session-start`.
    Karta mowi GDZIE patrzec i CZEGO nie zgadywac.
    """
    wm = os.path.join(memory_dir, "working_memory.md")
    linie = [
        "AUTOLOAD-KONTRAKT: %s (source: %s) — auto-load to ROUTER; "
        "tresc, ktora rosnie, idzie przez recall/Read." % (KONTRAKT, source),
        "",
        "STAN OPERACYJNY: `memory/working_memory.md` — **NIE jest auto-loadowany** "
        "(za duzy: %s znakow wobec progu %d). Read gdy potrzebujesz focusa / "
        "in-flight / decyzji. Edytuj bez pytania o zgode."
        % (_rozmiar(wm), BUDZET_ZNAKI),
    ]
    blok = _najswiezszy_blok(wm)
    if blok:
        linie.append("  najswiezszy blok sesji: %s" % blok)
    linie += [
        "ARCHITEKTURA: `memory/tech_state.md` (stack, schema, edge fns, routes) — on-demand.",
        "RECALL: `python memory/recall.py <rzeczowniki>` — OBOWIAZKOWY dla "
        "security / RLS / RODO / deploy / utraty danych. Hook UserPromptSubmit "
        "podrzuca kandydatow z promptu; dla tematow z ENVIRONMENT sesji odpal recznie.",
        "WEJSCIE W SESJE: `/session-start` — live stan sklepow, GitHub, git, vault, drift.",
        "LIVE WERSJE / PRODUKCJA: **nie zgaduj i nie bierz z pamieci** — krok 5b/5c "
        "`/session-start` (publiczny listing sklepu jest jedynym rozstrzygajacym zrodlem).",
    ]
    return "\n".join(linie)


def _rozmiar(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return "{:,}".format(len(f.read())).replace(",", " ")
    except OSError:
        return "?"


def _sekcja(naglowek: str, pozycje: list) -> str:
    return naglowek + "\n" + "\n".join(pozycje)


def _zloz(karta: str, hotlist: list, reguly: list):
    """Sklada output mieszczacy sie w BUDZET_ZNAKI i zwraca (tekst, pominiete_hot,
    pominiete_reg).

    KOLEJNOSC PRIORYTETU: karta > HOTLIST > reguly. Hotlista to rzeczy
    NIEODWRACALNE (RLS / RODO / data-loss / gate). Reguly procesu wyplywaja NA TEMAT
    przez hook UserPromptSubmit, wiec ich utrata jest odwracalna w trakcie sesji.
    """
    NAG_HOT = ("===== HOTLIST (krytyczna:true — nieodwracalne/kosztowne, ZAWSZE w "
               "glowie; pelna tresc: `python memory/recall.py <slowa>`) =====")
    NAG_REG = ("===== REGULY PROCESU (feedback_*) — WSKAZNIK, nie tresc; pelna regula: "
               "`python memory/recall.py <slowa>` =====")

    staly = len(karta) + REZERWA_NA_NOTKE
    budzet = BUDZET_ZNAKI - staly

    wziete_hot, wziete_reg = [], []
    zuzyte = 0
    if hotlist:
        zuzyte += len(NAG_HOT) + 2
        for p in hotlist:
            if zuzyte + len(p) + 1 > budzet:
                break
            wziete_hot.append(p)
            zuzyte += len(p) + 1
    if reguly:
        koszt_naglowka = len(NAG_REG) + 2
        if zuzyte + koszt_naglowka < budzet:
            zuzyte += koszt_naglowka
            for p in reguly:
                if zuzyte + len(p) + 1 > budzet:
                    break
                wziete_reg.append(p)
                zuzyte += len(p) + 1

    czesci = [karta]
    if wziete_hot:
        czesci.append(_sekcja(NAG_HOT, wziete_hot))
    if wziete_reg:
        czesci.append(_sekcja(NAG_REG, wziete_reg))

    pom_hot = len(hotlist) - len(wziete_hot)
    pom_reg = len(reguly) - len(wziete_reg)
    if pom_hot or pom_reg:
        czesci.append(
            "===== ⚠️ PRZYCIETO POD BUDZET AUTO-LOADU (%d znakow) =====\n"
            "Pominieto %d z %d pozycji HOTLIST i %d z %d regul procesu — NIE dostales "
            "kompletnego zestawu.\nOdzyskaj na temat: `python memory/recall.py "
            "<rzeczowniki zadania>`. Przy security / RLS / RODO / deploy zrob to ZANIM "
            "zadzialasz.\nPrzyczyna to rozmiar korpusu, nie blad — zglos, jesli "
            "przyciecie jest duze (kandydat na skrocenie summary)."
            % (BUDZET_ZNAKI, pom_hot, len(hotlist), pom_reg, len(reguly)))

    return "\n\n".join(czesci), pom_hot, pom_reg


def main() -> None:
    # CWD guard
    cwd = os.getcwd().replace("\\", "/").lower()
    if "kto-ma-racje" not in cwd:
        sys.exit(0)

    memory_dir = find_repo_memory(os.getcwd())
    source = "repo"
    if memory_dir is None:
        memory_dir = os.path.join(
            os.path.expanduser("~"), ".claude", "projects",
            "D--Projects-kto-ma-racje", "memory")
        source = "global-cache"
    if not os.path.isdir(memory_dir):
        sys.exit(0)

    reguly = []
    for path in sorted(glob.glob(os.path.join(memory_dir, "feedback_*.md"))):
        _kry, kat, summ = _fm_fields(path)
        reguly.append("- %s [%s] — %s"
                      % (os.path.basename(path)[:-3], kat or "?", _skroc(summ)))

    # HOTLIST data-driven z front-mattera (jedyne zrodlo prawdy = flaga na wezle).
    # Statyczna lista nazw cicho gnila: referencja do przemianowanego wezla
    # ladowala 3 z 4 (`lesson_plugin_version_drift_two_manifests`).
    hotlist = []
    for pat in ("lesson_*.md", "project_*.md", "reference_*.md", "checklist_*.md"):
        for path in sorted(glob.glob(os.path.join(memory_dir, pat))):
            kry, kat, summ = _fm_fields(path)
            if kry:
                hotlist.append("- %s [%s] — %s"
                               % (os.path.basename(path)[:-3], kat or "?", _skroc(summ)))

    tekst, pom_hot, pom_reg = _zloz(_karta(memory_dir, source), hotlist, reguly)

    # Fail-loud na stderr — nie zastepuje notki w tresci (model stderr nie czyta),
    # ale zostawia slad w transkrypcie dla diagnozy „czemu auto-load byl chudy".
    if pom_hot or pom_reg:
        sys.stderr.write(
            "auto-load-lessons-kmr: PRZYCIETO pod budzet %d znakow "
            "(hotlist -%d, reguly -%d). Rozwaz skrocenie MAX_SUMMARY.\n"
            % (BUDZET_ZNAKI, pom_hot, pom_reg))

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": tekst,
    }}))


if __name__ == "__main__":
    main()
