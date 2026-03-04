"""
Modules de récupération de données pour les différentes sources supportées.

Sources disponibles :
  - crypto      : Prix de clôture via Yahoo Finance (yfinance)
  - world_bank  : Statistiques mondiales via l'API World Bank (sans clé)
  - manual      : Données depuis un fichier Excel fourni par l'utilisateur

Indicateurs World Bank utiles :
  NY.GDP.MKTP.CD    → PIB (USD courant)
  MS.MIL.XPND.CD    → Dépenses militaires (USD courant)
  SP.POP.TOTL       → Population totale
  NY.GDP.PCAP.CD    → PIB par habitant (USD courant)
  EG.USE.PCAP.KG.OE → Consommation d'énergie par habitant
"""
from __future__ import annotations

import pandas as pd


# ─── Crypto ──────────────────────────────────────────────────────────────────

def fetch_crypto(
    tickers: dict,
    start: str,
    end: str | None = None,
    interval: str = "1wk",
) -> pd.DataFrame:
    """
    Télécharge les prix de clôture des cryptomonnaies depuis Yahoo Finance.

    :param tickers:  dict {code_yahoo: nom_affichage}, ex. {"BTC-USD": "Bitcoin"}
    :param start:    date de début "YYYY-MM-DD"
    :param end:      date de fin "YYYY-MM-DD" (None = aujourd'hui)
    :param interval: intervalle : "1d", "1wk" ou "1mo"
    :return: DataFrame avec DatetimeIndex et noms d'affichage en colonnes
    """
    import yfinance as yf

    symbols = list(tickers.keys())
    print(f"Téléchargement de {len(symbols)} actif(s) depuis Yahoo Finance...")

    raw = yf.download(symbols, start=start, end=end, interval=interval, progress=False)

    # Extraction de la colonne "Close" — gère les cas mono et multi-ticker
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw.xs("Close", axis=1, level=0).copy()
    else:
        close = raw[["Close"]].copy()
        close.columns = [symbols[0]]

    close = close.rename(columns=tickers).fillna(0)
    close.index = pd.to_datetime(close.index)
    close.index.name = "Date"

    print(f"{len(close)} points de données récupérés.")
    return close


# ─── World Bank ───────────────────────────────────────────────────────────────

def fetch_world_bank(
    indicator: str,
    countries: dict,
    start_year: int = 2000,
    end_year: int | None = None,
    scale: float = 1.0,
) -> pd.DataFrame:
    """
    Télécharge une statistique mondiale depuis l'API World Bank (sans clé API).

    :param indicator:  code indicateur WB, ex. "NY.GDP.MKTP.CD"
    :param countries:  dict {code_iso3: nom_affichage}, ex. {"USA": "États-Unis"}
    :param start_year: première année à récupérer
    :param end_year:   dernière année (None = l'an dernier)
    :param scale:      diviseur appliqué aux valeurs (ex. 1e9 pour passer en milliards)
    :return: DataFrame avec DatetimeIndex annuel et pays en colonnes
    """
    import requests
    from datetime import date

    end_year = end_year or (date.today().year - 1)
    country_codes = ";".join(countries.keys())

    print(f"Téléchargement World Bank [{indicator}] pour {len(countries)} pays ({start_year}→{end_year})...")

    # Récupération paginée
    all_records: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.worldbank.org/v2/country/{country_codes}"
            f"/indicator/{indicator}"
            f"?format=json&per_page=1000&date={start_year}:{end_year}&page={page}"
        )
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            raise RuntimeError(f"Erreur API World Bank : {exc}") from exc

        if not data or len(data) < 2 or not data[1]:
            break

        for item in data[1]:
            if item.get("value") is not None:
                iso3 = item.get("countryiso3code", "")
                all_records.append({
                    "country": countries.get(iso3, iso3),
                    "year": int(item["date"]),
                    "value": float(item["value"]) / scale,
                })

        if page >= data[0].get("pages", 1):
            break
        page += 1

    if not all_records:
        raise ValueError(
            f"Aucune donnée retournée pour l'indicateur {indicator!r}.\n"
            "Vérifiez le code indicateur sur https://data.worldbank.org/indicator"
        )

    df_raw = pd.DataFrame(all_records)
    df_pivot = df_raw.pivot_table(index="year", columns="country", values="value", aggfunc="mean")
    df_pivot.index = pd.to_datetime([f"{y}-01-01" for y in df_pivot.index])
    df_pivot = df_pivot.sort_index()

    # Forward-fill les années manquantes, puis 0 pour les pays sans historique
    df_pivot = df_pivot.ffill().fillna(0)
    df_pivot.index.name = "Date"

    print(f"{len(df_pivot)} années × {len(df_pivot.columns)} pays récupérés.")
    return df_pivot


# ─── Manuel ──────────────────────────────────────────────────────────────────

def load_manual(file_path: str) -> None:
    """
    Valide qu'un fichier Excel fourni manuellement existe et est lisible.

    Format attendu :
      - Colonne A (index) : dates au format YYYY-MM-DD
      - Colonnes B, C…   : un participant par colonne avec son nom en en-tête
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
