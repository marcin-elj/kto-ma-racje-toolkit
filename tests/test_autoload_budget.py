#!/usr/bin/env python
"""Testy hooka `hooks/auto-load-lessons-kmr.py` — BUDZET i JAWNOSC przyciecia.

DLACZEGO ISTNIEJA (2026-08-08 #2). Hook do wersji 0.5.0 skladal
`working_memory.md` + wskazniki `feedback_*` + HOTLIST i konczyl exit 0 —
NIE WIEDZAC, ze wynik nie dociera do modelu. Harness zrzuca additionalContext
powyzej progu do pliku i wpuszcza ~2 KB podgladu, czyli sama liste nazw plikow.
Prog zmierzono obustronnie: **(9 600, 9 999] ZNAKOW** (8 192/8 193/9 600 dociera;
9 999/10 000/20 000/40 000/47 237 zrzucane). Auto-load wazyl wtedy 47 979 znakow
= 5x prog, z czego `working_memory.md` to 86%.

Dwie wlasnosci, ktorych brak kosztowal ~198 sesji cichej awarii:
  1. hook MUSI zmiescic sie w budzecie — inaczej nie dostarcza NICZEGO,
  2. gdy przycina, MUSI to powiedziec W TRESCI additionalContext, bo to jedyny
     kanal do modelu (stderr hooka model widzi tylko jako pole w transkrypcie).

Uruchomienie:  python tests/test_autoload_budget.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HOOK = os.path.join(ROOT, "hooks", "auto-load-lessons-kmr.py")

WEZEL = """---
name: %(nazwa)s
description: '%(desc)s'
kategoria: %(kat)s
krytyczna: %(kry)s
---

%(body)s
"""


def _memory(base, wm_znaki=2000, n_feedback=2, n_krytycznych=2, wm_naglowek=None):
    """Buduje drzewo <base>/kto-ma-racje/memory/ — nazwa katalogu MUSI zawierac
    'kto-ma-racje', bo hook ma CWD guard."""
    proj = os.path.join(base, "kto-ma-racje")
    mdir = os.path.join(proj, "memory")
    os.makedirs(mdir)
    open(os.path.join(mdir, "MEMORY.md"), "w", encoding="utf-8").write("# mapa\n")

    naglowek = wm_naglowek or "> **2026-08-08 (TYTUL BLOKU SESJI):**"
    wm = "# Working memory\n\n%s\nSEKRETNA-TRESC-WORKING-MEMORY\n" % naglowek
    wm += "x" * max(0, wm_znaki - len(wm))
    open(os.path.join(mdir, "working_memory.md"), "w", encoding="utf-8").write(wm)

    for i in range(n_feedback):
        open(os.path.join(mdir, "feedback_%02d.md" % i), "w", encoding="utf-8").write(
            WEZEL % {"nazwa": "regula %d" % i, "desc": "OPIS-REGULY-%d " % i + "slowo " * 60,
                     "kat": "process-discipline", "kry": "false", "body": "tresc"})
    for i in range(n_krytycznych):
        open(os.path.join(mdir, "lesson_k%02d.md" % i), "w", encoding="utf-8").write(
            WEZEL % {"nazwa": "lekcja %d" % i, "desc": "OPIS-LEKCJI-%d " % i + "slowo " * 60,
                     "kat": "db-rls", "kry": "true", "body": "tresc"})
    return proj


def _odpal(cwd):
    """Zwraca (exit_code, additionalContext albo None). Wymusza UTF-8 w dziecku —
    test dostajacy inne srodowisko niz realne wywolanie klamie."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, HOOK], cwd=cwd, env=env,
                       capture_output=True, text=True, encoding="utf-8")
    if not p.stdout.strip():
        return p.returncode, None
    return p.returncode, json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"]


class TestBudzet(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _hook(self, **kw):
        return _odpal(_memory(self.tmp, **kw))

    def test_working_memory_nie_jest_wozony_w_calosci(self):
        """86% budzetu szlo na plik, ktory i tak nie docieral. Auto-load ma byc
        ROUTEREM: wskaznik + jak przeczytac, a nie tresc, ktora rosnie."""
        _kod, ctx = self._hook(wm_znaki=50_000)
        self.assertIsNotNone(ctx)
        self.assertNotIn("SEKRETNA-TRESC-WORKING-MEMORY", ctx,
                         "tresc working_memory nadal jedzie auto-loadem")
        self.assertIn("working_memory.md", ctx,
                      "brak WSKAZNIKA na working_memory — model nie wie, gdzie jest stan")

    def test_miesci_sie_w_budzecie_przy_duzym_korpusie(self):
        """Korpus rosnie (25 krytycznych na 2026-08-08, 210 wezlow lacznie).
        Hook nie moze przekroczyc progu ani przy 60 lekcjach krytycznych."""
        _kod, ctx = self._hook(wm_znaki=50_000, n_feedback=30, n_krytycznych=60)
        self.assertIsNotNone(ctx)
        self.assertLessEqual(len(ctx), 9_600,
                             "auto-load przekroczyl zmierzony prog — harness go zrzuci")

    def test_przyciecie_jest_jawne(self):
        """Cicha degradacja = ta sama awaria co zrzut: model nie wie, ze dostal
        podzbior. Przy przycieciu output MUSI powiedziec ILE i CZYM to nadgonic."""
        _kod, ctx = self._hook(n_feedback=30, n_krytycznych=60)
        self.assertIn("PRZYCIETO", ctx)
        self.assertIn("recall.py", ctx)

    def test_hotlista_ma_priorytet_nad_regulami(self):
        """Hotlista to rzeczy NIEODWRACALNE (RLS/RODO/data-loss). Reguly wyplywaja
        na temat przez hook UserPromptSubmit, wiec przy ciasnym budzecie gina pierwsze."""
        _kod, ctx = self._hook(n_feedback=40, n_krytycznych=40)
        krytyczne = ctx.count("OPIS-LEKCJI-")
        reguly = ctx.count("OPIS-REGULY-")
        self.assertGreater(krytyczne, reguly,
                           "przyciecie zjadlo hotliste przed regulami")

    def test_karta_pokazuje_najswiezszy_blok_sesji(self):
        """Wskaznik „na czym stoimy" nie gnije, bo jest wyciagany z pliku przy
        kazdym uruchomieniu — inaczej niz przepisany recznie tytul."""
        _kod, ctx = self._hook(wm_naglowek="> **2026-08-08 (UNIKALNY-TYTUL-BLOKU):**")
        self.assertIn("UNIKALNY-TYTUL-BLOKU", ctx)

    def test_deklaruje_kontrakt(self):
        """Z zewnatrz (np. krok /session-start) musi byc widac, ktora wersja
        hooka realnie zadzialala — inaczej gate w repo zaklada, a nie sprawdza."""
        _kod, ctx = self._hook()
        self.assertIn("AUTOLOAD-KONTRAKT: karta-v1", ctx)

    def test_cwd_guard_poza_projektem(self):
        obcy = os.path.join(self.tmp, "inny-projekt")
        os.makedirs(os.path.join(obcy, "memory"))
        open(os.path.join(obcy, "memory", "MEMORY.md"), "w").write("x")
        kod, ctx = _odpal(obcy)
        self.assertEqual(0, kod)
        self.assertIsNone(ctx, "hook odpalil sie poza drzewem kto-ma-racje")


if __name__ == "__main__":
    unittest.main()
