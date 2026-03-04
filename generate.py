#!/usr/bin/env python3
"""
Générateur de vidéos "Course" (Bar Chart Race) — 100% headless, aucune fenêtre.

Usage :
    python generate.py configs/crypto_performance_tiktok.yaml
    python generate.py configs/pays_armement_tiktok.yaml
    python generate.py configs/tech_actions_tiktok.yaml
    python generate.py configs/crypto_tiktok.yaml --preview   # aperçu rapide

Créer une nouvelle course :
    1. Dupliquer un fichier configs/*.yaml
    2. Modifier title, subtitle, source, colors
    3. Lancer python generate.py configs/ma_course.yaml
"""

# ── Rendu headless via matplotlib Agg ────────────────────────────────────────
# Ces lignes DOIVENT être en tout premier, avant tout import de matplotlib.pyplot.
import matplotlib
import imageio_ffmpeg
matplotlib.rcParams['animation.ffmpeg_path'] = imageio_ffmpeg.get_ffmpeg_exe()
matplotlib.use('Agg')    # Pas de fenêtre, pas de Xvfb, fonctionne partout
# ─────────────────────────────────────────────────────────────────────────────

import argparse
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
import yaml

# ── Palette par défaut (utilisée si une entité n'a pas de couleur dans le YAML) ──
_DEFAULT_PALETTE = [
    '#e63946', '#457b9d', '#2a9d8f', '#e9c46a', '#f4a261',
    '#9b5de5', '#f15bb5', '#00bbf9', '#00f5d4', '#fb5607',
    '#ff006e', '#8338ec', '#3a86ff', '#06d6a0', '#ffd166',
    '#ef476f', '#118ab2', '#06d6a0', '#ffc8dd', '#cdb4db',
]

# ── Thème sombre global ───────────────────────────────────────────────────────
_DARK_THEME = {
    'figure.facecolor': '#0a0a0f',
    'axes.facecolor':   '#0a0a0f',
    'text.color':       'white',
    'xtick.color':      '#888899',
    'ytick.color':      'white',
    'axes.labelcolor':  'white',
    'grid.color':       '#1e1e2e',
}

# ── Formats de sortie ─────────────────────────────────────────────────────────
FORMATS: dict = {
    "tiktok": {
        "figsize":           (5.625, 10.0),  # 1080×1920 @ 192 dpi
        "dpi":               192,
        "period_label_size": 32,
        "bar_label_size":    11,
        "tick_label_size":   11,
        "title_size":        16,
    },
    "youtube": {
        "figsize":           (16.0, 9.0),    # 1920×1080 @ 120 dpi
        "dpi":               120,
        "period_label_size": 28,
        "bar_label_size":    9,
        "tick_label_size":   9,
        "title_size":        13,
    },
}

# ── Correspondance time_format → strftime ────────────────────────────────────
_TIME_FMT = {"year": "%Y", "month": "%b %Y", "day": "%d %b %Y"}


# ─── Chargement config ────────────────────────────────────────────────────────

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─── Préparation des données ──────────────────────────────────────────────────

def prepare_data(config: dict) -> pd.DataFrame:
    """
    Télécharge logos + données selon la source.
    Retourne un DataFrame prêt pour bar_chart_race :
    index = DatetimeIndex, colonnes = participants.
    """
    source = config["source"]
    source_type = source["type"]
    os.makedirs("data", exist_ok=True)

    if source_type in ("crypto", "stocks"):
        from sources.fetchers import fetch_yfinance
        from sources.logos import download_logos_yfinance

        tickers = source["tickers"]
        download_logos_yfinance(tickers, source_type)
        df = fetch_yfinance(
            tickers=tickers,
            start=source.get("start", "2018-01-01"),
            end=source.get("end"),
            interval=source.get("interval", "1wk"),
        )

    elif source_type == "world_bank":
        from sources.fetchers import fetch_world_bank
        from sources.logos import download_country_flags

        countries = source["countries"]
        download_country_flags(countries)
        df = fetch_world_bank(
            indicator=source["indicator"],
            countries=countries,
            start_year=source.get("start_year", 2000),
            end_year=source.get("end_year"),
            scale=float(source.get("scale", 1.0)),
        )

    elif source_type == "manual":
        from sources.fetchers import load_manual

        load_manual(source["file"])
        df = pd.read_excel(source["file"], index_col=0)
        df.index = pd.to_datetime(df.index)

    else:
        sys.exit(
            f"Type de source inconnu : {source_type!r}\n"
            "Valeurs : crypto, stocks, world_bank, manual"
        )

    # ── Normalisation (performance relative, toutes les séries → base 100) ───
    display_cfg = config.get("display", {})
    if display_cfg.get("normalize"):
        for col in df.columns:
            first = df[col][df[col] > 0]
            if not first.empty:
                df[col] = (df[col] / first.iloc[0]) * 100
        print("Normalisation : toutes les séries démarrent à 100.")

    return df


# ─── Construction de la palette de couleurs ───────────────────────────────────

def _build_cmap(df: pd.DataFrame, config_colors: dict) -> list:
    """Renvoie une liste de couleurs dans l'ordre des colonnes du DataFrame."""
    palette = iter(_DEFAULT_PALETTE)
    result = []
    for col in df.columns:
        if col in config_colors:
            r, g, b = config_colors[col]
            result.append(f'#{int(r):02x}{int(g):02x}{int(b):02x}')
        else:
            result.append(next(palette, '#888888'))
    return result


# ─── Rendu vidéo ──────────────────────────────────────────────────────────────

def build_video(config: dict, df: pd.DataFrame, preview: bool = False) -> None:
    """Génère la vidéo via bar_chart_race (headless, matplotlib Agg)."""
    import bar_chart_race as bcr

    fmt_name = config.get("format", "tiktok")
    if fmt_name not in FORMATS:
        sys.exit(f"Format inconnu : {fmt_name!r}\nValeurs : {list(FORMATS)}")

    fmt = FORMATS[fmt_name]
    display_cfg = config.get("display", {})
    output_cfg = config.get("output", {})

    # ── Durée cible → period_length calculé automatiquement ──────────────────
    duration = output_cfg.get("duration", 60)
    n_periods = len(df)
    period_ms = max(80, int((duration * 1000) / n_periods))
    steps = display_cfg.get("steps_per_period", 15)

    # ── Palette ───────────────────────────────────────────────────────────────
    config_colors = {name: rgb for name, rgb in config.get("colors", {}).items()}
    cmap_list = _build_cmap(df, config_colors)

    # ── Titre (+ sous-titre sur une 2e ligne) ─────────────────────────────────
    title = config.get("title", "")
    subtitle = config.get("subtitle", "")
    full_title = f"{title}\n{subtitle}" if subtitle else title

    # ── Format de date ────────────────────────────────────────────────────────
    period_fmt = _TIME_FMT.get(display_cfg.get("time_format", "month"), "%b %Y")

    # ── Thème sombre ──────────────────────────────────────────────────────────
    plt.rcParams.update(_DARK_THEME)

    # ── Paramètres communs bar_chart_race ─────────────────────────────────────
    bcr_kwargs = dict(
        orientation='h',
        sort='desc',
        n_bars=display_cfg.get("bars", 10),
        cmap=cmap_list,
        title=full_title,
        title_size=fmt["title_size"],
        bar_label_size=fmt["bar_label_size"],
        tick_label_size=fmt["tick_label_size"],
        shared_fontdict={"color": "white", "weight": "bold"},
        period_label={
            "x": 0.97, "y": 0.07,
            "ha": "right", "va": "center",
            "color": "#FFD700", "weight": "bold",
            "size": fmt["period_label_size"],
        },
        period_fmt=period_fmt,
        bar_kwargs={"alpha": 0.88, "edgecolor": "none"},
        steps_per_period=steps,
        filter_column_colors=True,
    )

    if preview:
        # ── Aperçu rapide : premières 15 périodes, basse résolution ──────────
        out_file = "/tmp/preview_race.mp4"
        df_preview = df.iloc[:min(15, len(df))]
        print(f"Aperçu rapide → {out_file}")
        bcr.bar_chart_race(
            df=df_preview,
            filename=out_file,
            figsize=(fmt["figsize"][0] * 0.55, fmt["figsize"][1] * 0.55),
            dpi=72,
            period_length=250,
            steps_per_period=5,
            **{k: v for k, v in bcr_kwargs.items()
               if k not in ('steps_per_period',)},
        )
        print(f"Aperçu sauvegardé → {out_file}")
    else:
        # ── Rendu final ───────────────────────────────────────────────────────
        os.makedirs("output", exist_ok=True)
        out_file = output_cfg.get("file", "output/video.mp4")
        print(
            f"Rendu ({n_periods} périodes × {period_ms}ms = ~{duration}s, "
            f"{steps} frames/période) → {out_file}"
        )
        bcr.bar_chart_race(
            df=df,
            filename=out_file,
            figsize=fmt["figsize"],
            dpi=fmt["dpi"],
            period_length=period_ms,
            **bcr_kwargs,
        )
        print(f"\nVidéo sauvegardée → {out_file}")


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Génère une vidéo Bar Chart Race — 100% headless, sans fenêtre.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
exemples :
  python generate.py configs/crypto_performance_tiktok.yaml
  python generate.py configs/pays_armement_tiktok.yaml
  python generate.py configs/tech_actions_tiktok.yaml
  python generate.py configs/crypto_tiktok.yaml --preview
""",
    )
    parser.add_argument("config", help="Fichier de config YAML")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Génère un aperçu rapide basse qualité (15 premières périodes)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.config):
        sys.exit(f"Config introuvable : {args.config}")

    config = load_config(args.config)
    df = prepare_data(config)
    build_video(config, df, preview=args.preview)


if __name__ == "__main__":
    main()
