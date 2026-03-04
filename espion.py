from sjvisualizer.Canvas import Canvas
import sjvisualizer.StaticText

print("--- MÉTHODES DISPONIBLES DANS CANVAS ---")
print([m for m in dir(Canvas) if not m.startswith("__")])

print("\n--- NOM DE LA CLASSE TEXTE ---")
# On cherche si ça s'appelle StaticText ou static_text
print([m for m in dir(sjvisualizer.StaticText) if not m.startswith("__")])
print("----------------------------------------")