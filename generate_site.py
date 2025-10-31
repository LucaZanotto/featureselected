#!/usr/bin/env python3
"""
Genera una pagina "index.html" con 3 tab (uno per scenario) che mostrano,
per ciascuno scenario, una tabella a 5 colonne (una per modello) con le feature selezionate.

Struttura attesa delle cartelle (di default nella cartella "Selected features"):
Selected features/
    Normal only/
        Logistic Regression/selected_features.txt
        MLP/selected_features.txt
        Support Vector Machine/selected_features.txt
        Random Forest/selected_features.txt
        XGBoost/selected_features.txt
    Normal New only/ (stessa struttura)
    Merged Normal/ (stessa struttura)

Uso:
    python generate_site.py \\
        --base-dir "Selected features" \\
        --out index.html \\
        --title "Selected Features Dashboard"

Nessuna dipendenza extra: usa solo la standard library (Pathlib/Argparse/Datetime).
"""
from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime
import html

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
    """Crea l'HTML completo come stringa."""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    def features_cell(features: list[str]) -> str:
        if not features:
            return '<div class="empty">—</div>'
        items = "\n".join(f"<li>{html.escape(feat)}</li>" for feat in features)
        return f"<ul>\n{items}\n</ul>"

    # Tabs
    tabs_nav = "\n".join(
        f'<button class="tab-link" data-target="tab-{i}">{html.escape(sc_display)}</button>'
        for i, (_, sc_display) in enumerate(SCENARIOS)
    )

    # Sections per scenario
    sections = []
    for i, (sc_folder, sc_display) in enumerate(SCENARIOS):
        section_rows = []
        # Un'unica riga con 5 colonne, ogni colonna contiene l'elenco feature del modello
        t_head = "".join(f"<th>{html.escape(m)}</th>" for m in MODELS)
        t_cells = []
        for m in MODELS:
            feats = data.get(sc_folder, {}).get(m, [])
            t_cells.append(f"<td>{features_cell(feats)}</td>")
        t_row = "<tr>" + "".join(t_cells) + "</tr>"
        section_rows.append(t_row)
        table_html = f"""
        <table class=\"features-table\">
            <thead><tr>{t_head}</tr></thead>
            <tbody>
                {''.join(section_rows)}
            </tbody>
        </table>
        """

        # Badge conteggi
        counts = [len(data.get(sc_folder, {}).get(m, [])) for m in MODELS]
        badges = "".join(
            f'<div class="badge"><span class="label">{html.escape(m)}</span><span class="count">{c}</span></div>'
            for m, c in zip(MODELS, counts)
        )

        sections.append(
            f"""
            <section id=\"tab-{i}\" class=\"tab-panel{' active' if i == 0 else ''}\">
                <h2>{html.escape(sc_display)}</h2>
                <div class=\"badges\">{badges}</div>
                {table_html}
            </section>
            """
        )

    sections_html = "\n".join(sections)

    return f"""
<!DOCTYPE html>
<html lang=\"it\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
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

    .tab-panel {{ display:none; background: var(--panel); border:1px solid var(--border); padding: 20px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,.3); }}
    .tab-panel.active {{ display:block; }}
    .tab-panel h2 {{ margin-top: 0; margin-bottom: 12px; font-size: 20px; }}

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
    a.source {{ color: var(--accent); text-decoration: none; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>{html.escape(title)}</h1>
      <div class="meta">Generato il {generated_at} — sorgente: <code>{html.escape(str(base_dir))}</code></div>
    </header>

    <nav class="tabs">
      {tabs_nav}
    </nav>

    {sections_html}

    <footer>
      Static site — export HTML generato da script Python.
    </footer>
  </div>
  <script>
    const links = Array.from(document.querySelectorAll('.tab-link'));
    const panels = Array.from(document.querySelectorAll('.tab-panel'));
    function activate(i) {{
      links.forEach((b, idx) => b.classList.toggle('active', idx === i));
      panels.forEach((p, idx) => p.classList.toggle('active', idx === i));
      localStorage.setItem('activeTabIndex', String(i));
    }}
    links.forEach((b, i) => b.addEventListener('click', () => activate(i)));
    // Attiva la prima tab o quella salvata
    const saved = parseInt(localStorage.getItem('activeTabIndex') || '0', 10);
    activate(Number.isFinite(saved) ? Math.max(0, Math.min(saved, panels.length - 1)) : 0);
  </script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Genera index.html con le feature selezionate")
    parser.add_argument("--base-dir", type=Path, default=Path("Selected features"), help="Cartella radice che contiene gli scenari")
    parser.add_argument("--out", type=Path, default=Path("index.html"), help="Percorso del file HTML di output")
    parser.add_argument("--title", type=str, default=DEFAULT_TITLE, help="Titolo della pagina")
    args = parser.parse_args()

    base_dir: Path = args.base_dir
    if not base_dir.exists():
        raise SystemExit(f"Cartella non trovata: {base_dir}")

    # Carica i dati: dict[scenario][modello] -> list[feature]
    data: dict[str, dict[str, list[str]]] = {}
    for sc_folder, _sc_display in SCENARIOS:
        sc_path = base_dir / sc_folder
        model_map: dict[str, list[str]] = {}
        for model in MODELS:
            file_path = sc_path / model / "selected_features.txt"
            model_map[model] = read_features(file_path)
        data[sc_folder] = model_map

    html_str = build_html(args.title, base_dir, data)
    args.out.write_text(html_str, encoding="utf-8")
    print(f"Creato: {args.out.resolve()}")


if __name__ == "__main__":
    main()
