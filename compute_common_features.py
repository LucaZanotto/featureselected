#!/usr/bin/env python3
"""
Calcola le feature comuni a TUTTI i modelli nei 3 scenari, per ciascun Group.

Struttura attesa (default: "Selected features"):
Selected features/
  All groups/
    Normal only/
      Logistic Regression/selected_features.txt
      MLP/selected_features.txt
      Support Vector Machine/selected_features.txt
      Random Forest/selected_features.txt
      XGBoost/selected_features.txt
    Normal New only/ (stessa struttura)
    Merged Normal/ (stessa struttura)
  Pathologic And Control/
    (stessa struttura)

Output:
common_features/
  All groups/
    common_Normal only.txt
    common_Normal New only.txt
    common_Merged Normal.txt
    common_across_all_scenarios.txt
  Pathologic And Control/
    (stessi file)

Uso:
    python compute_common_features.py --base-dir "Selected features" --out-dir "common_features"

Opzioni:
    --normalize-case    Normalizza le feature in lower-case per l'intersezione
    --strip-punct       Rimuove punteggiatura semplice (.,;:!-?) dai nomi feature prima dell'intersezione
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import Iterable, Set, Dict, List
import string

# Config nominativi (sinistra: nome cartella, destra: etichetta visuale)
GROUPS = [
    ("All Groups", "All Groups"),
    ("Pathologic And Control", "Pathologic And Control"),
]

SCENARIOS = [
    ("Normal only", "Normal only"),
    ("Normal New only", "Normal New only"),
    ("Merged Normal", "Merged Normal"),
]

MODELS = [
    "Logistic Regression",
    "MLP",
    "Support Vector Machine",
    "Random Forest",
    "XGBoost",
]


def load_features(txt: Path) -> List[str]:
    if not txt.exists():
        return []
    out = []
    with txt.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if s:
                out.append(s)
    return out


def normalize_items(items: Iterable[str], lower: bool, strip_punct: bool) -> List[str]:
    if not lower and not strip_punct:
        return list(items)
    table = str.maketrans("", "", ".,;:!?-") if strip_punct else None
    normed = []
    for x in items:
        y = x
        if strip_punct:
            y = y.translate(table)
        if lower:
            y = y.lower()
        y = y.strip()
        if y:
            normed.append(y)
    return normed


def intersect_many(sets: Iterable[Set[str]]) -> Set[str]:
    it = iter(sets)
    try:
        acc = set(next(it))
    except StopIteration:
        return set()
    for s in it:
        acc &= s
        if not acc:
            break
    return acc


def write_list(path: Path, items: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for x in sorted(items):
            f.write(f"{x}\n")


def main():
    ap = argparse.ArgumentParser(description="Calcola feature comuni ai modelli nei 3 scenari, per group.")
    ap.add_argument("--base-dir", type=Path, default=Path("Selected features"), help="Cartella radice con i group/scenario/modello")
    ap.add_argument("--out-dir", type=Path, default=Path("common_features"), help="Cartella di output per i file risultanti")
    ap.add_argument("--normalize-case", action="store_true", help="Converte le feature in minuscolo per il calcolo dell'intersezione")
    ap.add_argument("--strip-punct", action="store_true", help="Rimuove punteggiatura semplice (.,;:!?-) prima dell'intersezione")
    args = ap.parse_args()

    base = args.base_dir
    if not base.exists():
        raise SystemExit(f"Cartella non trovata: {base}")

    # Report console
    print(f"Base dir: {base.resolve()}")
    print(f"Output dir: {args.out_dir.resolve()}")
    print(f"Normalizzazione: lower={args.normalize_case}, strip_punct={args.strip_punct}")
    print()

    for g_folder, g_label in GROUPS:
        print(f"=== GROUP: {g_label} ===")
        per_scenario_common: Dict[str, Set[str]] = {}

        for s_folder, s_label in SCENARIOS:
            # Colleziona i set per i 5 modelli dentro lo scenario
            model_sets: List[Set[str]] = []
            missing_models = []
            for model in MODELS:
                txt = base / g_folder / s_folder / model / "selected_features.txt"
                feats = load_features(txt)
                feats_norm = normalize_items(feats, args.normalize_case, args.strip_punct)
                model_sets.append(set(feats_norm))
                if not txt.exists():
                    missing_models.append(model)

            common_in_scenario = intersect_many(model_sets)
            per_scenario_common[s_folder] = common_in_scenario

            # Scrivi file scenario
            out_file = args.out_dir / g_folder / f"common_{s_folder}.txt"
            write_list(out_file, common_in_scenario)

            print(f"- Scenario: {s_label}")
            print(f"  Modelli: {', '.join(MODELS)}")
            if missing_models:
                print(f"  ATTENZIONE: file mancanti per: {', '.join(missing_models)}")
            sizes = [len(ms) for ms in model_sets]
            print(f"  Sizes per modello: {sizes}  → Common: {len(common_in_scenario)}")
            if common_in_scenario:
                preview = ", ".join(sorted(list(common_in_scenario))[:10])
                print(f"  Esempi: {preview}")
            print()

        # Intersezione tra i 3 scenari (feature comuni a TUTTI i modelli in ognuno dei 3 scenari)
        across = intersect_many(per_scenario_common.values())
        out_across = args.out_dir / g_folder / "common_across_all_scenarios.txt"
        write_list(out_across, across)

        print(f"→ Common ACROSS ALL 3 SCENARIOS in '{g_label}': {len(across)}")
        if across:
            preview = ", ".join(sorted(list(across))[:20])
            print(f"  Esempi: {preview}")
        print()

    print("✅ Fatto.")


if __name__ == "__main__":
    main()
