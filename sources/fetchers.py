"""
Modules de récupération de données pour les différentes sources supportées.

Sources disponibles :
  - crypto  : Prix de fermeture via Yahoo Finance (yfinance)
  - manual  : Données depuis un fichier Excel fourni par l'utilisateur
"""
from __future__ import annotations

import pandas as pd


def fetch_crypto(
    tickers: dict,
    start: str,
    end: str | None = None,
    interval: str = "1wk",
) -> pd.DataFrame:
    """
    Télécharge les prix de clôture des cryptomonnaies depuis Yahoo Finance.

    :param tickers: dict {code_yahoo: nom_affichage}, ex. {"BTC-USD": "Bitcoin"}
    :param start:   date de début "YYYY-MM-DD"
    :param end:     date de fin "YYYY-MM-DD" (None = aujourd'hui)
    :param interval: intervalle : "1d", "1wk" ou "1mo"
    :return: DataFrame avec DatetimeIndex et noms d'affichage en colonnes
    """
    import yfinance as yf

    symbols = list(tickers.keys())
    names = tickers

    print(f"Téléchargement de {len(symbols)} actif(s) depuis Yahoo Finance...")
    raw = yf.download(
        symbols,
        start=start,
        end=end,
        interval=interval,
        progress=False,
    )

    # Extraction de la colonne "Close" — gère les cas mono et multi-ticker
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw.xs("Close", axis=1, level=0).copy()
    else:
        # Ticker unique téléchargé sans liste
        close = raw[["Close"]].copy()
        close.columns = [symbols[0]]

    close = close.rename(columns=names)

    # Valeur 0 pour les actifs qui n'existaient pas encore à la date de départ
    close = close.fillna(0)

    close.index = pd.to_datetime(close.index)
    close.index.name = "Date"

    print(f"{len(close)} points de données récupérés.")
    return close


def load_manual(file_path: str) -> None:
    """
    Valide qu'un fichier Excel fourni manuellement existe et est lisible.

    Le fichier doit avoir :
      - La première colonne = dates (index)
      - Les colonnes suivantes = participants (ex. "Bitcoin", "Ethereum")

    :param file_path: chemin vers le fichier Excel
    :raises FileNotFoundError: si le fichier n'existe pas
    :raises ValueError: si le fichier n'est pas lisible
    """
    import os

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    try:
        df = pd.read_excel(file_path, index_col=0, nrows=3)
        if df.empty:
            raise ValueError("Le fichier Excel est vide ou mal formaté.")
    except Exception as exc:
        raise ValueError(f"Impossible de lire {file_path} : {exc}") from exc
