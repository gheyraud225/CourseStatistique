# --- IMPORTS ---
from sjvisualizer.Canvas import Canvas
from sjvisualizer.BarRace import bar_race 
import json

def main():
    # 1. CONFIGURATION
    width = 1080
    height = 1920
    canvas = Canvas(width=width, height=height, bg="#141414")

    # 2. TITRES (DÉSACTIVÉS TEMPORAIREMENT)
    # On les remettra quand on aura trouvé la bonne commande
    # canvas.add_title("Crypto Battle", color=(255, 255, 255))
    # canvas.add_sub_title("Évolution des prix (2018-2024)", color=(200, 200, 200))

    # 3. GRAPHIQUE
    chart_width = 900
    chart_height = 1100

    bar_chart = bar_race(
        canvas=canvas,
        data_file="data.xlsx",
        width=chart_width,
        height=chart_height,
        shift=(90, 450), 
        number_of_bars=6,
        text_color=(255, 255, 255),
        font_size=28
    )

    canvas.add_sub_plot(bar_chart)

    # 4. DATE (On tente de l'ajouter, si ça plante, commente la ligne ci-dessous)
    try:
        canvas.add_time_indicator(bar_chart, color=(200, 200, 200))
    except AttributeError:
        print("ATTENTION: Impossible d'ajouter la date pour l'instant.")

    # 5. ENREGISTREMENT
    print("--- DÉBUT DE LA GÉNÉRATION ---")
    canvas.play(record=True, file_name="tiktok_crypto.mp4")

if __name__ == "__main__":
    main()