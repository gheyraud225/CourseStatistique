"""
Téléchargement automatique des logos/drapeaux dans le dossier assets/.

  - Logos crypto  : CoinGecko API (gratuit, sans clé)
  - Logos actions : Clearbit Logo API (gratuit, sans clé)
  - Drapeaux pays : flagcdn.com (gratuit, sans clé)
"""
from __future__ import annotations

import io
import os

import requests
from PIL import Image

ASSETS_DIR = "assets"
LOGO_SIZE = (130, 130)
FLAG_SIZE = (130, 87)    # Ratio 3:2 pour les drapeaux

# ── CoinGecko : ticker Yahoo → ID CoinGecko ──────────────────────────────────
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
}

# ── Clearbit : ticker Yahoo → domaine web ────────────────────────────────────
COMPANY_DOMAINS: dict[str, str] = {
    "AAPL":  "apple.com",
    "MSFT":  "microsoft.com",
    "NVDA":  "nvidia.com",
    "GOOGL": "google.com",
    "GOOG":  "google.com",
    "AMZN":  "amazon.com",
    "META":  "meta.com",
    "TSLA":  "tesla.com",
    "NFLX":  "netflix.com",
    "AMD":   "amd.com",
    "INTC":  "intel.com",
    "ORCL":  "oracle.com",
    "SHOP":  "shopify.com",
    "UBER":  "uber.com",
    "SNAP":  "snap.com",
    "SPOT":  "spotify.com",
    "CRM":   "salesforce.com",
    "PYPL":  "paypal.com",
    "SQ":    "squareup.com",
    "COIN":  "coinbase.com",
}

# ── ISO 3166-1 alpha-3 → alpha-2 (flagcdn.com) ───────────────────────────────
ISO3_TO_ISO2: dict[str, str] = {
    "USA": "us", "CHN": "cn", "RUS": "ru", "DEU": "de",
    "GBR": "gb", "FRA": "fr", "IND": "in", "JPN": "jp",
    "SAU": "sa", "ITA": "it", "BRA": "br", "KOR": "kr",
    "AUS": "au", "CAN": "ca", "ISR": "il", "TUR": "tr",
    "ESP": "es", "NLD": "nl", "POL": "pl", "UKR": "ua",
    "MEX": "mx", "IDN": "id", "NGA": "ng", "ZAF": "za",
    "ARG": "ar", "PAK": "pk", "EGY": "eg", "IRN": "ir",
    "IRQ": "iq", "SWE": "se", "NOR": "no", "CHE": "ch",
    "BEL": "be", "GRC": "gr", "PRT": "pt", "FIN": "fi",
    "DNK": "dk", "CZE": "cz", "HUN": "hu", "ROU": "ro",
    "AUT": "at", "SGP": "sg", "MYS": "my", "THA": "th",
    "VNM": "vn", "PHL": "ph", "BGD": "bd", "ETH": "et",
    "KEN": "ke", "GHA": "gh", "DZA": "dz", "MAR": "ma",
    "KAZ": "kz", "CHL": "cl", "COL": "co", "PER": "pe",
    "PRK": "kp", "TWN": "tw", "MMR": "mm", "SDN": "sd",
}


def _fetch_and_save(url: str, name: str, size: tuple[int, int]) -> bool:
    """Télécharge, redimensionne et sauvegarde dans assets/{name}.png."""
    path = os.path.join(ASSETS_DIR, f"{name}.png")
    if os.path.exists(path):
        return True
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


def download_logos_yfinance(tickers: dict, source_type: str = "crypto") -> None:
    """
    Télécharge les logos pour les tickers Yahoo Finance.
    - source_type='crypto' → CoinGecko
    - source_type='stocks' → Clearbit
    """
    os.makedirs(ASSETS_DIR, exist_ok=True)
    needed = [
        (ticker, name)
        for ticker, name in tickers.items()
        if not os.path.exists(os.path.join(ASSETS_DIR, f"{name}.png"))
    ]
    if not needed:
        return

    if source_type == "stocks":
        print("Téléchargement des logos (Google favicon)...")
        for ticker, name in needed:
            domain = COMPANY_DOMAINS.get(ticker.upper())
            if not domain:
                print(f"  ✗ {ticker} : domaine inconnu — placez assets/{name}.png manuellement")
                continue
            # Google favicon service (256px) — fonctionne sans clé API
            url = f"https://www.google.com/s2/favicons?domain={domain}&sz=256"
            ok = _fetch_and_save(url, name, LOGO_SIZE)
            if not ok:
                # Fallback : DuckDuckGo icons
                _fetch_and_save(f"https://icons.duckduckgo.com/ip3/{domain}.ico", name, LOGO_SIZE)
    else:
        print("Téléchargement des logos crypto (CoinGecko)...")
        for ticker, name in needed:
            coin_id = COINGECKO_IDS.get(ticker)
            if not coin_id:
                print(f"  ✗ {ticker} : ID CoinGecko inconnu — placez assets/{name}.png manuellement")
                continue
            try:
                api = requests.get(
                    f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                    timeout=15,
                    headers={"Accept": "application/json"},
                )
                api.raise_for_status()
                img_url = api.json()["image"]["large"]
                _fetch_and_save(img_url, name, LOGO_SIZE)
            except Exception as exc:
                print(f"  ✗ {name} : {exc}")


def download_country_flags(countries: dict) -> None:
    """Télécharge les drapeaux depuis flagcdn.com."""
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
            print(f"  ✗ {iso3} : code ISO2 inconnu — placez assets/{name}.png manuellement")
            continue
        _fetch_and_save(f"https://flagcdn.com/w160/{iso2}.png", name, FLAG_SIZE)
