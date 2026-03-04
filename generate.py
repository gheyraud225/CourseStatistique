#!/usr/bin/env python3
"""
Générateur de vidéos "Course" (Bar Chart Race) pour TikTok / YouTube Shorts / Instagram Reels.

Usage :
    python generate.py configs/crypto_tiktok.yaml
    python generate.py configs/crypto_tiktok.yaml --headless   # enregistre sans fenêtre visible
    python generate.py configs/crypto_tiktok.yaml --preview     # fenêtre, pas d'enregistrement

Créer une nouvelle course :
    1. Dupliquer configs/crypto_tiktok.yaml → configs/ma_course.yaml
    2. Modifier title, subtitle, source.*, colors
    3. Lancer : python generate.py configs/ma_course.yaml --headless
"""

# ── Mode headless : relance le script via xvfb-run AVANT tout import graphique ──
# Doit être en tout premier dans le fichier.
import os
import shutil
import sys

if "--headless" in sys.argv and "XVFB_ACTIVE" not in os.environ:
    if shutil.which("xvfb-run"):
        import subprocess
        env = {**os.environ, "XVFB_ACTIVE": "1"}
        # Retire --headless des args pour éviter la boucle infinie
        args = [a for a in sys.argv[1:] if a != "--headless"]
        result = subprocess.run(
            ["xvfb-run", "--auto-servernum",
             "--server-args=-screen 0 1920x1920x24",
             sys.executable, __file__] + args,
            env=env,
        )
        sys.exit(result.returncode)
    else:
        print(
            "Avertissement : xvfb-run introuvable — la fenêtre sera visible.\n"
            "Pour l'installer : sudo apt install xvfb"
        )
# ─────────────────────────────────────────────────────────────────────────────

import argparse

import yaml

# ── Formats prédéfinis ────────────────────────────────────────────────────────
# Thème sombre pour les deux formats (meilleur rendu TikTok/YouTube).
# Modifiez "chart" pour ajuster la zone du graphique (x_pos, y_pos, width, height).
FORMATS: dict = {
    "tiktok": {
        "width": 1080,
        "height": 1920,
        "bg": (10, 10, 15),               # Noir quasi-pur
        "text_color": (255, 255, 255),
        "subtitle_color": (160, 160, 175),
        "time_color": (255, 200, 50),      # Jaune vif pour le temps
        "chart": {"width": 960, "height": 1200, "x_pos": 60, "y_pos": 380},
    },
    "youtube": {
        "width": 1920,
        "height": 1080,
        "bg": (10, 10, 15),
        "text_color": (255, 255, 255),
        "subtitle_color": (160, 160, 175),
        "time_color": (255, 200, 50),
        "chart": {"width": 1600, "height": 750, "x_pos": 80, "y_pos": 200},
    },
}


# ── Chargement de la config ───────────────────────────────────────────────────

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Préparation des données ───────────────────────────────────────────────────

def prepare_data(config: dict) -> str:
    """
    Télécharge logos + données selon la source configurée.
    Retourne le chemin vers le fichier Excel prêt à l'emploi.
    """
    source = config["source"]
    source_type = source["type"]
    os.makedirs("data", exist_ok=True)

    if source_type == "crypto":
        from sources.fetchers import fetch_crypto
        from sources.logos import download_crypto_logos

        tickers = source["tickers"]
        download_crypto_logos(tickers)          # Auto-télécharge les logos

        data_file = source.get("file", "data/data.xlsx")
        df = fetch_crypto(
            tickers=tickers,
            start=source.get("start", "2018-01-01"),
            end=source.get("end"),
            interval=source.get("interval", "1wk"),
        )
        df.to_excel(data_file)
        print(f"Données → {data_file}")
        return data_file

    elif source_type == "world_bank":
        from sources.fetchers import fetch_world_bank
        from sources.logos import download_country_flags

        countries = source["countries"]
        download_country_flags(countries)       # Auto-télécharge les drapeaux

        data_file = source.get("file", "data/data.xlsx")
        df = fetch_world_bank(
            indicator=source["indicator"],
            countries=countries,
            start_year=source.get("start_year", 2000),
            end_year=source.get("end_year"),
            scale=float(source.get("scale", 1.0)),
        )
        df.to_excel(data_file)
        print(f"Données → {data_file}")
        return data_file

    elif source_type == "manual":
        from sources.fetchers import load_manual

        data_file = source["file"]
        load_manual(data_file)
        return data_file

    else:
        sys.exit(
            f"Type de source inconnu : {source_type!r}\n"
            "Valeurs acceptées : crypto, world_bank, manual"
        )


# ── Construction et rendu de la vidéo ────────────────────────────────────────

def build_video(config: dict, data_file: str, preview: bool = False) -> None:
    """Assemble le canvas et rend la vidéo."""
    # Imports ici : tkinter est chargé à ce moment (après Xvfb si --headless)
    from sjvisualizer.BarRace import bar_race
    from sjvisualizer.Canvas import canvas
    from sjvisualizer.DataHandler import DataHandler

    fmt_name = config.get("format", "tiktok")
    if fmt_name not in FORMATS:
        sys.exit(f"Format inconnu : {fmt_name!r}\nValeurs acceptées : {list(FORMATS)}")

    fmt = FORMATS[fmt_name]
    display_cfg = config.get("display", {})
    output_cfg = config.get("output", {})

    width, height = fmt["width"], fmt["height"]
    fps = output_cfg.get("fps", 30)
    duration = output_cfg.get("duration", 60)       # 60 secondes par défaut
    num_frames = int(duration * fps)

    # Couleurs personnalisées par participant (liste RGB dans le YAML → tuple)
    custom_colors: dict = {
        name: tuple(rgb)
        for name, rgb in config.get("colors", {}).items()
    }

    # ── Interpolation des données ─────────────────────────────────────────────
    print(f"Interpolation ({num_frames} frames = {duration}s × {fps} FPS)...")
    dh = DataHandler(excel_file=data_file, number_of_frames=num_frames)
    df = dh.df

    # ── Canvas ───────────────────────────────────────────────────────────────
    cv = canvas(
        width=width,
        height=height,
        bg=tuple(fmt["bg"]),
        include_logo=False,
    )

    # ── Titres ───────────────────────────────────────────────────────────────
    if config.get("title"):
        cv.add_title(config["title"], color=tuple(fmt["text_color"]))
    if config.get("subtitle"):
        cv.add_sub_title(config["subtitle"], color=tuple(fmt["subtitle_color"]))

    # ── Graphique Bar Race ────────────────────────────────────────────────────
    # Les logos sont cherchés automatiquement dans assets/{nom}.png
    chart_cfg = fmt["chart"]
    chart = bar_race(
        canvas=cv,
        df=df,
        width=chart_cfg["width"],
        height=chart_cfg["height"],
        x_pos=chart_cfg["x_pos"],
        y_pos=chart_cfg["y_pos"],
        number_of_bars=display_cfg.get("bars", 10),
        font_color=tuple(fmt["text_color"]),
        font_size=display_cfg.get("font_size", 26),
        unit=display_cfg.get("unit", ""),
        colors=custom_colors,                       # Couleurs de marque
        back_ground_color=tuple(fmt["bg"]),         # Fond identique au canvas
    )
    cv.add_sub_plot(chart)

    # ── Indicateur de date ────────────────────────────────────────────────────
    cv.add_time(
        df,
        time_indicator=display_cfg.get("time_format", "month"),
        color=tuple(fmt["time_color"]),
    )

    # ── Rendu ─────────────────────────────────────────────────────────────────
    if preview:
        print("Prévisualisation — appuie sur Ctrl+C pour quitter.")
        cv.play(fps=fps, record=False)
    else:
        os.makedirs("output", exist_ok=True)
        out_file = output_cfg.get("file", "output/video.mp4")
        print(f"Génération → {out_file}")
        cv.play(fps=fps, record=True, width=width, height=height, file_name=out_file)
        print(f"\nVidéo sauvegardée → {out_file}")


# ── Point d'entrée ────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Génère une vidéo Bar Chart Race à partir d'un fichier de config YAML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
exemples :
  python generate.py configs/crypto_tiktok.yaml
  python generate.py configs/crypto_tiktok.yaml --headless
  python generate.py configs/pays_armement_tiktok.yaml --headless
  python generate.py configs/crypto_tiktok.yaml --preview
""",
    )
    parser.add_argument("config", help="Fichier de config YAML")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Enregistre sans afficher la fenêtre (requiert xvfb : sudo apt install xvfb)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Ouvre une fenêtre de prévisualisation sans enregistrer",
    )
    args = parser.parse_args()

    if not os.path.exists(args.config):
        sys.exit(f"Config introuvable : {args.config}")

    config = load_config(args.config)
    data_file = prepare_data(config)
    build_video(config, data_file, preview=args.preview)


if __name__ == "__main__":
    main()
