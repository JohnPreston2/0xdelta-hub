# 0xDELTA — Autonomous Crypto Forensic Agent

> An autonomous AI agent that monitors Base chain tokens, computes 65+ forensic metrics every 2 hours, publishes a public intelligence dashboard, executes on-chain swaps, and gates premium reports behind an x402 micropayment — all without human intervention.

**Live dashboard** → https://johnpreston2.github.io/0xdelta-hub/  
**Hackathon track** → The Synthesis · Open Track + Base + Venice AI + Bankr  

---

## What it does

0xDELTA is a fully autonomous forensic intelligence agent running 24/7 on a GCP VPS. Every 2 hours, it:

1. Fetches on-chain data for 19 Base chain tokens (Moralis, GeckoTerminal)
2. Computes 65+ forensic metrics via `forensic_engine_v5.py`
3. Calls Venice AI (Gemini 3 Flash Preview) to synthesize a structured EN analysis — ranking tokens by CES score, detecting entry zones, whale movements, and phase transitions
4. Autonomously enters a new position: top-ranked token → swap 75% ETH via `bankr.sh` on-chain, stores trade state in `position.json` (auto-close at T+90min)
5. Pushes `memory.json` + `data.json` to GitHub Pages — public dashboard updates live
6. Posts alerts to Telegram + activity to Moltbook

Premium forensic sheets are gated behind an **x402 micropayment** ($0.02 USDC on Base) — the agent monetizes its own intelligence output directly on-chain.

---

## Problem it solves

**Agents that pay** — the core Synthesis theme.

Today, AI agents that move money operate in a black box:
- No transparent scope of what they can spend
- No verifiable proof that they spent correctly  
- No settlement without a middleman

0xDELTA demonstrates a different model: every action the agent takes is traceable. The forensic report explains *why* a position was entered. The x402 paywall is trustless — payment is verified on-chain before content is released. No API keys, no subscriptions, no backend auth.

---

## Architecture

```
Cron: every 2 hours — run_pipeline.sh
│
├── 0 · Check open position
│     position.json → if T+90min → sell via bankr.sh
│
├── 1 · collector.py
│     Fetch 19 tokens · Moralis + GeckoTerminal → raw data
│
├── 2 · report_builder.py
│     forensic_engine_v5.py → 65+ metrics → forensic_*.json
│
├── 3 · request_analysis.py
│     Load .md memory files + delta vs N-1
│     → Venice AI (Gemini 3 Flash Preview)
│     → CES ranking + entry zones + whale watch + EN narrative
│     → Telegram alerts + Moltbook post
│
├── 3b · enter_new_position
│     Token #1 from report → swap 75% ETH via bankr.sh
│     → position.json: OPEN / T+90min auto-close
│
├── 4 · export_memory_json.py v4
│     65 fields + forensic_report (.md) → memory.json
│
└── 5 · Push GitHub Pages
      push_to_github.py (data.json)
      push_memory_github.py (memory.json)
      → live at johnpreston2.github.io/0xdelta-hub
```

**Duration per cycle:** ~2–4 min · logged in `pipeline.log`

---

## Forensic Metrics

| Metric | Full Name | Description |
|--------|-----------|-------------|
| **FHS** | Forensic Health Score | Composite 0–10 score aggregating all signals |
| **NBP** | Net Buying Pressure | Buy/sell flow balance · EARLY_BREAKOUT override above threshold |
| **ICR** | Impact Crash Risk | Estimated price drop if top holder exits · >1.5 = critical |
| **LCR** | Liquidity Coverage Ratio | Pool liquidity vs market cap · danger below 30% |
| **BPI** | Breakout Potential Index | Multi-factor signal: volume surge + wallet accumulation + RSI divergence |
| **WCC** | Whale Concentration Coefficient | Gini-like supply concentration across top 20 wallets · >40% = rug risk |
| **DAI** | Distribution Accumulation Index | Detects accumulation vs distribution phases |

**Phase detection:** `EARLY_BREAKOUT` · `ACCUMULATION` · `DISTRIBUTION` · `DISTRIBUTION_LATE` · `PRE_CONSOLIDATION`

65+ metrics total including RSI, MACD, OHLCV analysis, wallet flow, liquidity depth, holder delta.

---

## x402 Paywall — Agents that pay

The dashboard is public. The forensic sheets are not.

```
User visits dashboard → clicks "Unlock Forensic Sheet"
→ MetaMask: switch to Base chain
→ Transfer $0.02 USDC (0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)
→ tx.wait() — on-chain verification
→ forensic_report unlocked from memory.json
→ sessionStorage: stays unlocked for the session
```

Full synthesis report (Venice AI narrative): $0.05 USDC via `report.html`.

No backend. No API key. No middleman. The content is already in `memory.json` — payment is the only gate.

---

## Stack

| Component | Tool |
|-----------|------|
| Agent runtime | OpenClaw · GCP VPS (`openclaw-agent` · 34.14.53.149) |
| LLM synthesis | Venice AI · Gemini 3 Flash Preview |
| On-chain data | Moralis · GeckoTerminal · DexScreener |
| Solana data | Helius API |
| On-chain execution | bankr.sh (Base chain swaps) |
| Paywall | x402 · USDC · Base |
| Frontend | GitHub Pages · `JohnPreston2/0xdelta-hub` |
| Alerts | Telegram · Moltbook |
| Memory | `.md` files per token · delta vs N-1 |

---

## Partner Tracks

- **Base** — all forensics, swaps, and x402 payments run on Base chain
- **Venice AI** — LLM synthesis engine for all forensic narratives
- **Bankr** — on-chain swap execution (`bankr.sh`) for autonomous position entry
- **Open Track** — "Agents that pay": trustless micropayment gating of AI-generated intelligence

---

## Live Links

- **Landing page** → https://johnpreston2.github.io/0xdelta-hub/landing.html
- **Dashboard** → https://johnpreston2.github.io/0xdelta-hub/index.html
- **Synthesis report** → https://johnpreston2.github.io/0xdelta-hub/report.html
- **GitHub repo** → https://github.com/JohnPreston2/0xdelta-hub

---

## Built by

John Preston · Marseille, France  
Pharmacy background → AI/crypto builder  
*First autonomous agent. First hackathon.*
