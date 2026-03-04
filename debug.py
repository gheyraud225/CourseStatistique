import sjvisualizer
import os

print(f"--- DIAGNOSTIC ---")
path = sjvisualizer.__path__[0]
print(f"Dossier installé : {path}")
print(f"Fichiers trouvés à l'intérieur :")
try:
    files = os.listdir(path)
    for f in files:
        if ".py" in f:
            print(f" - {f}")
except Exception as e:
    print(f"Erreur de lecture : {e}")
print("------------------")