#!/usr/bin/env python3
"""
Genera una pagina "index.html" con doppio livello di tab:
- Tab superiori per Group ("All groups", "Pathologic And Control")
- Tab secondari per Scenario ("Normal only", "Normal New only", "Merged Normal")

Dentro ogni scenario, una tabella a 5 colonne (una per modello) con le feature.

Struttura attesa (di default nella cartella "Selected features"):
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
    Normal only/ (stessa struttura)
    Normal New only/
    Merged Normal/

Uso:
    python generate_site.py \
        --base-dir "Selected features" \
        --out index.html \
        --title "Selected Features Dashboard"

Nessuna dipendenza extra: solo standard library.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime
import html

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

DEFAULT_TITLE = "Selected Features Dashboard"


def read_features(file_path: Path) -> list[str]:
    """Legge un selected_features.txt e restituisce una lista di feature (righe non vuote)."""
    if not file_path.exists():
        return []
    lines: list[str] = []
    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if s:
                lines.append(s)
    return lines


def build_html(title: str, base_dir: Path, data: dict) -> str:
    """Crea l'HTML completo con tab Group (1° livello) e Scenario (2° livello)."""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    def features_cell(features: list[str]) -> str:
        if not features:
            return '<div class="empty">—</div>'
        items = "\n".join(f"<li>{html.escape(feat)}</li>" for feat in features)
        return f"<ul>\n{items}\n</ul>"

    # Nav gruppi (livello 1)
    groups_nav = "\n".join(
        f'<button class="tab-link group-link" data-target="group-{i}">{html.escape(g_display)}</button>'
        for i, (_, g_display) in enumerate(GROUPS)
    )

    # Pannelli gruppo (ognuno con i propri tab scenario del livello 2)
    group_sections = []
    for gi, (g_folder, g_display) in enumerate(GROUPS):

        # Nav scenari (livello 2) dentro il gruppo
        scenarios_nav = "\n".join(
            f'<button class="tab-link scenario-link" data-target="sc-{gi}-{si}">{html.escape(sc_display)}</button>'
            for si, (_, sc_display) in enumerate(SCENARIOS)
        )

        # Sezioni scenario per questo gruppo
        scenario_sections = []
        for si, (sc_folder, sc_display) in enumerate(SCENARIOS):
            # Tabella a 5 colonne (una per modello)
            t_head = "".join(f"<th>{html.escape(m)}</th>" for m in MODELS)
            t_cells = []
            for m in MODELS:
                feats = data.get(g_folder, {}).get(sc_folder, {}).get(m, [])
                t_cells.append(f"<td>{features_cell(feats)}</td>")
            t_row = "<tr>" + "".join(t_cells) + "</tr>"

            # Badge conteggio feature per modello
            counts = [len(data.get(g_folder, {}).get(sc_folder, {}).get(m, [])) for m in MODELS]
            badges = "".join(
                f'<div class="badge"><span class="label">{html.escape(m)}</span><span class="count">{c}</span></div>'
                for m, c in zip(MODELS, counts)
            )

            scenario_sections.append(
                f"""
                <section id="sc-{gi}-{si}" class="tab-panel scenario-panel{' active' if (gi == 0 and si == 0) else ''}">
                    <h3>{html.escape(sc_display)}</h3>
                    <div class="badges">{badges}</div>
                    <table class="features-table">
                        <thead><tr>{t_head}</tr></thead>
                        <tbody>{t_row}</tbody>
                    </table>
                </section>
                """
            )

        group_sections.append(
            f"""
            <section id="group-{gi}" class="tab-panel group-panel{' active' if gi == 0 else ''}">
                <h2>{html.escape(g_display)}</h2>
                <nav class="tabs scenarios">{scenarios_nav}</nav>
                {''.join(scenario_sections)}
            </section>
            """
        )

    sections_html = "\n".join(group_sections)

    # Per evitare conflitti tra { } del CSS/JS e f-string, raddoppiamo le graffe nel CSS.
    # Il JS è inserito come stringa normale all'interno dello script, quindi sicuro.
    JS = r"""
const groupLinks = Array.from(document.querySelectorAll('.group-link'));
const groupPanels = Array.from(document.querySelectorAll('.group-panel'));

function activateGroup(index) {
  groupLinks.forEach((b, i) => b.classList.toggle('active', i === index));
  groupPanels.forEach((p, i) => p.classList.toggle('active', i === index));
  localStorage.setItem('activeGroupIndex', String(index));

  const panel = groupPanels[index];
  const key = `activeScenarioIndex_group_${index}`;
  const saved = parseInt(localStorage.getItem(key) || '0', 10);
  const sPanels = Array.from(panel.querySelectorAll('.scenario-panel'));
  const safe = Number.isFinite(saved) ? Math.max(0, Math.min(saved, sPanels.length - 1)) : 0;
  activateScenarioIn(panel, safe);
}

function activateScenarioIn(groupPanel, index) {
  const sLinks = Array.from(groupPanel.querySelectorAll('.scenario-link'));
  const sPanels = Array.from(groupPanel.querySelectorAll('.scenario-panel'));
  sLinks.forEach((b, i) => b.classList.toggle('active', i === index));
  sPanels.forEach((p, i) => p.classList.toggle('active', i === index));
  const gi = Array.from(document.querySelectorAll('.group-panel')).indexOf(groupPanel);
  localStorage.setItem(`activeScenarioIndex_group_${gi}`, String(index));
}

// Wire up scenario tab clicks
groupPanels.forEach((panel, gi) => {
  const sLinks = Array.from(panel.querySelectorAll('.scenario-link'));
  sLinks.forEach((b, si) => b.addEventListener('click', () => activateScenarioIn(panel, si)));
});

// Wire up group tab clicks
groupLinks.forEach((b, i) => b.addEventListener('click', () => activateGroup(i)));

// initial
const savedGroup = parseInt(localStorage.getItem('activeGroupIndex') || '0', 10);
const gSafe = Number.isFinite(savedGroup) ? Math.max(0, Math.min(savedGroup, groupPanels.length - 1)) : 0;
activateGroup(gSafe);
""".strip()

    return f"""
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #0f172a; /* slate-900 */
      --panel: #111827; /* gray-900 */
      --muted: #94a3b8; /* slate-400 */
      --text: #e5e7eb; /* gray-200 */
      --accent: #38bdf8; /* sky-400 */
      --accent-2: #a78bfa; /* violet-400 */
      --table: #0b1220;
      --border: #1f2937;
    }}
    html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 60px; }}
    header {{ display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom: 20px; }}
    h1 {{ font-size: clamp(22px, 2vw, 28px); margin: 0; letter-spacing: 0.2px; }}
    .meta {{ color: var(--muted); font-size: 12px; }}

    /* Tabs */
    .tabs {{ display:flex; gap:8px; margin: 16px 0 24px; flex-wrap: wrap; }}
    .tab-link {{
      background: linear-gradient(180deg, #1f2937, #0b1220);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 10px 14px;
      border-radius: 12px;
      cursor: pointer;
      font-weight: 600;
    }}
    .tab-link.active {{ outline: 2px solid var(--accent); }}

    /* Panels */
    .tab-panel {{ display:none; background: var(--panel); border:1px solid var(--border); padding: 20px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,.3); }}
    .tab-panel.active {{ display:block; }}
    .group-panel h2 {{ margin-top: 0; margin-bottom: 8px; font-size: 20px; }}
    .scenario-panel h3 {{ margin: 0 0 12px; font-size: 18px; }}

    /* Badges + Table */
    .badges {{ display:flex; gap:10px; flex-wrap: wrap; margin-bottom: 10px; }}
    .badge {{ display:flex; align-items:center; gap:8px; background: #0b1220; border:1px solid var(--border); padding: 6px 10px; border-radius: 999px; }}
    .badge .label {{ color: var(--muted); font-size: 12px; }}
    .badge .count {{ background: linear-gradient(180deg, var(--accent), var(--accent-2)); color: #0b1220; font-weight: 800; padding: 2px 8px; border-radius: 999px; font-size: 12px; }}

    table.features-table {{ width: 100%; border-collapse: collapse; background: var(--table); border-radius: 12px; overflow: hidden; }}
    .features-table thead th {{ text-align: left; padding: 12px; border-bottom: 1px solid var(--border); font-size: 14px; color: var(--muted); }}
    .features-table td {{ vertical-align: top; padding: 14px; border-right: 1px solid var(--border); }}
    .features-table td:last-child {{ border-right: none; }}
    .features-table ul {{ margin: 0; padding-left: 18px; }}
    .features-table li {{ line-height: 1.5; }}
    .empty {{ color: var(--muted); font-style: italic; }}

    footer {{ margin-top: 26px; color: var(--muted); font-size: 12px; text-align: right; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>{html.escape(title)}</h1>
      <div class="meta">Generato il {generated_at} — sorgente: <code>{html.escape(str(base_dir))}</code></div>
    </header>

    <div>
      <div style="font-size:12px;color:var(--muted);margin-bottom:4px;">Groups</div>
      <nav class="tabs groups">{groups_nav}</nav>
    </div>

    {sections_html}

    <footer>
      Static site — export HTML generato da script Python.
    </footer>
  </div>

  <script>
{JS}
  </script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Genera index.html con le feature selezionate")
    parser.add_argument("--base-dir", type=Path, default=Path("Selected features"), help="Cartella radice che contiene gruppi e scenari")
    parser.add_argument("--out", type=Path, default=Path("index.html"), help="Percorso del file HTML di output")
    parser.add_argument("--title", type=str, default=DEFAULT_TITLE, help="Titolo della pagina")
    args = parser.parse_args()

    base_dir: Path = args.base_dir
    if not base_dir.exists():
        raise SystemExit(f"Cartella non trovata: {base_dir}")

    # Carica i dati: dict[group][scenario][modello] -> list[feature]
    data: dict[str, dict[str, dict[str, list[str]]]] = {}
    for g_folder, _ in GROUPS:
        scen_map: dict[str, dict[str, list[str]]] = {}
        for sc_folder, _ in SCENARIOS:
            model_map: dict[str, list[str]] = {}
            for model in MODELS:
                file_path = base_dir / g_folder / sc_folder / model / "selected_features.txt"
                model_map[model] = read_features(file_path)
            scen_map[sc_folder] = model_map
        data[g_folder] = scen_map

    html_str = build_html(args.title, base_dir, data)
    args.out.write_text(html_str, encoding="utf-8")
    print(f"Creato: {args.out.resolve()}")


if __name__ == "__main__":
    main()
