#!/usr/bin/env python3
"""
enter_new_position.py — Step 3b du pipeline
Parse la ligne INJECTION PRIORITAIRE du rapport Gemini.
Fallback: parse TOP 3 OPPORTUNITIES si INJECTION absente.
Verifie les filtres RULE_BOOK (ICR, Top5, Phase, NBP).
Execute le trade via bankr.sh si les conditions sont reunies.
Ecrit position.json SEULEMENT apres confirmation trade.
"""
import json, os, re, subprocess, time, sys
from datetime import datetime, timezone

POSITION_FILE  = "/home/classics2323/.openclaw/workspace/mind/position.json"
BANKR_SCRIPT   = "/home/classics2323/.openclaw/workspace/skills/bankr/scripts/bankr.sh"
SYNTHESIS_FILE = "/tmp/0xdelta-hub/synthesis.json"
FORENSIC_DIR   = "/home/classics2323/crypto-monitor/data/processed"
ANALYSIS_LOG   = "/home/classics2323/crypto-monitor/last_analysis.txt"

# Regles de trading actives
TRADE_SIZE_PCT = 75   # 75% du capital ETH disponible
MAX_ICR        = 10.0
MAX_TOP5       = 50.0
MIN_BPI_TIER2  = 1.5
MIN_FHS        = 6.0
BLOCKED_PHASES = ["DISTRIBUTION", "DIST"]

def load_position():
    if not os.path.exists(POSITION_FILE):
        return None
    with open(POSITION_FILE) as f:
        return json.load(f)

def save_position(data):
    with open(POSITION_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_position_open():
    pos = load_position()
    return pos and pos.get("status") == "OPEN"

def parse_injection_from_analysis(text):
    """
    Parse le ticker cible depuis le rapport Venice AI.
    Strategie multi-fallback:
      1. INJECTION PRIORITAIRE : $SYMBOL (n'importe ou dans le texte)
      2. TOP 3 OPPORTUNITIES -> premier token bold **SYMBOL**
      3. Pattern CES ranking: SYMBOL - CES: XX/100
      4. Fallback #1 / TOP 1 / Rank 1
    """
    # 1. Pattern principal — INJECTION PRIORITAIRE n'importe ou
    pattern = r'INJECTION\s+PRIORITAIRE\s*[:\-]\s*\$([A-Z0-9]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        print(f"[ENTER] Parsed via INJECTION PRIORITAIRE: {match.group(1)}")
        return match.group(1).upper()

    # 2. Premier token bold dans TOP 3 OPPORTUNITIES
    #    Format: **BUNKER** - CES: 72/100
    pattern2 = r'\*\*([A-Z0-9]{2,12})\*\*\s*[-\u2013]\s*CES'
    match = re.search(pattern2, text)
    if match:
        print(f"[ENTER] Parsed via TOP 3 bold pattern: {match.group(1)}")
        return match.group(1).upper()

    # 3. Pattern CES ranking sans bold
    #    Format: BUNKER - CES: 72/100  or  1. BUNKER (CES 72)
    pattern3 = r'(?:^|\n)\s*(?:\d+\.?\s*)?([A-Z][A-Z0-9]{1,11})\s*[-\u2013(]\s*CES'
    match = re.search(pattern3, text)
    if match:
        print(f"[ENTER] Parsed via CES ranking pattern: {match.group(1)}")
        return match.group(1).upper()

    # 4. Fallback : #1 ou TOP 1
    fallback = r'(?:TOP\s*1|#1|Rank\s*1)[^\n]*\$([A-Z0-9]+)'
    match = re.search(fallback, text, re.IGNORECASE)
    if match:
        print(f"[ENTER] Parsed via fallback #1/TOP1: {match.group(1)}")
        return match.group(1).upper()

    # 5. Dernier recours: premier $SYMBOL dans le texte
    last_resort = r'\$([A-Z][A-Z0-9]{1,11})'
    match = re.search(last_resort, text)
    if match:
        print(f"[ENTER] Parsed via last resort $SYMBOL: {match.group(1)}")
        return match.group(1).upper()

    return None

def get_token_data(symbol):
    """
    Recupere les donnees forensic du token depuis le dernier rapport JSON.
    """
    try:
        files = sorted([f for f in os.listdir(FORENSIC_DIR) if f.startswith("forensic_")])
        if not files:
            return None, None
        with open(os.path.join(FORENSIC_DIR, files[-1])) as f:
            data = json.load(f)
        tokens = data.get("tokens", {})
        for addr, t in tokens.items():
            if t.get("symbol", "").upper() == symbol.upper():
                return t, addr
    except Exception as e:
        print(f"[ENTER] Erreur lecture forensic: {e}")
    return None, None

def check_filters(symbol, token_data):
    """
    Verifie les filtres bloquants du RULE_BOOK.
    Retourne (ok, raison_blocage)
    """
    if not token_data:
        return False, "Donnees forensic introuvables"

    conv     = token_data.get("convergence", {})
    forensic = token_data.get("forensic", {})
    flows    = token_data.get("flows", {})

    icr     = token_data.get("liquidity", {}).get("icr", 0)
    top5    = forensic.get("top5_pct", 0)
    phase   = conv.get("phase", "")
    nbp     = flows.get("nbp", 0)
    fhs     = conv.get("fhs", 0)
    bpi     = token_data.get("bull_flag", {}).get("bpi", 0)

    print(f"[ENTER] Filters {symbol}: ICR={icr} Top5={top5}% Phase={phase} NBP={nbp}% FHS={fhs} BPI={bpi}")

    # Bloquants absolus
    if icr > MAX_ICR:
        return False, f"ICR {icr} > {MAX_ICR} (blocking)"

    if top5 > MAX_TOP5:
        return False, f"Top5 {top5}% > {MAX_TOP5}% (excessive concentration)"

    for blocked in BLOCKED_PHASES:
        if blocked.upper() in phase.upper():
            return False, f"Phase {phase} = DISTRIBUTION (blocking)"

    if nbp < -80:
        return False, f"NBP {nbp}% < -80% (insurmountable sell wall)"

    if fhs < MIN_FHS:
        return False, f"FHS {fhs} < {MIN_FHS} (insufficient structure)"

    if bpi < MIN_BPI_TIER2:
        return False, f"BPI {bpi} < {MIN_BPI_TIER2} (signal too weak)"

    # Price > +25% in 24h = overheat
    price_chg = token_data.get("raw_metrics", {}).get("price_change_24h", 0)
    if price_chg > 25:
        return False, f"Price +{price_chg}% in 24h (overheat)"

    return True, "OK"

def execute_trade(symbol, address):
    """
    Execute le swap via bankr.sh — achete avec ETH.
    """
    prompt = f"Swap {TRADE_SIZE_PCT}% of my ETH balance for {symbol} on Base. Token contract: {address}. Use market order."
    print(f"[ENTER] Prompt bankr: {prompt}")

    try:
        result = subprocess.run(
            [BANKR_SCRIPT, prompt],
            capture_output=True, text=True, timeout=360
        )
        print(f"[ENTER] Bankr stdout: {result.stdout[-800:]}")

        if result.returncode == 0:
            tx_hash = ""
            # Extraire tx depuis basescan link
            match = re.search(r'basescan\.org/tx/(0x[a-fA-F0-9]+)', result.stdout)
            if match:
                tx_hash = match.group(1)
            else:
                # Cherche dans le JSON response
                try:
                    resp = json.loads(result.stdout.strip().split("\n")[-1])
                    response_text = resp.get("response", "")
                    match = re.search(r'basescan\.org/tx/(0x[a-fA-F0-9]+)', response_text)
                    if match:
                        tx_hash = match.group(1)
                    else:
                        match = re.search(r'0x[a-fA-F0-9]{64}', response_text)
                        if match:
                            tx_hash = match.group(0)
                except:
                    pass

            # Verifier que le trade a reellement eu lieu
            if not tx_hash:
                print(f"[ENTER] Warning: no TX hash found — trade may have failed")
                if "insufficient" in result.stdout.lower() or "failed" in result.stdout.lower():
                    return False, "Trade failed — insufficient balance or error"

            return True, tx_hash
        else:
            return False, result.stderr[:200]

    except subprocess.TimeoutExpired:
        return False, "Timeout bankr (>6min)"
    except Exception as e:
        return False, str(e)

def main():
    print(f"[ENTER] === enter_new_position.py — {datetime.now().isoformat()} ===")

    # Verifier si position deja ouverte
    if is_position_open():
        pos = load_position()
        print(f"[ENTER] Position already OPEN: {pos.get('symbol')} — skipping")
        return

    # Lire le dernier rapport d'analyse
    analysis_text = ""
    if os.path.exists(ANALYSIS_LOG):
        with open(ANALYSIS_LOG) as f:
            analysis_text = f.read()
    else:
        # Essayer synthesis.json
        if os.path.exists(SYNTHESIS_FILE):
            with open(SYNTHESIS_FILE) as f:
                synth = json.load(f)
            analysis_text = synth.get("raw_report", "")
            if not analysis_text:
                # Construire depuis top_opportunities
                opps = synth.get("top_opportunities", [])
                if opps:
                    analysis_text = f"INJECTION PRIORITAIRE : ${opps[0]['symbol']}"

    if not analysis_text:
        print("[ENTER] No analysis report found — skip")
        return

    # Parser le ticker
    symbol = parse_injection_from_analysis(analysis_text)
    if not symbol:
        print("[ENTER] Could not parse target token from report — skip")
        print(f"[ENTER] Report start: {analysis_text[:300]}")
        return

    print(f"[ENTER] Target token: {symbol}")

    # Recuperer donnees forensic
    token_data, address = get_token_data(symbol)
    if not address:
        print(f"[ENTER] Token {symbol} not found in forensic data")
        return

    # Verifier les filtres
    ok, reason = check_filters(symbol, token_data)
    if not ok:
        print(f"[ENTER] Trade blocked — {reason}")
        return

    print(f"[ENTER] Filters passed — executing trade {symbol}")

    # Executer le trade — position.json ecrit SEULEMENT apres confirmation
    success, tx_info = execute_trade(symbol, address)

    if success:
        pos = {
            "symbol":     symbol,
            "address":    address,
            "entry_time": int(time.time()),
            "status":     "OPEN",
            "tx_hash":    tx_info,
            "trade_size_pct": TRADE_SIZE_PCT,
        }
        save_position(pos)
        print(f"[ENTER] Position opened: {symbol} | TX: {tx_info}")
    else:
        print(f"[ENTER] Trade failed: {tx_info}")

if __name__ == "__main__":
    main()
