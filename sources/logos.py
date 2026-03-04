"""
Téléchargement automatique des logos/drapeaux dans le dossier assets/.

- Logos crypto  : CoinGecko (gratuit, sans clé API)
- Drapeaux pays : flagcdn.com (gratuit, sans clé API)
"""
from __future__ import annotations

import io
import os

import requests
from PIL import Image

ASSETS_DIR = "assets"
LOGO_SIZE = (130, 130)      # Taille cible pour les logos (pixels)
FLAG_SIZE = (130, 87)       # Taille cible pour les drapeaux (ratio 3:2)

# ─── Correspondances ticker → ID CoinGecko ───────────────────────────────────
COINGECKO_IDS: dict[str, str] = {
    "BTC-USD":   "bitcoin",
    "ETH-USD":   "ethereum",
    "DOGE-USD":  "dogecoin",
    "BNB-USD":   "binancecoin",
    "SOL-USD":   "solana",
    "XRP-USD":   "ripple",
    "ADA-USD":   "cardano",
    "DOT-USD":   "polkadot",
    "AVAX-USD":  "avalanche-2",
    "MATIC-USD": "matic-network",
    "LINK-USD":  "chainlink",
    "LTC-USD":   "litecoin",
    "ATOM-USD":  "cosmos",
    "UNI-USD":   "uniswap",
    "SHIB-USD":  "shiba-inu",
    "TRX-USD":   "tron",
    "NEAR-USD":  "near",
    "APT-USD":   "aptos",
    "ARB-USD":   "arbitrum",
    "OP-USD":    "optimism",
}

# ─── Correspondances ISO 3166-1 alpha-3 → alpha-2 (pour flagcdn.com) ─────────
ISO3_TO_ISO2: dict[str, str] = {
    "USA": "us", "CHN": "cn", "RUS": "ru", "DEU": "de",
    "GBR": "gb", "FRA": "fr", "IND": "in", "JPN": "jp",
    "SAU": "sa", "ITA": "it", "BRA": "br", "KOR": "kr",
    "AUS": "au", "CAN": "ca", "ISR": "il", "TUR": "tr",
    "ESP": "es", "NLD": "nl", "POL": "pl", "UKR": "ua",
    "MEX": "mx", "IDN": "id", "NGA": "ng", "ZAF": "za",
    "ARG": "ar", "PAK": "pk", "EGY": "eg", "IRN": "ir",
    "IRQ": "iq", "SYR": "sy", "YEM": "ye", "AFG": "af",
    "SWE": "se", "NOR": "no", "CHE": "ch", "BEL": "be",
    "GRC": "gr", "PRT": "pt", "FIN": "fi", "DNK": "dk",
    "CZE": "cz", "HUN": "hu", "ROU": "ro", "AUT": "at",
    "SGP": "sg", "MYS": "my", "THA": "th", "VNM": "vn",
    "PHL": "ph", "BGD": "bd", "ETH": "et", "TZA": "tz",
    "KEN": "ke", "GHA": "gh", "DZA": "dz", "MAR": "ma",
    "KAZ": "kz", "UZB": "uz", "CHL": "cl", "COL": "co",
    "PER": "pe", "VEN": "ve", "PRK": "kp", "TWN": "tw",
    "MMR": "mm", "SDN": "sd", "AGO": "ao", "MOZ": "mz",
}


def _fetch_and_save(url: str, name: str, size: tuple[int, int]) -> bool:
    """Télécharge une image, la redimensionne et la sauvegarde dans assets/."""
    path = os.path.join(ASSETS_DIR, f"{name}.png")
    if os.path.exists(path):
        return True     # Déjà présent, rien à faire

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        img = img.resize(size, Image.LANCZOS)
        img.save(path)
        print(f"  ✓ {name}.png")
        return True
    except Exception as exc:
        print(f"  ✗ {name} : {exc}")
        return False


def download_crypto_logos(tickers: dict) -> None:
    """
    Télécharge les logos crypto depuis l'API CoinGecko (gratuite, sans clé).

    :param tickers: dict {ticker_yahoo: nom_affichage}, ex. {"BTC-USD": "Bitcoin"}
    """
    os.makedirs(ASSETS_DIR, exist_ok=True)
    needed = [
        (ticker, name)
        for ticker, name in tickers.items()
        if not os.path.exists(os.path.join(ASSETS_DIR, f"{name}.png"))
    ]
    if not needed:
        return

    print("Téléchargement des logos crypto (CoinGecko)...")
    for ticker, name in needed:
        coin_id = COINGECKO_IDS.get(ticker)
        if not coin_id:
            print(f"  ✗ {ticker} : ID CoinGecko inconnu — placez manuellement assets/{name}.png")
            continue
        try:
            api_resp = requests.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                timeout=15,
                headers={"Accept": "application/json"},
            )
            api_resp.raise_for_status()
            img_url = api_resp.json()["image"]["large"]
            _fetch_and_save(img_url, name, LOGO_SIZE)
        except Exception as exc:
            print(f"  ✗ {name} : {exc}")


def download_country_flags(countries: dict) -> None:
    """
    Télécharge les drapeaux depuis flagcdn.com (gratuit, sans clé).

    :param countries: dict {code_iso3: nom_affichage}, ex. {"USA": "États-Unis"}
    """
    os.makedirs(ASSETS_DIR, exist_ok=True)
    needed = [
        (iso3, name)
        for iso3, name in countries.items()
        if not os.path.exists(os.path.join(ASSETS_DIR, f"{name}.png"))
    ]
    if not needed:
        return

    print("Téléchargement des drapeaux (flagcdn.com)...")
    for iso3, name in needed:
        iso2 = ISO3_TO_ISO2.get(iso3.upper())
        if not iso2:
            print(f"  ✗ {iso3} : code ISO2 inconnu — placez manuellement assets/{name}.png")
            continue
        _fetch_and_save(f"https://flagcdn.com/w160/{iso2}.png", name, FLAG_SIZE)
