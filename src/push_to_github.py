#!/usr/bin/env python3
import requests
import json
import base64
import os
import time
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = "JohnPreston2/0xdelta-hub"

OPENCLAW_TOKENS = [
    "0xB695559b26BB2c9703ef1935c37AeaE9526bab07",
    "0xe2f3FaE4bc62E21826018364aa30ae45D430bb07",
    "0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be",
    "0xc78fAbC2cB5B9cf59E0Af3Da8E3Bc46d47753A4e",
    "0xf48bC234855aB08ab2EC0cfaaEb2A80D065a3b07",
    "0xeff5672a3e73e104A56b7d16c1166f2Ae0714b07",
    "0xe6725BE5AC8DFf03538a9ef3E3a7A6BEd256bB4f",
    "0x2A767b649A4c469f2c4F88f85D4eFb6be7abFB07",
    "0xCe16Ef461d88256D2D80DFD31F0D9E7a9fD59213",
    "0x0f325c92DDbaF5712c960b7F6CA170e537321B07",
    "0xd655790B0486fa681c23B955F5Ca7Cd5f5C8Cb07",
    "0x4E6c9f48f73E54EE5F3AB7e2992B2d733D0d0b07",
    "0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07",
    "0x59c0d5c34C301aC0600147924D6C9be22a2F0B07",
    "0x9f86dB9fc6f7c9408e8Fda3Ff8ce4e78ac7a6b07",
    "0xf27b8ef47842E6445E37804896f1BC5e29381b07",
    "0x1bc0c42215582d5a085795f4badbac3ff36d1bcb",
    "0x3ec2156d4c0a9cbdab4a016633b7bcf6a8d68ea2",
    "0xa9FEE7b2F54781A14c85A1B8815345AefbE1EB07",
]

def fetch_trending_solana():
    try:
        response = requests.get("https://api.dexscreener.com/latest/dex/search?q=SOL", timeout=15)
        if response.status_code == 200:
            pairs = [p for p in response.json().get("pairs", []) if p.get("chainId") == "solana"]
            pairs.sort(key=lambda x: float(x.get("volume", {}).get("h24", 0) or 0), reverse=True)
            return [{"name": p.get('baseToken',{}).get('symbol',''), "symbol": p.get('baseToken',{}).get('symbol',''), "price_usd": p.get('priceUsd','0'), "price_change_24h": str(p.get('priceChange',{}).get('h24',0) or 0), "volume_24h": str(p.get('volume',{}).get('h24',0) or 0), "market_cap_usd": str(p.get('marketCap',0) or 0), "pool_address": p.get('pairAddress','')} for p in pairs[:10]]
    except Exception as e:
        print(f"Err Sol: {e}")
    return []

def fetch_trending_base():
    try:
        response = requests.get("https://api.dexscreener.com/latest/dex/search?q=base%20WETH", timeout=15)
        if response.status_code == 200:
            pairs = [p for p in response.json().get("pairs", []) if p.get("chainId") == "base"]
            pairs.sort(key=lambda x: float(x.get("volume", {}).get("h24", 0) or 0), reverse=True)
            return [{"name": p.get('baseToken',{}).get('symbol',''), "symbol": p.get('baseToken',{}).get('symbol',''), "price_usd": p.get('priceUsd','0'), "price_change_24h": str(p.get('priceChange',{}).get('h24',0) or 0), "volume_24h": str(p.get('volume',{}).get('h24',0) or 0), "market_cap_usd": str(p.get('marketCap',0) or 0), "pool_address": p.get('pairAddress','')} for p in pairs[:10]]
    except Exception as e:
        print(f"Err Base: {e}")
    return []

def fetch_openclaw():
    tokens = []
    for addr in OPENCLAW_TOKENS:
        try:
            r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addr}", timeout=10)
            time.sleep(0.3)
            if r.status_code == 200 and r.json().get("pairs"):
                p = max(r.json()["pairs"], key=lambda x: float(x.get("liquidity",{}).get("usd",0) or 0))
                tokens.append({"name": p.get('baseToken',{}).get('name',''), "symbol": p.get('baseToken',{}).get('symbol',''), "price_usd": p.get('priceUsd','0'), "price_change_24h": str(p.get('priceChange',{}).get('h24',0) or 0), "market_cap_usd": str(p.get('marketCap',0) or 0), "volume_24h": str(p.get('volume',{}).get('h24',0) or 0), "pool_address": p.get('pairAddress','')})
            else:
                tokens.append({"name": addr[:8], "symbol": "???", "price_usd": "0", "price_change_24h": "0", "market_cap_usd": "0", "volume_24h": "0", "pool_address": "---"})
        except:
            pass
    return tokens

def push_file_to_github(filename, content_str):
    """Push a single file to GitHub repo."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{REPO}/contents/{filename}"
    
    # Get current SHA
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha", "") if r.status_code == 200 else ""
    
    content = base64.b64encode(content_str.encode()).decode()
    payload = {"message": f"Update {filename}", "content": content, "branch": "main"}
    if sha:
        payload["sha"] = sha
    
    r = requests.put(url, headers=headers, json=payload)
    if r.status_code in [200, 201]:
        print(f"OK -> {filename} pushed")
        return True
    print(f"Err {filename}: {r.status_code} {r.text[:100]}")
    return False

def main():
    print(f"Fetch - {datetime.now(timezone.utc).strftime('%H:%M')}")
    sol = fetch_trending_solana()
    base = fetch_trending_base()
    openclaw = fetch_openclaw()
    print(f"  Sol:{len(sol)} Base:{len(base)} OC:{len(openclaw)}")
    
    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "trending_solana": sol,
        "trending_base": base,
        "volume_solana": [],
        "volume_base": [],
        "openclaw_tokens": openclaw,
    }
    push_file_to_github("data.json", json.dumps(data, indent=2))
    
    # Also push signals.json if it exists
    signals_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "signals.json")
    if os.path.exists(signals_path):
        with open(signals_path, 'r') as f:
            signals_content = f.read()
        push_file_to_github("signals.json", signals_content)
    else:
        print("signals.json not found, skipping")

if __name__ == "__main__":
    main()
