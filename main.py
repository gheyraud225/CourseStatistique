from sjvisualizer import Canvas
from sjvisualizer import DataHandler
from sjvisualizer import BarChartRace
import time

def main():
    # 1. Configuration de la vidéo (Toile de fond)
    # width/height : résolution (1920x1080 pour HD)
    canvas = Canvas(width=1920, height=1080, bg_color=(255, 255, 255))

    # 2. Titre de la vidéo (Optionnel mais recommandé)
    canvas.add_title("Course aux Abonnés YouTube", color=(0,0,0))
    canvas.add_sub_title("Historique 2020-2024", color=(100,100,100))

    # 3. Ajout de la course (Bar Chart Race)
    # shift : déplace le graphique sur l'écran (x, y)
    bar_chart = BarChartRace(
        canvas=canvas, 
        data_file="data.xlsx", 
        width=1500,        # Largeur du graphique
        height=800,        # Hauteur du graphique
        shift=(100, 150),  # Position (marge gauche, marge haut)
        number_of_bars=10, # Top 10 seulement
        text_color=(0,0,0) # Couleur du texte
    )
    
    # Ajoute l'élément au canvas
    canvas.add_sub_plot(bar_chart)

    # 4. Ajout de la date (le compteur qui tourne)
    canvas.add_time_indicator(bar_chart, color=(100,100,100))

    # 5. Lancer et Enregistrer
    # record=True va créer un fichier mp4. 
    # Si tu mets False, ça ouvre juste une fenêtre pour prévisualiser.
    canvas.play(record=True, file_name="ma_video_finale.mp4")

if __name__ == "__main__":
    main()