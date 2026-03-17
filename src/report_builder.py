import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, '/home/classics2323/.openclaw/workspace/skills/crypto-forensics-v5')
from forensic_engine_v5 import ForensicEngineV5
sys.path.insert(0, '/home/classics2323')
from forensic_memory import ForensicMemoryManager

import requests

def publish_forensic_digest(results):
    """Publie un tableau synthèse des 17 tokens sur Moltbook"""
    MOLTBOOK_API_KEY = os.environ.get("MOLTBOOK_API_KEY", "")
    MOLTBOOK_URL = "https://www.moltbook.com/api/v1/posts"
    
    # Construction du tableau synthétique
    header = "| Token | FHS | Phase | BPI | NBP |\n|---|---|---|---|---|\n"
    rows = []
    
    # Trier par FHS décroissant
    sorted_tokens = sorted(results["tokens"].values(), key=lambda x: x["convergence"]["fhs"], reverse=True)
    
    for t in sorted_tokens[:10]: # Top 10 pour la lisibilité
        symbol = t["symbol"]
        fhs = t["convergence"]["fhs"]
        phase = t["convergence"]["phase"]
        bpi = round(t["bull_flag"]["bpi"], 2)
        nbp = round(t["flows"]["nbp"], 1)
        rows.append(f"| {symbol} | {fhs} | {phase} | {bpi} | {nbp}% |")
    
    content = f"📊 **0xDvta Forensic Digest — {datetime.now(timezone.utc).strftime('%H:%M UTC')}**\n\n"
    content += header + "\n".join(rows)
    content += "\n\nFull pipeline analysis complete. Monitoring for Sequential Pulse injection.\n#Base #Forensic #Trading"

    try:
        payload = {
            "submolt_name": "trading",
            "title": f"FORENSIC REPORT: {len(results['tokens'])} Conduits Scan",
            "content": content
        }
        requests.post(MOLTBOOK_URL, headers={"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=10)
        print("📣 Digest Forensique publié sur Moltbook.")
    except:
        print("⚠️ Échec publication Digest.")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    snapshots = sorted([f for f in os.listdir(raw_dir) if f.startswith("snapshot_")])
    if not snapshots:
        print("Aucun snapshot trouvé")
        return
    
    latest = snapshots[-1]
    filepath = os.path.join(raw_dir, latest)
    print(f"Analyse de {latest}...")
    
    with open(filepath) as f:
        data = json.load(f)
    
    engine = ForensicEngineV5()
    memory = ForensicMemoryManager()
    results = {
        "timestamp": data.get("timestamp"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tokens_count": len(data["tokens"]),
        "tokens": {}
    }
    
    for addr, token_data in data["tokens"].items():
        report = engine.analyze(token_data)
        report_dict = report.to_dict()
        
        # Ajouter les données holders brutes (top 20)
        holders_raw = token_data.get("holders", [])
        if isinstance(holders_raw, list):
            report_dict["top20_holders"] = []
            for h in holders_raw[:20]:
                report_dict["top20_holders"].append({
                    "address": h.get("owner_address", ""),
                    "usd_value": float(h.get("usd_value", 0)),
                    "pct_supply": float(h.get("percentage_relative_to_total_supply", 0)),
                    "is_contract": h.get("is_contract", False),
                    "entity": h.get("entity"),
                    "label": h.get("owner_address_label")
                })
        
        # Ajouter prix et market data
        pool = token_data.get("pool", {})
        report_dict["market_data"] = {
            "price_usd": float(pool.get("priceUsd", 0)),
            "price_change_24h": float(pool.get("priceChange", {}).get("h24", 0)),
            "volume_24h": float(pool.get("volume", {}).get("h24", 0)),
            "liquidity_usd": float(pool.get("liquidity", {}).get("usd", 0)),
            "fdv": float(pool.get("fdv", 0)),
            "mcap": float(pool.get("marketCap", 0)),
            "buys_24h": int(pool.get("txns", {}).get("h24", {}).get("buys", 0)),
            "sells_24h": int(pool.get("txns", {}).get("h24", {}).get("sells", 0))
        }
        
        results["tokens"][addr] = report_dict
        print(f"  ✅ {report.symbol}: FHS={report.convergence.fhs}/10, Phase={report.convergence.phase}")
        memory.update(report_dict, token_address=addr)
    
    timestamp_str = latest.replace("snapshot_", "").replace(".json", "")
    output_file = os.path.join(processed_dir, f"forensic_{timestamp_str}.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Rapport sauvegardé: {output_file}")
    print(f"📊 {len(results['tokens'])} tokens analysés")

if __name__ == "__main__":
    main()
