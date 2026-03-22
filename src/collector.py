import json
import time
import requests
import logging
from datetime import datetime, timezone
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config.settings as settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DELAY_BETWEEN_TOKENS = 150

def fetch_dexscreener(address):
    response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{address}")
    time.sleep(settings.DEXSCREENER_DELAY)
    if response.status_code == 200:
        pairs = response.json().get("pairs", [])
        if pairs:
            return max(pairs, key=lambda x: x.get("liquidity", {}).get("usd", 0))
    return {}

def fetch_geckoterminal_ohlcv(address, pool_address=None):
    """Fetch hourly OHLCV (24 candles = 24h)."""
    if not pool_address:
        dex_res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{address}")
        time.sleep(settings.DEXSCREENER_DELAY)
        pairs = dex_res.json().get("pairs", [])
        if not pairs:
            return [], None
        pool_address = pairs[0].get("pairAddress")
    url = f"https://api.geckoterminal.com/api/v2/networks/base/pools/{pool_address}/ohlcv/hour?limit=24"
    response = requests.get(url)
    time.sleep(settings.GECKOTERMINAL_DELAY)
    if response.status_code == 200:
        return response.json().get("data", {}).get("attributes", {}).get("ohlcv_list", []), pool_address
    return [], pool_address

def fetch_geckoterminal_ohlcv_15m(pool_address):
    """Fetch 15-min OHLCV (96 candles = 24h). Reuses pool_address from hourly call."""
    if not pool_address:
        return []
    url = f"https://api.geckoterminal.com/api/v2/networks/base/pools/{pool_address}/ohlcv/minute15?limit=96"
    response = requests.get(url)
    time.sleep(settings.GECKOTERMINAL_DELAY)
    if response.status_code == 200:
        return response.json().get("data", {}).get("attributes", {}).get("ohlcv_list", [])
    return []

def fetch_moralis_holders(address):
    if not settings.MORALIS_API_KEY:
        return []
    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{address}/owners?chain=base"
    headers = {"accept": "application/json", "X-API-Key": settings.MORALIS_API_KEY}
    response = requests.get(url, headers=headers)
    time.sleep(settings.MORALIS_DELAY)
    if response.status_code == 200:
        return response.json().get("result", [])
    return []

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tokens_path = os.path.join(base_dir, "config", "tokens.json")
    raw_dir = os.path.join(base_dir, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    with open(tokens_path, 'r') as f:
        tokens = json.load(f)
    
    total = len(tokens)
    estimated_time = total * DELAY_BETWEEN_TOKENS // 60
    logging.info(f"Demarrage collecte de {total} tokens (duree estimee: ~{estimated_time} min)")
    
    snapshot = {"timestamp": datetime.now(timezone.utc).isoformat(), "tokens": {}}
    
    for i, address in enumerate(tokens, 1):
        logging.info(f"[{i}/{total}] Collecte pour {address[:10]}...")
        
        pool_data = fetch_dexscreener(address)
        
        # Get pool address from DexScreener for GeckoTerminal calls
        pair_address = pool_data.get("pairAddress")
        
        # Hourly OHLCV (reuse pair_address to avoid extra DexScreener call)
        ohlcv_data, pool_addr = fetch_geckoterminal_ohlcv(address, pool_address=pair_address)
        
        # 15-min OHLCV (reuse same pool address — 1 extra GeckoTerminal call only)
        ohlcv_15m_data = fetch_geckoterminal_ohlcv_15m(pool_addr)
        
        holders_data = fetch_moralis_holders(address)
        
        snapshot["tokens"][address] = {
            "token_address": address,
            "chain": "base",
            "pool": pool_data,
            "holders": holders_data,
            "ohlcv": ohlcv_data,
            "ohlcv_15m": ohlcv_15m_data,
            "indicators": {}
        }
        
        symbol = pool_data.get("baseToken", {}).get("symbol", "???")
        logging.info(f"    {symbol} - {len(holders_data)} holders, {len(ohlcv_data)} candles 1H, {len(ohlcv_15m_data)} candles 15m")
        
        if i < total:
            logging.info(f"    Pause {DELAY_BETWEEN_TOKENS}s...")
            time.sleep(DELAY_BETWEEN_TOKENS)
    
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(raw_dir, f"snapshot_{timestamp_str}.json")
    with open(filepath, 'w') as f:
        json.dump(snapshot, f, indent=4)
    
    logging.info(f"Snapshot sauvegarde: {filepath}")

if __name__ == "__main__":
    main()
