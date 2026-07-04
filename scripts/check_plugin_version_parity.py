#!/usr/bin/env python3
"""Gate: plugin.json version MUST equal marketplace.json plugins[name].version.

Zamyka klasę `lesson_plugin_version_drift_two_manifests`: `claude plugin update`
czyta wersję z marketplace.json, więc zbumpowanie tylko plugin.json = cichy no-op
(update widzi "already up to date" mimo świeżego kodu w repo). Ten check FAIL-uje
głośno (exit 1) gdy dwie wersje się rozjadą — bez `|| true`, ścieżka czerwona
przetestowana (lesson_gate_must_fail_loudly).

Zero zależności (tylko stdlib), python3 preinstalowany na ubuntu-latest.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
MARKET = ROOT / ".claude-plugin" / "marketplace.json"


def fail(msg: str) -> "None":
    # ::error:: = adnotacja GitHub Actions; drukujemy też zwykły FAIL do logu.
    print(f"::error::{msg}")
    print(f"FAIL: {msg}")
    sys.exit(1)


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"manifest nie znaleziony: {path}")
    except json.JSONDecodeError as e:
        fail(f"nieparsowalny JSON w {path.name}: {e}")


def main() -> "None":
    plugin = load(PLUGIN)
    market = load(MARKET)

    name = plugin.get("name")
    pv = plugin.get("version")
    if not name:
        fail("plugin.json: brak pola 'name'")
    if not pv:
        fail("plugin.json: brak pola 'version'")

    entries = market.get("plugins", [])
    match = [p for p in entries if p.get("name") == name]
    if not match:
        fail(f"marketplace.json: brak wpisu plugins[] o name={name!r}")
    mv = match[0].get("version")
    if mv != pv:
        fail(
            f"version drift: plugin.json={pv!r} != marketplace.json "
            f"plugins[{name!r}]={mv!r} - zbumpuj OBA pliki "
            f"(lesson_plugin_version_drift_two_manifests)"
        )

    print(f"OK: {name} version parity = {pv} (plugin.json == marketplace.json)")


if __name__ == "__main__":
    main()
