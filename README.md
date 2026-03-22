# 0xDELTA — Autonomous Crypto Forensic Agent

> **ERC-8004 Agent #32715** on Base chain. A fully autonomous AI agent that runs 24/7, analyzes 17 OpenClaw ecosystem tokens every 2 hours, computes 65+ forensic metrics, runs a hybrid privacy AI pipeline (Llama 3.3 70B private + Gemini 3 Flash anonymized via Venice AI), autonomously trades the top-ranked token via self-custody wallet, seals each report on-chain, and gates premium intelligence behind x402 micropayments — all without human intervention.

**Live dashboard** → https://johnpreston2.github.io/0xdelta-hub/
**Hackathon** → The Synthesis · **7 tracks**: Open Track, Let the Agent Cook, Bankr, Venice AI, Autonomous Trading Agent (Base), Agent Services on Base, Agents With Receipts (ERC-8004)

---

## What it does

0xDELTA is a fully autonomous forensic intelligence agent running 24/7 on a GCP VPS. Every 2 hours, an **8-step pipeline** executes:

1. **Check position** — if open > T+90min, auto-close via Bankr sell → ETH
2. **Venice billing check** — log remaining credits
3. **Collect data** — 17 Base chain tokens via Moralis + GeckoTerminal + DexScreener (OHLCV 1H + 15min)
4. **Forensic engine v5** — 65+ metrics per token, dual-timeframe RSI/SI (hourly + 15min), phase detection
5. **Signal tracker** — **Llama 3.3 70B** (private, no data retention) compares current vs N-1 cycle, detects momentum shifts
6. **Venice synthesis** — **Gemini 3 Flash Preview** (anonymized) generates CES ranking, entry zones, whale watch, full EN narrative
7. **Autonomous trade** — top CES token → RULE_BOOK filters (ICR, Top5, Phase, BPI, FHS) → swap 75% ETH via Bankr → 90min auto-close
8. **Publish** — push data.json, memory.json, signals.json, synthesis.json to GitHub Pages + Telegram alerts + Moltbook

**Report seal**: SHA256 hash of each synthesis report sent on-chain ($0.05 USDC to Forensic Wallet) — verifiable on Basescan.

Premium forensic sheets are gated behind **x402 micropayments** ($0.02 USDC dashboard, $0.05 USDC synthesis) — the agent monetizes its own intelligence output directly on-chain.

---

## Problem it solves

AI agents that trade autonomously give humans **no way to verify their decisions**:
- No transparent scope of what they can spend
- No verifiable proof that they spent correctly
- No settlement without a middleman

0xDELTA demonstrates a different model: **every action is traceable**. The forensic report explains *why* a position was entered. The report hash is sealed on-chain *before* any trade executes. The x402 paywall is trustless — payment verified on-chain, no backend. ERC-8004 provides verifiable agent identity.

---

## Architecture — 8-Step Pipeline

```
Cron: every 2 hours — run_pipeline.sh
│
├── 0   · check_position.py      → auto-close if T+90min via Bankr
├── 0b  · check_balance.py       → Venice AI billing check
│
├── 1   · collector.py            → 17 tokens · Moralis + GeckoTerminal (1H + 15min) + DexScreener
├── 2   · report_builder.py       → forensic_engine_v5 · 65+ metrics · dual-timeframe
│
├── 2b  · signal_tracker.py       → Llama 3.3 70B [PRIVATE] · momentum shifts · → signals.json
├── 3   · request_analysis.py     → Gemini 3 Flash [ANONYMIZED] · CES ranking · → synthesis.json
│                                   + seal_report_onchain() → $0.05 USDC to Forensic Wallet
│
├── 3b  · enter_new_position.py   → RULE_BOOK filters → swap 75% ETH via Bankr
├── 4   · export_memory_json.py   → 65 fields + forensic_report → memory.json
│
└── 5   · push_to_github.py       → data.json + memory.json + signals.json + synthesis.json
          push_memory_github.py     → GitHub Pages live update
```

**Hybrid privacy model** (validated by Venice team): Llama 3.3 70B runs in private mode (no data retention) for signal tracking. Gemini 3 Flash runs in anonymized mode for main synthesis. Neither model sees the other's output.

**Duration per cycle:** ~2–4 min · logged in `pipeline.log`

---

## Repo Structure

```
0xdelta-hub/
├── README.md
├── agent.json              # ERC-8004 agent manifest (machine-readable)
├── agent_log.json          # Structured execution logs (v2.0)
├── landing.html            # Project presentation + "How to Read the Dashboard" guide
├── index.html              # Live dashboard (x402 gated, $0.02)
├── report.html             # Global synthesis report (x402 gated, $0.05) + Signal Tracker
├── memory.json             # Live forensic data — updated every 2h
├── data.json               # Trending data feed
├── signals.json            # Llama 70B signal tracking output
├── synthesis.json          # Venice AI synthesis + report seal hash
└── src/
    ├── collector.py            # Step 1 — 17 tokens · OHLCV 1H + 15min
    ├── report_builder.py       # Step 2 — runs forensic_engine_v5
    ├── forensic_engine_v5.py   # Core — 65+ metrics, dual-timeframe RSI/SI/BPI
    ├── signal_tracker.py       # Step 2b — Llama 3.3 70B private inference
    ├── request_analysis.py     # Step 3 — Gemini 3 Flash synthesis + on-chain seal
    ├── enter_new_position.py   # Step 3b — 5-level parser + RULE_BOOK + Bankr swap
    ├── check_position.py       # Step 0 — auto-close at T+90min
    ├── check_balance.py        # Step 0b — Venice billing
    ├── export_memory_json.py   # Step 4 — bundle forensic data
    ├── push_to_github.py       # Step 5 — push data + signals + synthesis
    ├── push_memory_github.py   # Step 5 — push memory.json
    └── run_pipeline.sh         # Cron entrypoint — orchestrates all 8 steps
```

---

## Forensic Metrics (65+)

### Core Metrics
| Metric | Full Name | Description |
|--------|-----------|-------------|
| **FHS** | Forensic Health Score | Composite 0–10 aggregating all signals |
| **NBP** | Net Buying Pressure | Buy/sell flow balance · detects accumulation vs distribution |
| **ICR** | Impact Crash Risk | Price drop if top holder exits · >1.5 = critical |
| **LCR** | Liquidity Coverage Ratio | Pool liquidity vs FDV · <2% = fragile |
| **BPI** | Breakout Potential Index | Volume surge + wallet accumulation + RSI divergence + Bollinger squeeze |
| **WCC** | Whale Concentration | Gini-like supply concentration · >40% = rug risk |

### Deep Forensic Signals
| Metric | Full Name | Description |
|--------|-----------|-------------|
| **SI** | Squeeze Intensity | Bollinger compression, dual-timeframe (1H + 15min) |
| **TCI** | Team Concentration Index | Contract ratio + entity clustering + address prefix + balance tiers |
| **FCI** | Flow Concentration Index | Unknown whale concentration + balance clustering |

### Trading Rules (RULE_BOOK)
- ICR < 10, Top5 < 50%, Phase ≠ DISTRIBUTION, BPI > 1.5, FHS > 6.0, Price change < 25%/24h
- Auto-close at T+90min via check_position.py

**Phase detection:** `EARLY_BREAKOUT` · `ACCUMULATION` · `DISTRIBUTION` · `CONSOLIDATION` · `RUPTURE`

---

## On-Chain Artifacts

| Artifact | Details |
|----------|---------|
| **ERC-8004 Registration** | Agent #32715 on Base · [TX](https://basescan.org/tx/0xd79072ca8c98f1ae8d4eced124e3cd43b02df6e85aff688c868ad9f5923843db) |
| **Report Seal** | SHA256 hash → $0.05 USDC to Forensic Wallet every cycle · [Example TX](https://basescan.org/tx/0x5d9a4413feb347d1f5c57b15b55e2bbadc5b408a9bfe556f806eaeb7b11a193a) |
| **Trading Wallet** | Self-custody via Bankr · `0x0ab463a9427fee78f2a3724e84114b79ff9697f7` |
| **Forensic Wallet** | Report seal receiver · `0xEb18a33e8F9517EC1D2888267540029e126a3054` |
| **x402 Receiver** | Dashboard/synthesis payments · `0x71fd4359eB2da83C1BCd34f93a1C206d68b1eFba` |
| **agent.json** | Published on GitHub Pages · machine-readable identity + capabilities |
| **agent_log.json** | Structured execution logs v2.0 — decisions, errors, tool interactions |

---

## x402 Paywall — Agent Services on Base

The dashboard shows FHS scores for free. Full forensic sheets are gated:

| Service | Price | Content |
|---------|-------|---------|
| **Token Dashboard** | $0.02 USDC | 65+ metrics, ICR breakdown, wallet flows, bull flag/Fibonacci, AI narrative |
| **Global Synthesis** | $0.05 USDC | CES ranking, Top 3 opportunities, whale watch, phase transitions, trade recommendation |

No backend. No API key. No middleman. Payment verified on-chain via MetaMask → USDC transfer on Base.

---

## Stack

| Component | Tool |
|-----------|------|
| Agent runtime | OpenClaw · GCP VPS |
| LLM — private | Venice AI · **Llama 3.3 70B** (no data retention) |
| LLM — synthesis | Venice AI · **Gemini 3 Flash Preview** (anonymized) |
| On-chain data | Moralis · GeckoTerminal · DexScreener |
| On-chain execution | Bankr (self-custody, Base DEX swaps) |
| On-chain identity | ERC-8004 Agent #32715 |
| Report seal | SHA256 → $0.05 USDC on-chain every cycle |
| Paywall | x402 · USDC · Base |
| Frontend | GitHub Pages |
| Alerts | Telegram · Moltbook |
| Memory | PROFILE.md / PROJECTS.md / DECISIONS.md / ERRORS.md |

---

## Hackathon Tracks (7)

| Track | Sponsor | Relevance |
|-------|---------|-----------|
| **Synthesis Open Track** | Community | Full autonomous agent with on-chain artifacts |
| **Let the Agent Cook** | Protocol Labs | 8-step pipeline, zero human intervention |
| **Best Bankr LLM Gateway** | Bankr | Self-custody trading + swap execution |
| **Private Agents, Trusted Actions** | Venice AI | Hybrid privacy: Llama 70B private + Gemini Flash anonymized |
| **Autonomous Trading Agent** | Base | Forensic-driven autonomous trading, 90min positions |
| **Agent Services on Base** | Base | x402 discoverable agent service, forensic intelligence |
| **Agents With Receipts — ERC-8004** | Protocol Labs | On-chain identity, report seal, verifiable agent actions |

---

## Live Links

- **Landing page** → https://johnpreston2.github.io/0xdelta-hub/landing.html
- **Dashboard** → https://johnpreston2.github.io/0xdelta-hub/index.html
- **Synthesis report** → https://johnpreston2.github.io/0xdelta-hub/report.html
- **GitHub repo** → https://github.com/JohnPreston2/0xdelta-hub
- **Moltbook** → https://www.moltbook.com/post/91bda51a-888c-4a16-b09f-8739610a9614
- **Devfolio** → https://synthesis.devfolio.co/projects/0xdelta-autonomous-forensic-intelligence-agent-29f3

---

## Built by

John Preston · Marseille, France
Pharmacy background → AI/crypto builder
*First autonomous agent. First hackathon. Built solo in 10 days.*
