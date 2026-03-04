#!/usr/bin/env python3
"""
Générateur de vidéos "Course" (Bar Chart Race) pour TikTok / YouTube Shorts / Instagram Reels.

Usage :
    python generate.py configs/crypto_tiktok.yaml
    python generate.py configs/crypto_youtube.yaml
    python generate.py configs/crypto_tiktok.yaml --preview   # fenêtre sans enregistrement

Ajouter une nouvelle course :
    1. Dupliquer un fichier dans configs/
    2. Modifier title, subtitle, source.tickers (ou source.file pour une source manuelle)
    3. Placer les images correspondantes dans assets/{NomParticipant}.png
    4. Lancer python generate.py configs/ma_nouvelle_course.yaml
"""

import argparse
import os
import sys

import yaml

# ─── Formats prédéfinis ──────────────────────────────────────────────────────
# Chaque format définit la résolution, les couleurs et le positionnement du graphique.
# Vous pouvez modifier les valeurs "chart" pour ajuster la taille et la position.
FORMATS: dict = {
    "tiktok": {
        "width": 1080,
        "height": 1920,
        "bg": (20, 20, 20),
        "text_color": (255, 255, 255),
        "subtitle_color": (180, 180, 180),
        "time_color": (150, 150, 150),
        # chart : zone où se dessinent les barres (x_pos, y_pos, width, height)
        "chart": {"width": 900, "height": 1100, "x_pos": 90, "y_pos": 430},
    },
    "youtube": {
        "width": 1920,
        "height": 1080,
        "bg": (255, 255, 255),
        "text_color": (0, 0, 0),
        "subtitle_color": (100, 100, 100),
        "time_color": (100, 100, 100),
        "chart": {"width": 1500, "height": 700, "x_pos": 100, "y_pos": 220},
    },
}


# ─── Chargement de la config ─────────────────────────────────────────────────

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─── Préparation des données ─────────────────────────────────────────────────

def prepare_data(config: dict) -> str:
    """
    Récupère ou valide les données selon le type de source défini dans la config.
    Retourne le chemin vers le fichier Excel prêt à l'emploi.
    """
    source = config["source"]
    source_type = source["type"]
    os.makedirs("data", exist_ok=True)

    if source_type == "crypto":
        from sources.fetchers import fetch_crypto

        data_file = source.get("file", "data/data.xlsx")
        df = fetch_crypto(
            tickers=source["tickers"],
            start=source.get("start", "2018-01-01"),
            end=source.get("end"),
            interval=source.get("interval", "1wk"),
        )
        df.to_excel(data_file)
        print(f"Données sauvegardées → {data_file}")
        return data_file

    elif source_type == "manual":
        from sources.fetchers import load_manual

        data_file = source["file"]
        load_manual(data_file)   # valide que le fichier est lisible
        return data_file

    else:
        sys.exit(
            f"Erreur : type de source inconnu → {source_type!r}\n"
            f"Valeurs acceptées : 'crypto', 'manual'"
        )


# ─── Construction et rendu de la vidéo ──────────────────────────────────────

def build_video(config: dict, data_file: str, preview: bool = False) -> None:
    """
    Assemble le canvas, le graphique et les éléments décoratifs,
    puis enregistre (ou prévisualise) la vidéo.
    """
    # Import ici pour ne pas charger tkinter si on n'en a pas besoin
    from sjvisualizer.Canvas import canvas
    from sjvisualizer.BarRace import bar_race
    from sjvisualizer.DataHandler import DataHandler

    fmt_name = config.get("format", "tiktok")
    if fmt_name not in FORMATS:
        sys.exit(
            f"Erreur : format inconnu → {fmt_name!r}\n"
            f"Valeurs acceptées : {list(FORMATS)}"
        )

    fmt = FORMATS[fmt_name]
    display = config.get("display", {})
    output_cfg = config.get("output", {})

    width = fmt["width"]
    height = fmt["height"]
    fps = output_cfg.get("fps", 30)
    duration = output_cfg.get("duration", 60)       # secondes
    num_frames = int(duration * fps)

    # ── Chargement et interpolation des données ──────────────────────────────
    # DataHandler crée les frames intermédiaires pour une animation fluide.
    print(f"Interpolation des données ({num_frames} frames = {duration}s × {fps} FPS)...")
    dh = DataHandler(excel_file=data_file, number_of_frames=num_frames)
    df = dh.df

    # ── Création du canvas ───────────────────────────────────────────────────
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

    # ── Graphique Bar Race ───────────────────────────────────────────────────
    # Les images de chaque participant sont cherchées dans assets/{nom}.png
    chart_cfg = fmt["chart"]
    chart = bar_race(
        canvas=cv,
        df=df,
        width=chart_cfg["width"],
        height=chart_cfg["height"],
        x_pos=chart_cfg["x_pos"],
        y_pos=chart_cfg["y_pos"],
        number_of_bars=display.get("bars", 10),
        font_color=tuple(fmt["text_color"]),
        font_size=display.get("font_size", 25),
        unit=display.get("unit", ""),
    )
    cv.add_sub_plot(chart)

    # ── Indicateur de date ───────────────────────────────────────────────────
    cv.add_time(
        df,
        time_indicator=display.get("time_format", "month"),
        color=tuple(fmt["time_color"]),
    )

    # ── Rendu ────────────────────────────────────────────────────────────────
    if preview:
        print("Prévisualisation (fenêtre) — Ctrl+C pour quitter.")
        cv.play(fps=fps, record=False)
    else:
        os.makedirs("output", exist_ok=True)
        out_file = output_cfg.get("file", "output/video.mp4")
        print(f"Génération en cours → {out_file}")
        cv.play(fps=fps, record=True, width=width, height=height, file_name=out_file)
        print(f"\nVidéo sauvegardée → {out_file}")


# ─── Point d'entrée ──────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Génère une vidéo Bar Chart Race à partir d'un fichier de config YAML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
exemples :
  python generate.py configs/crypto_tiktok.yaml
  python generate.py configs/crypto_youtube.yaml
  python generate.py configs/crypto_tiktok.yaml --preview
""",
    )
    parser.add_argument("config", help="Chemin vers le fichier de config YAML")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Ouvre une fenêtre de prévisualisation sans enregistrer la vidéo",
    )
    args = parser.parse_args()

    if not os.path.exists(args.config):
        sys.exit(f"Erreur : fichier de config introuvable → {args.config}")

    config = load_config(args.config)
    data_file = prepare_data(config)
    build_video(config, data_file, preview=args.preview)


if __name__ == "__main__":
    main()
