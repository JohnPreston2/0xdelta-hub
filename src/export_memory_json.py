"""
export_memory_json.py — v3
Lit directement le dernier rapport forensic dans data/processed/
et exporte TOUS les champs (65) vers memory.json pour le frontend.
"""

import json
import os
from pathlib import Path
from datetime import datetime

PROCESSED_DIR = Path("/home/classics2323/crypto-monitor/data/processed")
OUTPUT        = Path("/home/classics2323/crypto-monitor/frontend/memory.json")

def load_latest_report():
    files = sorted([f for f in PROCESSED_DIR.glob("forensic_*.json")])
    if not files:
        print("[ERROR] Aucun rapport forensic trouvé")
        return None
    latest = files[-1]
    print(f"[OK] Rapport chargé: {latest.name}")
    with open(latest) as f:
        return json.load(f)

def build_history(symbol, address):
    """Reconstruit l'historique FHS/NBP/ICR sur les 24 derniers rapports."""
    files = sorted(PROCESSED_DIR.glob("forensic_*.json"))[-24:]
    history = []
    for f in files:
        try:
            data = json.load(open(f))
            # cherche par adresse ou par symbol
            token = None
            for addr, t in data.get("tokens", {}).items():
                if addr.lower() == address.lower() or t.get("symbol","").upper() == symbol.upper():
                    token = t
                    break
            if token:
                ts = data.get("timestamp", "")[:16].replace("T", " ").replace("-", "-")[5:]
                history.append({
                    "ts":    ts,
                    "fhs":   token.get("convergence", {}).get("fhs", 0),
                    "phase": token.get("convergence", {}).get("phase", "?")[:4],
                    "nbp":   f"{token.get('flows', {}).get('nbp', 0):.0f}%",
                    "icr":   round(token.get("liquidity", {}).get("icr", 0), 2),
                    "flow":  token.get("flows", {}).get("flow_classification", "?")[:4],
                })
        except Exception as e:
            continue
    return history

def transform_token(address, t):
    """Transforme un token du rapport brut en objet frontend complet."""
    liq   = t.get("liquidity", {})
    flows = t.get("flows", {})
    bf    = t.get("bull_flag", {})
    tech  = t.get("technical", {})
    forn  = t.get("forensic", {})
    conv  = t.get("convergence", {})
    mkt   = t.get("market_data", {})
    raw   = t.get("raw_metrics", {})

    symbol = t.get("symbol", address[:8])

    return {
        # Identité
        "symbol":  symbol,
        "address": address[:8],
        "chain":   t.get("chain", "base"),

        # Convergence
        "fhs":   conv.get("fhs", 0),
        "fhs_label": conv.get("fhs_label", ""),
        "phase": conv.get("phase", "UNKNOWN"),
        "cp":    conv.get("cp", 0),

        # Liquidité
        "icr":               liq.get("icr", 0),
        "icr_alert":         liq.get("icr_alert", False),
        "lcr":               liq.get("lcr", 0),
        "lcr_fragile":       liq.get("lcr_fragile", False),
        "lvr":               liq.get("lvr", 0),
        "lvr_status":        liq.get("lvr_status", ""),
        "dai":               liq.get("dai", 0),
        "dai_status":        liq.get("dai_status", ""),
        "crash_threshold":   liq.get("crash_threshold_usd", 0),
        "ips_10k":           liq.get("ips_10k", 0),
        "ips_50k":           liq.get("ips_50k", 0),
        "ips_100k":          liq.get("ips_100k", 0),

        # Flows
        "nbp":               flows.get("nbp", 0),
        "nbp_status":        flows.get("nbp_status", ""),
        "ev":                flows.get("ev", 0),
        "ev_trend":          flows.get("ev_trend", ""),
        "ac":                flows.get("ac", 0),
        "vwad":              flows.get("vwad", 0),
        "flow_classification": flows.get("flow_classification", ""),

        # Bull Flag
        "bull_flag":         bf.get("detected", False),
        "bf_retracement":    bf.get("retracement_pct", 0),
        "bf_class":          bf.get("flag_class", 0),
        "fqs":               bf.get("fqs", 0),
        "fqs_label":         bf.get("fqs_label", ""),
        "bpi":               bf.get("bpi", 0),
        "bpi_label":         bf.get("bpi_label", ""),
        "fib_target":        bf.get("fib_target_1618", 0),
        "fib_upside_pct":    bf.get("fib_upside_pct", 0),
        "pole_high":         bf.get("pole_high", 0),
        "pole_low":          bf.get("pole_low", 0),
        "squeeze_factor":    bf.get("squeeze_factor", 1),

        # Technique
        "rsi_1h":    tech.get("rsi_1h", 0),
        "rsi_1d":    tech.get("rsi_1d", 0),
        "ber":       tech.get("ber", 0),
        "ber_zone":  tech.get("ber_zone", ""),
        "rmd":       tech.get("rmd", 0),
        "rmd_divergence": tech.get("rmd_divergence", ""),
        "si":        tech.get("si", 0),
        "si_status": tech.get("si_status", ""),
        "saturated": tech.get("saturated", False),

        # Forensic
        "wcc":       forn.get("wcc", 0),
        "wcc_alert": forn.get("wcc_alert", False),
        "scr":       forn.get("scr", 0),
        "tci":       forn.get("tci", 0),
        "fci":       forn.get("fci", 0),
        "top5_pct":  forn.get("top5_pct", 0),
        "top10_pct": forn.get("top10_pct", 0),
        "top20_pct": forn.get("top20_pct", 0),

        # Market data
        "price_usd":       mkt.get("price_usd", raw.get("price", 0)),
        "price_change_24h": mkt.get("price_change_24h", raw.get("price_change_24h", 0)),
        "volume_24h":      mkt.get("volume_24h", raw.get("volume_24h", 0)),
        "liquidity_usd":   mkt.get("liquidity_usd", raw.get("liquidity", 0)),
        "mcap":            mkt.get("mcap", raw.get("mcap", 0)),
        "buys_24h":        mkt.get("buys_24h", int(raw.get("buys", 0))),
        "sells_24h":       mkt.get("sells_24h", int(raw.get("sells", 0))),

        # Narratives
        "narrative_phase":     t.get("narrative_phase", ""),
        "narrative_insight":   t.get("narrative_insight", ""),
        "narrative_structure": t.get("narrative_structure", ""),
        "support_key":         t.get("support_key", 0),
        "resistance_key":      t.get("resistance_key", 0),

        # Alertes
        "alerts": t.get("alerts", []),

        # Top 20 holders
        "top20_holders": t.get("top20_holders", []),

        # Historique
        "history": build_history(symbol, address),
    }

def run():
    report = load_latest_report()
    if not report:
        return

    tokens = []
    for address, t in report.get("tokens", {}).items():
        try:
            token = transform_token(address, t)
            tokens.append(token)
            print(f"  {token['symbol']:12} FHS={token['fhs']} phase={token['phase']} top20={len(token['top20_holders'])} rsi={token['rsi_1h']}")
        except Exception as e:
            print(f"[WARN] {address[:8]}: {e}")

    # Trier par FHS décroissant
    tokens.sort(key=lambda x: x.get("fhs", 0), reverse=True)

    out = {
        "updated_at": report.get("generated_at", datetime.utcnow().isoformat()),
        "count":      len(tokens),
        "tokens":     tokens
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\n[OK] {len(tokens)} tokens → {OUTPUT}")

if __name__ == "__main__":
    run()
