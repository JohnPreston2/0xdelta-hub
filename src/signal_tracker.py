#!/usr/bin/env python3
"""
🔄 Signal Evolution Tracker — Step 2b
======================================
Compare cycle N (fresh from report_builder) vs cycle N-1.
Calls Venice AI to analyze signal evolution, price/volume deltas, and memory trends.
Outputs signals.json for injection into Step 3 (request_analysis.py).
"""

import requests
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# ── Config ──
VENICE_API_KEY = os.environ.get("VENICE_API_KEY", "")
VENICE_URL = "https://api.venice.ai/api/v1/chat/completions"
PROCESSED_DIR = "/home/classics2323/crypto-monitor/data/processed"
MEMORY_DIR = Path.home() / ".openclaw" / "agents" / "main" / "memory"
SIGNALS_FILE = "/home/classics2323/crypto-monitor/data/signals.json"
DECISIONS_FILE = "/home/classics2323/.openclaw/workspace/mind/DECISIONS.md"
ERRORS_FILE = "/home/classics2323/.openclaw/workspace/mind/ERRORS.md"

def load_reports():
    files = sorted([f for f in os.listdir(PROCESSED_DIR) if f.startswith("forensic_")])
    if not files: return None, None
    with open(os.path.join(PROCESSED_DIR, files[-1])) as f: current = json.load(f)
    previous = None
    if len(files) > 1:
        with open(os.path.join(PROCESSED_DIR, files[-2])) as f: previous = json.load(f)
    return current, previous

def extract_market_data(report):
    if not report: return {}
    snapshot = {}
    for addr, t in report.get("tokens", {}).items():
        symbol = t.get("symbol", addr[:8])
        pool = t.get("pool", {})
        conv = t.get("convergence", {})
        flows = t.get("flows", {})
        bf = t.get("bull_flag", {})
        liq = t.get("liquidity", {})
        snapshot[symbol] = {
            "price_usd": float(pool.get("priceUsd", 0)),
            "change_24h": float(pool.get("priceChange", {}).get("h24", 0)),
            "volume_24h": float(pool.get("volume", {}).get("h24", 0)),
            "liquidity_usd": float(pool.get("liquidity", {}).get("usd", 0)),
            "mcap": float(pool.get("marketCap", 0)),
            "fdv": float(pool.get("fdv", 0)),
            "buys_24h": int(pool.get("txns", {}).get("h24", {}).get("buys", 0)),
            "sells_24h": int(pool.get("txns", {}).get("h24", {}).get("sells", 0)),
            "fhs": conv.get("fhs", 0),
            "phase": conv.get("phase", ""),
            "nbp": flows.get("nbp", 0),
            "bpi": bf.get("bpi", 0),
            "bull_flag_detected": bf.get("detected", False),
            "flag_class": bf.get("flag_class", 0),
            "icr": liq.get("icr", 0),
            "lcr": liq.get("lcr", 0),
            "dai": liq.get("dai", 0),
        }
    return snapshot

def compute_deltas(current_snap, previous_snap):
    deltas = {}
    for symbol, curr in current_snap.items():
        prev = previous_snap.get(symbol, {})
        if not prev:
            deltas[symbol] = {"status": "NEW_TOKEN"}
            continue
        prev_price = prev.get("price_usd", 0)
        curr_price = curr.get("price_usd", 0)
        prev_vol = prev.get("volume_24h", 0)
        curr_vol = curr.get("volume_24h", 0)
        prev_liq = prev.get("liquidity_usd", 0)
        curr_liq = curr.get("liquidity_usd", 0)
        deltas[symbol] = {
            "price_delta_pct": round(((curr_price - prev_price) / prev_price * 100) if prev_price else 0, 2),
            "volume_delta_pct": round(((curr_vol - prev_vol) / prev_vol * 100) if prev_vol else 0, 2),
            "liquidity_delta_pct": round(((curr_liq - prev_liq) / prev_liq * 100) if prev_liq else 0, 2),
            "fhs_delta": round(curr.get("fhs", 0) - prev.get("fhs", 0), 1),
            "nbp_delta": round(curr.get("nbp", 0) - prev.get("nbp", 0), 1),
            "bpi_delta": round(curr.get("bpi", 0) - prev.get("bpi", 0), 3),
            "icr_delta": round(curr.get("icr", 0) - prev.get("icr", 0), 2),
            "phase_changed": curr.get("phase", "") != prev.get("phase", ""),
            "prev_phase": prev.get("phase", ""),
            "bull_flag_new": curr.get("bull_flag_detected", False) and not prev.get("bull_flag_detected", False),
            "bull_flag_lost": not curr.get("bull_flag_detected", False) and prev.get("bull_flag_detected", False),
        }
    return deltas

def load_top_memories(current_snap, top_n=5):
    sorted_tokens = sorted(current_snap.items(), key=lambda x: x[1].get("fhs", 0), reverse=True)
    memories = {}
    for symbol, data in sorted_tokens[:top_n]:
        matches = list(MEMORY_DIR.glob(f"{symbol}_*.md"))
        if matches:
            content = matches[0].read_text(encoding="utf-8")
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "| Heure |" in line:
                    memories[symbol] = "\n".join(lines[i:])
                    break
            if symbol not in memories:
                memories[symbol] = content[-1000:]
    return memories

def load_previous_signals():
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE) as f: return json.load(f)
    return {"signals": [], "cycle": 0}

def load_decisions():
    content = ""
    for f in [DECISIONS_FILE, ERRORS_FILE]:
        if os.path.exists(f):
            with open(f) as fh: content += fh.read() + "\n\n"
    return content

def build_tracker_prompt(current_snap, deltas, memories, prev_signals, decisions):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    market_lines = ["| Token | Price | \u03942h | \u039424h | Vol 24h | \u0394Vol | Liq | MCap | FHS | Phase |"]
    market_lines.append("|-------|-------|-----|------|---------|------|-----|------|-----|-------|")
    for symbol, data in sorted(current_snap.items(), key=lambda x: x[1].get("fhs", 0), reverse=True):
        d = deltas.get(symbol, {})
        price = data.get("price_usd", 0)
        price_str = f"${price:.2f}" if price >= 1 else f"${price:.6f}" if price < 0.01 else f"${price:.4f}"
        vol = data.get("volume_24h", 0)
        vol_str = f"${vol/1000:.0f}K" if vol >= 1000 else f"${vol:.0f}"
        liq = data.get("liquidity_usd", 0)
        liq_str = f"${liq/1000:.0f}K" if liq >= 1000 else f"${liq:.0f}"
        mcap = data.get("mcap", 0)
        mcap_str = f"${mcap/1e6:.1f}M" if mcap >= 1e6 else f"${mcap/1000:.0f}K"
        market_lines.append(f"| {symbol} | {price_str} | {d.get('price_delta_pct',0):+.1f}% | {data.get('change_24h',0):+.1f}% | {vol_str} | {d.get('volume_delta_pct',0):+.0f}% | {liq_str} | {mcap_str} | {data.get('fhs',0):.1f} | {data.get('phase','')[:5]} |")
    market_table = "\n".join(market_lines)
    delta_lines = []
    for symbol, d in deltas.items():
        if d.get("status") == "NEW_TOKEN": continue
        changes = []
        if abs(d.get("price_delta_pct", 0)) > 2: changes.append(f"Price {d['price_delta_pct']:+.1f}%")
        if abs(d.get("volume_delta_pct", 0)) > 20: changes.append(f"Vol {d['volume_delta_pct']:+.0f}%")
        if abs(d.get("fhs_delta", 0)) >= 0.5: changes.append(f"FHS {d['fhs_delta']:+.1f}")
        if abs(d.get("nbp_delta", 0)) > 10: changes.append(f"NBP {d['nbp_delta']:+.0f}")
        if d.get("phase_changed"): changes.append(f"Phase: {d['prev_phase']} \u2192 {current_snap[symbol]['phase']}")
        if d.get("bull_flag_new"): changes.append("\ud83d\udea9 NEW BULL FLAG")
        if d.get("bull_flag_lost"): changes.append("\u274c BULL FLAG LOST")
        if changes: delta_lines.append(f"- **{symbol}**: {', '.join(changes)}")
    deltas_text = "\n".join(delta_lines) if delta_lines else "No significant changes this cycle."
    prev_sig_text = ""
    if prev_signals.get("signals"):
        prev_sig_text = "ACTIVE SIGNALS FROM PREVIOUS CYCLE:\n"
        for sig in prev_signals["signals"]:
            prev_sig_text += f"- {sig['symbol']}: {sig['type']} (status: {sig['status']}) \u2014 {sig.get('note', '')}\n"
    memory_text = ""
    if memories:
        memory_text = "48H MEMORY TRENDS (top tokens):\n"
        for symbol, hist in memories.items():
            memory_text += f"\n--- {symbol} ---\n{hist}\n"
    rules_text = decisions[:2000] if decisions else ""
    return f"""CRITICAL: Respond ENTIRELY in English. No French.

You are 0xDELTA's Signal Evolution Tracker. Analyze HOW signals are evolving between cycles.

Current time: {now}

## MARKET SNAPSHOT (current cycle vs 2h ago)
{market_table}

## SIGNIFICANT CHANGES THIS CYCLE
{deltas_text}

## PREVIOUS SIGNALS TO TRACK
{prev_sig_text or "No previous signals."}

## 48H MEMORY TRENDS
{memory_text or "No memory data available."}

## TRADING RULES
{rules_text}

---

Generate a Signal Evolution Report:

### 1. MARKET OVERVIEW (2-3 sentences)
### 2. PRICE & VOLUME HIGHLIGHTS (tokens with significant movement)
### 3. SIGNAL TRACKING (update status of previous signals: CONFIRMED/HOLDING/WEAKENING/INVALIDATED)
### 4. NEW SIGNALS DETECTED
### 5. SIGNAL WATCHLIST (JSON)
```json
[{{"symbol": "TOKEN", "type": "SIGNAL_TYPE", "status": "STATUS", "since": "timestamp", "note": "explanation"}}]
```
Types: SAC, BULL_FLAG, ICR_CRITICAL, DISTRIBUTION, VPD_ABSORPTION, VPD_EXHAUSTION, PHASE_CHANGE, WHALE_MOVE
### 6. KEY INSIGHT (one sentence)"""

def call_venice(prompt, data_payload):
    payload = {"model": "gemini-3-flash-preview", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": f"Analyze:\n{json.dumps(data_payload, indent=None)}"}], "max_tokens": 2500}
    try:
        r = requests.post(VENICE_URL, headers={"Authorization": f"Bearer {VENICE_API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=120)
        if r.status_code == 200: return r.json()["choices"][0]["message"]["content"]
        else: print(f"\u274c Venice error: {r.status_code}"); return None
    except Exception as e: print(f"\u274c Venice exception: {e}"); return None

def extract_signals_json(response):
    try:
        import re
        match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
        if match: return json.loads(match.group(1))
        match = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
        if match: return json.loads(match.group(0))
    except: pass
    return []

def save_signals(signals, report_text):
    output = {"updated_at": datetime.now(timezone.utc).isoformat(), "cycle": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M"), "signals": signals, "evolution_report": report_text}
    os.makedirs(os.path.dirname(SIGNALS_FILE), exist_ok=True)
    with open(SIGNALS_FILE, "w") as f: json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\u2705 signals.json written \u2192 {SIGNALS_FILE}")

def main():
    print("\ud83d\udd04 Signal Evolution Tracker \u2014 loading data...")
    current, previous = load_reports()
    if not current: print("\u274c No report found"); return
    current_snap = extract_market_data(current)
    previous_snap = extract_market_data(previous) if previous else {}
    print(f"\ud83d\udcca Current: {len(current_snap)} tokens | Previous: {len(previous_snap)} tokens")
    deltas = compute_deltas(current_snap, previous_snap) if previous_snap else {}
    memories = load_top_memories(current_snap, top_n=5)
    print(f"\ud83e\udde0 Loaded {len(memories)} memory files")
    prev_signals = load_previous_signals()
    print(f"\ud83d\udce1 Previous signals: {len(prev_signals.get('signals', []))}")
    decisions = load_decisions()
    prompt = build_tracker_prompt(current_snap, deltas, memories, prev_signals, decisions)
    data_payload = {"current_metrics": {s: {k: v for k, v in d.items() if k in ['fhs','phase','nbp','bpi','icr','dai','bull_flag_detected']} for s, d in current_snap.items()}, "deltas": deltas}
    print("\ud83e\udd16 Calling Venice AI (Signal Tracker)...")
    response = call_venice(prompt, data_payload)
    if response:
        print("\u2705 Signal Evolution Report generated")
        signals = extract_signals_json(response)
        print(f"\ud83d\udce1 {len(signals)} active signals extracted")
        save_signals(signals, response)
    else:
        print("\u274c Signal tracker failed")
        save_signals([], "Signal tracker failed this cycle.")

if __name__ == "__main__": main()
