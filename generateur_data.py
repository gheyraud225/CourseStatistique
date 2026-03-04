import yfinance as yf
import pandas as pd
import os

def generer_donnees_crypto():
    print("--- Démarrage du téléchargement des données ---")

    # 1. Liste des cryptos à récupérer (Codes Yahoo Finance)
    # BTC=Bitcoin, ETH=Ethereum, DOGE=Dogecoin, BNB=Binance, SOL=Solana, XRP=Ripple
    tickers = ['BTC-USD', 'ETH-USD', 'DOGE-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD']
    
    # Noms simplifiés pour l'affichage (et pour tes noms de fichiers images !)
    noms_propres = {
        'BTC-USD': 'Bitcoin',
        'ETH-USD': 'Ethereum',
        'DOGE-USD': 'Dogecoin',
        'BNB-USD': 'Binance',
        'SOL-USD': 'Solana',
        'XRP-USD': 'Ripple'
    }

    # 2. Téléchargement via Yahoo Finance (depuis 2018)
    data = yf.download(tickers, start="2018-01-01", interval="1wk") # 1wk = 1 donnée par semaine (plus fluide)

    # 3. On garde seulement la colonne 'Close' (Prix à la fermeture)
    df = data['Close']

    # 4. Nettoyage des données
    # Renommer les colonnes avec les noms simples
    df = df.rename(columns=noms_propres)
    
    # Remplir les vides (NaN) par 0 (pour les cryptos qui n'existaient pas encore en 2018)
    df = df.fillna(0)
    
    # Formatage de la date pour sjvisualizer (important !)
    df.index = df.index.strftime('%Y-%m-%d')
    df.index.name = 'Date'

    # 5. Sauvegarde Excel
    fichier_sortie = 'data.xlsx'
    df.to_excel(fichier_sortie)

    print(f"\nsuccès ! Le fichier '{fichier_sortie}' a été créé.")
    print("Aperçu des dernières données :")
    print(df.tail(3))
    print("-" * 30)
    print("IMPORTANT : N'oublie pas de mettre tes images dans le dossier 'assets/'")
    print(f"Tes images doivent s'appeler exactement : {list(noms_propres.values())}")
    print("Exemple : assets/Bitcoin.png, assets/Ethereum.png, etc.")

if __name__ == "__main__":
    generer_donnees_crypto()