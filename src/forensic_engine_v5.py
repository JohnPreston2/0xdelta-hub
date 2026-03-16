"""
🔬 OpenClaw Forensic Engine V5 - FIXED
========================================
Version corrigée pour parser correctement les JSON de:
- DexScreener (pool data)
- Moralis (holders)
- GeckoTerminal (OHLCV)

Corrections appliquées:
- Chemins pool: pool.liquidity.usd, pool.priceUsd, pool.volume.h24
- Chemins holders: holders[] array direct, usd_value au lieu de balance_usd
- Chemins OHLCV: array de arrays [timestamp, o, h, l, c, volume]
- Symbol: pool.baseToken.symbol

Usage:
  from forensic_engine_v5_fixed import ForensicEngineV5
  engine = ForensicEngineV5()
  report = engine.analyze(collector_json)
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import Counter


# ════════════════════════════════════════════════════════
# DATA CLASSES
# ════════════════════════════════════════════════════════

@dataclass
class LiquidityAudit:
    """Étape 1: Audit de Liquidité & Stress Test"""
    crash_threshold_usd: float = 0.0
    icr: float = 0.0
    icr_alert: bool = False
    lcr: float = 0.0
    lcr_fragile: bool = False
    lvr: float = 0.0
    lvr_status: str = "unknown"
    dai: float = 0.0
    dai_status: str = "balanced"
    ips_10k: float = 0.0
    ips_50k: float = 0.0
    ips_100k: float = 0.0


@dataclass
class FlowAnalysis:
    """Étape 2: Détection des Flux & VPA"""
    nbp: float = 0.0
    nbp_status: str = "neutral"
    ev: float = 0.0
    ev_trend: str = "stable"
    ac: float = 0.0
    ac_above_median: bool = False
    vwad: float = 0.0
    flow_classification: str = "NEUTRAL"


@dataclass
class BullFlagAnalysis:
    """Étape 3: Bull Flags & Fibonacci"""
    detected: bool = False
    retracement_pct: float = 0.0
    flag_class: int = 0
    fqs: float = 0.0
    fqs_label: str = "N/A"
    bpi: float = 0.0
    bpi_label: str = "N/A"
    fib_target_1618: float = 0.0
    fib_upside_pct: float = 0.0
    pole_high: float = 0.0
    pole_low: float = 0.0
    squeeze_factor: float = 1.0


@dataclass
class TechnicalAnalysis:
    """Étape 4: RSI & Bollinger"""
    rmd: float = 0.0
    rmd_divergence: str = "none"
    ber: float = 0.5
    ber_zone: str = "equilibrium"
    si: float = 0.0
    si_status: str = "normal"
    saturated: bool = False
    rsi_1h: float = 0.0
    rsi_1d: float = 0.0


@dataclass
class ForensicCluster:
    """Étape 5: Cluster & Forensic Avancé"""
    wcc: float = 0.0
    wcc_alert: bool = False
    tci: float = 0.0
    tci_alert: bool = False
    scr: float = 0.0
    scr_centralized: bool = False
    fci: float = 0.0
    fci_alert: bool = False
    top5_pct: float = 0.0
    top10_pct: float = 0.0
    top20_pct: float = 0.0


@dataclass
class ConvergenceScore:
    """Étape 6: Score de Convergence Global"""
    fhs: float = 0.0
    fhs_label: str = "unknown"
    cp: float = 0.0
    phase: str = "UNKNOWN"


@dataclass
class ForensicReportV5:
    """Rapport complet V5"""
    token_address: str = ""
    symbol: str = ""
    chain: str = "base"
    
    # Sub-reports
    liquidity: LiquidityAudit = field(default_factory=LiquidityAudit)
    flows: FlowAnalysis = field(default_factory=FlowAnalysis)
    bull_flag: BullFlagAnalysis = field(default_factory=BullFlagAnalysis)
    technical: TechnicalAnalysis = field(default_factory=TechnicalAnalysis)
    forensic: ForensicCluster = field(default_factory=ForensicCluster)
    convergence: ConvergenceScore = field(default_factory=ConvergenceScore)
    
    # Alerts
    alerts: List[Dict] = field(default_factory=list)
    
    # Narrative
    narrative_phase: str = ""
    narrative_insight: str = ""
    narrative_structure: str = ""
    
    # Surveillance
    support_key: float = 0.0
    resistance_key: float = 0.0
    
    # Raw metrics for debug
    raw_metrics: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ════════════════════════════════════════════════════════
# ENGINE
# ════════════════════════════════════════════════════════

class ForensicEngineV5:
    """
    Moteur de calcul forensic V5 - VERSION CORRIGÉE.
    Compatible avec format DexScreener + Moralis + GeckoTerminal.
    """

    def analyze(self, data: Dict[str, Any]) -> ForensicReportV5:
        """Point d'entrée principal."""
        report = ForensicReportV5()
        
        # ────────────────────────────────────────────
        # EXTRACTION DES DONNÉES (CHEMINS CORRIGÉS)
        # ────────────────────────────────────────────
        
        # Token address
        report.token_address = data.get("token_address", "")
        report.chain = data.get("chain", "base")
        
        # Pool data (format DexScreener)
        pool = data.get("pool", {})
        
        # Symbol - CORRIGÉ: pool.baseToken.symbol
        base_token = pool.get("baseToken", {})
        report.symbol = base_token.get("symbol", "") or pool.get("symbol", "UNKNOWN")
        
        # Price - CORRIGÉ: pool.priceUsd (string)
        price = self._f(pool.get("priceUsd", 0))
        
        # Liquidity - CORRIGÉ: pool.liquidity.usd
        liquidity_data = pool.get("liquidity", {})
        if isinstance(liquidity_data, dict):
            liquidity = self._f(liquidity_data.get("usd", 0))
        else:
            liquidity = self._f(liquidity_data)
        
        # Volume - CORRIGÉ: pool.volume.h24
        volume_data = pool.get("volume", {})
        if isinstance(volume_data, dict):
            volume_24h = self._f(volume_data.get("h24", 0))
        else:
            volume_24h = self._f(volume_data)
        
        # FDV & Market Cap
        fdv = self._f(pool.get("fdv", 0))
        mcap = self._f(pool.get("marketCap", 0)) or fdv
        
        # Transactions - CORRIGÉ: pool.txns.h24.buys/sells
        txns = pool.get("txns", {})
        txns_24h = txns.get("h24", {})
        buys = self._f(txns_24h.get("buys", 0))
        sells = self._f(txns_24h.get("sells", 0))
        
        # Price change - CORRIGÉ: pool.priceChange.h24
        price_change_data = pool.get("priceChange", {})
        price_change_24h = self._f(price_change_data.get("h24", 0))
        
        # Holders - CORRIGÉ: holders est un array direct, pas un dict
        holders_raw = data.get("holders", [])
        if isinstance(holders_raw, dict):
            holders_list = holders_raw.get("list", []) or holders_raw.get("top_holders", [])
        else:
            holders_list = holders_raw if isinstance(holders_raw, list) else []
        
        # Extract balances USD - CORRIGÉ: usd_value au lieu de balance_usd
        top5_balances = self._extract_top_balances(holders_list, 5)
        top10_balances = self._extract_top_balances(holders_list, 10)
        top20_balances = self._extract_top_balances(holders_list, 20)
        
        # Total supply from holders percentages
        total_supply_pct = sum(self._f(h.get("percentage_relative_to_total_supply", 0)) for h in holders_list[:20])
        total_supply_usd = sum(top20_balances)
        
        # Holder count
        holder_count = len(holders_list)
        
        # OHLCV - CORRIGÉ: array de arrays [timestamp, o, h, l, c, volume]
        ohlcv = data.get("ohlcv", [])
        
        # Indicators (peut être vide, on calcule depuis OHLCV)
        indicators = data.get("indicators", {})
        
        # RSI from indicators or calculate
        rsi_1h = self._f(indicators.get("rsi_1h")) if indicators.get("rsi_1h") else None
        rsi_1d = self._f(indicators.get("rsi_1d")) if indicators.get("rsi_1d") else None
        
        # Bollinger from indicators
        bb = indicators.get("bollinger_1h") or indicators.get("bb_1h", {})
        
        # Si pas d'indicateurs, calculer depuis OHLCV
        if ohlcv and not rsi_1h:
            rsi_1h = self._calc_rsi_from_ohlcv(ohlcv, 14)
        
        if ohlcv and not bb:
            bb = self._calc_bollinger_from_ohlcv(ohlcv, 20)
        
        # Store raw metrics for debug
        report.raw_metrics = {
            "price": price,
            "liquidity": liquidity,
            "volume_24h": volume_24h,
            "fdv": fdv,
            "mcap": mcap,
            "buys": buys,
            "sells": sells,
            "price_change_24h": price_change_24h,
            "holder_count": holder_count,
            "top5_sum_usd": sum(top5_balances),
            "ohlcv_count": len(ohlcv),
            "rsi_1h": rsi_1h
        }
        
        # ────────────────────────────────────────────
        # ÉTAPE 1: Audit de Liquidité
        # ────────────────────────────────────────────
        liq = report.liquidity
        
        # Seuil de rupture (crash 30%)
        if liquidity > 0:
            liq.crash_threshold_usd = (0.3 / 0.7) * (liquidity / 2)
        
        # ICR - Index de Concentration Relative
        sum_top5 = sum(top5_balances)
        if liq.crash_threshold_usd > 0:
            liq.icr = sum_top5 / liq.crash_threshold_usd
        liq.icr_alert = liq.icr > 1.0
        
        # LCR - Liquidity Coverage Ratio
        if fdv > 0:
            liq.lcr = (liquidity / fdv) * 100
        liq.lcr_fragile = liq.lcr < 2.0
        
        # LVR - Liquidity Velocity Ratio
        if liquidity > 0:
            liq.lvr = volume_24h / liquidity
        if liq.lvr > 10:
            liq.lvr_status = "alert"
        elif liq.lvr < 0.1:
            liq.lvr_status = "dead"
        elif liq.lvr < 1:
            liq.lvr_status = "suspicious"
        elif 2 <= liq.lvr <= 5:
            liq.lvr_status = "optimal"
        else:
            liq.lvr_status = "acceptable"
        
        # DAI - Depth Asymmetry Index (from buy/sell counts)
        total_txns = buys + sells
        if total_txns > 0:
            liq.dai = (buys - sells) / total_txns
        if liq.dai > 0.3:
            liq.dai_status = "buy_wall"
        elif liq.dai < -0.3:
            liq.dai_status = "sell_wall"
        else:
            liq.dai_status = "balanced"
        
        # IPS - Impact Price Slippage
        if liquidity > 0:
            liq.ips_10k = self._estimate_slippage(10_000, liquidity)
            liq.ips_50k = self._estimate_slippage(50_000, liquidity)
            liq.ips_100k = self._estimate_slippage(100_000, liquidity)
        
        # ────────────────────────────────────────────
        # ÉTAPE 2: Flux & VPA
        # ────────────────────────────────────────────
        fl = report.flows
        
        # NBP - Net Buyer Pressure (from transaction counts)
        if total_txns > 0:
            fl.nbp = ((buys - sells) / total_txns) * 100
        
        if fl.nbp > 15:
            fl.nbp_status = "accumulation"
        elif fl.nbp < -15:
            fl.nbp_status = "distribution"
        else:
            fl.nbp_status = "neutral"
        
        # EV - Volume Efficiency
        if volume_24h > 0:
            fl.ev = (abs(price_change_24h) / volume_24h) * 1_000_000
        
        # AC - Absorption Coefficient
        if abs(price_change_24h) > 0.01:
            fl.ac = volume_24h / abs(price_change_24h)
        
        # Flow classification
        if fl.nbp > 10 and abs(price_change_24h) < 5:
            fl.flow_classification = "ACCUMULATION"
        elif fl.nbp < -10:
            fl.flow_classification = "DISTRIBUTION"
        elif volume_24h > 0 and abs(price_change_24h) < 2:
            fl.flow_classification = "CHURNING"
        else:
            fl.flow_classification = "NEUTRAL"
        
        # ────────────────────────────────────────────
        # ÉTAPE 3: Bull Flags & Fibonacci
        # ────────────────────────────────────────────
        bf = report.bull_flag
        
        if len(ohlcv) >= 10:
            pole_high, pole_low, current = self._detect_bull_flag_from_ohlcv(ohlcv, price)
            
            if pole_high > pole_low > 0 and current > 0:
                pole_range = pole_high - pole_low
                retracement = ((pole_high - current) / pole_range) * 100 if pole_range > 0 else 100
                
                if 0 < retracement < 66:
                    bf.detected = True
                    bf.retracement_pct = round(retracement, 1)
                    bf.pole_high = pole_high
                    bf.pole_low = pole_low
                    
                    # Flag class
                    if retracement <= 38.2:
                        bf.flag_class = 1
                    elif retracement <= 50:
                        bf.flag_class = 2
                    else:
                        bf.flag_class = 3
                    
                    # FQS - Flag Quality Score
                    vol_pole = self._sum_ohlcv_volume(ohlcv[:len(ohlcv)//2])
                    vol_flag = self._sum_ohlcv_volume(ohlcv[len(ohlcv)//2:]) or 1
                    rsi_bonus = 0.1 if (rsi_1h and rsi_1h < 40) else 0
                    bf.fqs = (100 - retracement) * (vol_pole / vol_flag) * (1 + rsi_bonus)
                    
                    if bf.fqs > 150:
                        bf.fqs_label = "Premium"
                    elif bf.fqs > 100:
                        bf.fqs_label = "Standard"
                    else:
                        bf.fqs_label = "Fragile"
                    
                    # BPI - Breakout Probability Index
                    current_vol = self._get_last_volume(ohlcv)
                    avg_flag_vol = vol_flag / max(len(ohlcv) // 2, 1)
                    
                    bf.squeeze_factor = 1.0
                    if bb and bb.get("bandwidth"):
                        bw_current = self._f(bb.get("bandwidth", 0))
                        bw_max = self._f(bb.get("bandwidth_max", bw_current * 2))
                        if bw_max > 0:
                            bf.squeeze_factor = 1 + (1 - bw_current / bw_max)
                    
                    if avg_flag_vol > 0:
                        bf.bpi = (current_vol / avg_flag_vol) * (1 - retracement / 100) * bf.squeeze_factor
                    
                    if bf.bpi > 2:
                        bf.bpi_label = "Breakout probable"
                    elif bf.bpi > 1:
                        bf.bpi_label = "Incertain"
                    else:
                        bf.bpi_label = "Improbable"
                    
                    # Fibonacci 1.618 target
                    bf.fib_target_1618 = pole_low + 1.618 * pole_range
                    if current > 0:
                        bf.fib_upside_pct = ((bf.fib_target_1618 - current) / current) * 100
        
        # ────────────────────────────────────────────
        # ÉTAPE 4: RSI & Bollinger
        # ────────────────────────────────────────────
        ta = report.technical
        ta.rsi_1h = rsi_1h or 0
        ta.rsi_1d = rsi_1d or 0
        
        # RMD - RSI Momentum Divergence
        if rsi_1h and price_change_24h != 0:
            rsi_slope = (rsi_1h - 50) / 10
            price_slope = price_change_24h / 10
            ta.rmd = rsi_slope - price_slope
            if ta.rmd < -5:
                ta.rmd_divergence = "bearish_hidden"
            elif ta.rmd > 5:
                ta.rmd_divergence = "bullish_hidden"
        
        # BER - Bollinger Efficiency Ratio
        upper = self._f(bb.get("upper", 0))
        lower = self._f(bb.get("lower", 0))
        middle = self._f(bb.get("middle", 0))
        
        if upper > lower and price > 0:
            ta.ber = (price - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
            if ta.ber > 0.9:
                ta.ber_zone = "overbought"
            elif ta.ber < 0.1:
                ta.ber_zone = "oversold"
        
        # SI - Squeeze Intensity
        if middle > 0:
            bw_current = ((upper - lower) / middle) * 100 if middle > 0 else 0
            bw_max = self._f(bb.get("bandwidth_max", bw_current * 1.5))
            if bw_max > 0:
                ta.si = max(0, ((bw_max - bw_current) / bw_max) * 100)
                if ta.si > 80:
                    ta.si_status = "extreme_compression"
                elif ta.si < 30:
                    ta.si_status = "active_expansion"
        
        # Saturation
        ta.saturated = (rsi_1h is not None and rsi_1h > 75 and ta.ber > 0.9)
        
        # ────────────────────────────────────────────
        # ÉTAPE 5: Cluster & Forensic
        # ────────────────────────────────────────────
        fc = report.forensic
        
        # Calculate holder concentration percentages
        if holders_list:
            fc.top5_pct = sum(self._f(h.get("percentage_relative_to_total_supply", 0)) for h in holders_list[:5])
            fc.top10_pct = sum(self._f(h.get("percentage_relative_to_total_supply", 0)) for h in holders_list[:10])
            fc.top20_pct = sum(self._f(h.get("percentage_relative_to_total_supply", 0)) for h in holders_list[:20])
        
        # TCI - Temporal Concentration Index
        fc.tci = self._calc_tci(holders_list)
        fc.tci_alert = fc.tci > 30
        
        # FCI - Funding Correlation Index
        fc.fci = self._calc_fci(holders_list)
        fc.fci_alert = fc.fci > 60
        
        # WCC - Wallet Clustering Coefficient
        fc.wcc = self._calc_wcc(holders_list)
        fc.wcc_alert = fc.wcc > 20
        
        # SCR - Supply Control Ratio
        fc.scr = fc.top5_pct
        if fc.wcc_alert:
            fc.scr = fc.scr * 1.3  # Adjust for linked wallets
        fc.scr_centralized = fc.scr > 40
        
        # ────────────────────────────────────────────
        # ÉTAPE 6: Convergence
        # ────────────────────────────────────────────
        conv = report.convergence
        
        # Normalize components to 0-1
        icr_norm = min(liq.icr / 3.0, 1.0) if liq.icr > 0 else 0
        ev_norm = min(fl.ev / 10.0, 1.0) if fl.ev > 0 else 0
        fqs_norm = min(bf.fqs / 200.0, 1.0) if bf.fqs > 0 else 0.5
        wcc_pct = fc.wcc / 100.0
        lcr_norm = min(liq.lcr / 10.0, 1.0) if liq.lcr > 0 else 0
        bpi_norm = min(bf.bpi / 3.0, 1.0) if bf.bpi > 0 else 0.5
        
        # FHS - Forensic Health Score (/10)
        fhs_raw = (
            (1 - icr_norm) * 0.25 +
            ev_norm * 0.20 +
            fqs_norm * 0.20 +
            (1 - wcc_pct) * 0.15 +
            lcr_norm * 0.10 +
            bpi_norm * 0.10
        )
        conv.fhs = round(fhs_raw * 10, 1)
        
        if conv.fhs > 7:
            conv.fhs_label = "solid"
        elif conv.fhs > 4:
            conv.fhs_label = "moderate"
        else:
            conv.fhs_label = "critical"
        
        # CP - Continuation Probability
        cp_raw = (fqs_norm + bpi_norm + (fl.nbp / 100.0 + 0.5)) / 3.0 * 100
        if rsi_1h and rsi_1h < 70 and ta.si > 60:
            cp_raw += 15
        if liq.icr > 1.5:
            cp_raw -= 20
        conv.cp = round(max(0, min(100, cp_raw)), 1)
        
        # Phase determination
        if fl.flow_classification == "ACCUMULATION":
            conv.phase = "ACCUMULATION"
        elif fl.flow_classification == "DISTRIBUTION":
            conv.phase = "DISTRIBUTION"
        elif fl.flow_classification == "CHURNING":
            conv.phase = "DISTRIBUTION_POTENTIELLE"
        elif bf.detected and bf.bpi > 1.5:
            conv.phase = "RUPTURE"
        else:
            conv.phase = "CONSOLIDATION"
        
        # ────────────────────────────────────────────
        # ALERTS
        # ────────────────────────────────────────────
        alerts = []
        
        if liq.icr > 1.5:
            alerts.append({
                "severity": "critical",
                "code": "ICR_HIGH",
                "message": f"⚠️ Top holder peut crash >30%. Seuil: ${liq.crash_threshold_usd:,.0f}. ICR={liq.icr:.2f}"
            })
        elif liq.icr > 1.0:
            alerts.append({
                "severity": "warning",
                "code": "ICR_ELEVATED",
                "message": f"⚠️ Concentration élevée. ICR={liq.icr:.2f}"
            })
        
        if fc.wcc > 25 and fc.tci > 30:
            alerts.append({
                "severity": "critical",
                "code": "MANIPULATION",
                "message": f"🔴 Wallets liés détectés. WCC={fc.wcc:.1f}%, TCI={fc.tci:.1f}%"
            })
        
        if liq.dai > 0.4:
            alerts.append({
                "severity": "warning",
                "code": "BUY_WALL",
                "message": f"⚠️ Mur d'achat. DAI={liq.dai:.2f}"
            })
        elif liq.dai < -0.4:
            alerts.append({
                "severity": "warning",
                "code": "SELL_WALL",
                "message": f"⚠️ Mur de vente. DAI={liq.dai:.2f}"
            })
        
        if liq.lvr > 12:
            alerts.append({
                "severity": "critical",
                "code": "POOL_OVERHEAT",
                "message": f"🔴 Pool surchauffe. LVR={liq.lvr:.1f}"
            })
        
        if liq.lcr_fragile:
            alerts.append({
                "severity": "warning",
                "code": "LOW_COVERAGE",
                "message": f"⚠️ LCR fragile: {liq.lcr:.2f}%"
            })
        
        if ta.saturated:
            alerts.append({
                "severity": "warning",
                "code": "SATURATED",
                "message": f"⚠️ Saturé: RSI={rsi_1h:.1f}, BER={ta.ber:.2f}"
            })
        
        if fc.fci_alert:
            alerts.append({
                "severity": "critical",
                "code": "INSIDER_FUNDING",
                "message": f"🔴 Insider wallets: FCI={fc.fci:.1f}%"
            })
        
        if fc.scr_centralized:
            alerts.append({
                "severity": "warning",
                "code": "CENTRALIZED",
                "message": f"⚠️ Supply centralisée: Top5={fc.top5_pct:.1f}%"
            })
        
        report.alerts = alerts
        
        # ────────────────────────────────────────────
        # NARRATIVES
        # ────────────────────────────────────────────
        report.narrative_phase = self._build_phase_narrative(report)
        report.narrative_insight = self._build_insight(report, price, mcap, liquidity)
        report.narrative_structure = self._build_structure_narrative(report)
        
        # Surveillance levels
        if bf.detected:
            report.support_key = bf.pole_low
            report.resistance_key = bf.pole_high
        
        return report

    # ════════════════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════════════════
    
    def _f(self, val) -> float:
        """Safe float conversion."""
        if val is None:
            return 0.0
        try:
            if isinstance(val, str):
                val = val.replace(",", "")
            n = float(val)
            return n if math.isfinite(n) else 0.0
        except (TypeError, ValueError):
            return 0.0
    
    def _extract_top_balances(self, holders_list: list, n: int) -> List[float]:
        """Extract top N holder balances as USD values - CORRIGÉ pour Moralis."""
        balances = []
        for h in holders_list[:n]:
            # Moralis retourne usd_value, pas balance_usd
            bal = self._f(h.get("usd_value") or h.get("balance_usd") or h.get("value_usd") or 0)
            balances.append(bal)
        return balances
    
    def _estimate_slippage(self, trade_usd: float, liquidity: float) -> float:
        """Estimate slippage via constant product formula."""
        half_liq = liquidity / 2
        if half_liq <= 0:
            return 100.0
        return (trade_usd / (half_liq + trade_usd)) * 100
    
    def _detect_bull_flag_from_ohlcv(self, ohlcv: list, current_price: float) -> Tuple[float, float, float]:
        """Detect pole high/low from OHLCV - CORRIGÉ pour format array."""
        if not ohlcv:
            return 0, 0, current_price
        
        highs = []
        lows = []
        
        for c in ohlcv:
            if isinstance(c, (list, tuple)) and len(c) >= 5:
                # Format: [timestamp, open, high, low, close, volume]
                highs.append(self._f(c[2]))  # high
                lows.append(self._f(c[3]))   # low
            elif isinstance(c, dict):
                highs.append(self._f(c.get("high") or c.get("h", 0)))
                lows.append(self._f(c.get("low") or c.get("l", 0)))
        
        highs = [h for h in highs if h > 0]
        lows = [l for l in lows if l > 0]
        
        if not highs or not lows:
            return 0, 0, current_price
        
        return max(highs), min(lows), current_price
    
    def _sum_ohlcv_volume(self, ohlcv: list) -> float:
        """Sum volume from OHLCV candles - CORRIGÉ pour format array."""
        total = 0
        for c in ohlcv:
            if isinstance(c, (list, tuple)) and len(c) >= 6:
                total += self._f(c[5])  # volume at index 5
            elif isinstance(c, dict):
                total += self._f(c.get("volume") or c.get("v", 0))
        return total
    
    def _get_last_volume(self, ohlcv: list) -> float:
        """Get last candle volume - CORRIGÉ pour format array."""
        if not ohlcv:
            return 0
        last = ohlcv[0]  # Most recent first in GeckoTerminal
        if isinstance(last, (list, tuple)) and len(last) >= 6:
            return self._f(last[5])
        elif isinstance(last, dict):
            return self._f(last.get("volume") or last.get("v", 0))
        return 0
    
    def _calc_rsi_from_ohlcv(self, ohlcv: list, period: int = 14) -> Optional[float]:
        """Calculate RSI from OHLCV data."""
        if len(ohlcv) < period + 1:
            return None
        
        closes = []
        for c in ohlcv:
            if isinstance(c, (list, tuple)) and len(c) >= 5:
                closes.append(self._f(c[4]))  # close at index 4
            elif isinstance(c, dict):
                closes.append(self._f(c.get("close") or c.get("c", 0)))
        
        closes = [c for c in closes if c > 0]
        if len(closes) < period + 1:
            return None
        
        # Reverse if newest first
        if len(closes) >= 2 and closes[0] != closes[-1]:
            closes = list(reversed(closes))
        
        gains = []
        losses = []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def _calc_bollinger_from_ohlcv(self, ohlcv: list, period: int = 20) -> Dict:
        """Calculate Bollinger Bands from OHLCV data."""
        if len(ohlcv) < period:
            return {}
        
        closes = []
        for c in ohlcv:
            if isinstance(c, (list, tuple)) and len(c) >= 5:
                closes.append(self._f(c[4]))
            elif isinstance(c, dict):
                closes.append(self._f(c.get("close") or c.get("c", 0)))
        
        closes = [c for c in closes if c > 0]
        if len(closes) < period:
            return {}
        
        recent = closes[:period]
        middle = sum(recent) / period
        variance = sum((x - middle) ** 2 for x in recent) / period
        std_dev = variance ** 0.5
        
        upper = middle + (2 * std_dev)
        lower = middle - (2 * std_dev)
        bandwidth = ((upper - lower) / middle) * 100 if middle > 0 else 0
        
        return {
            "upper": upper,
            "middle": middle,
            "lower": lower,
            "bandwidth": bandwidth,
            "bandwidth_max": bandwidth * 1.5
        }
    
    def _calc_tci(self, holder_list: list) -> float:
        """Calculate Temporal Concentration Index."""
        if not holder_list or len(holder_list) < 2:
            return 0
        
        # Check for contracts vs EOA concentration
        contracts = sum(1 for h in holder_list[:20] if h.get("is_contract", False))
        if contracts > 10:
            return contracts * 5  # High contract concentration
        
        # Check for entity concentration (same entity holding multiple positions)
        entities = [h.get("entity") for h in holder_list[:20] if h.get("entity")]
        if entities:
            entity_counts = Counter(entities)
            max_entity = max(entity_counts.values()) if entity_counts else 0
            if max_entity > 2:
                return max_entity * 15
        
        return 0
    
    def _calc_fci(self, holder_list: list) -> float:
        """Calculate Funding Correlation Index."""
        if not holder_list or len(holder_list) < 5:
            return 0
        
        # Check for known entities (CEX, protocols)
        known_entities = []
        for h in holder_list[:20]:
            entity = h.get("entity") or h.get("owner_address_label")
            if entity:
                known_entities.append(entity.lower())
        
        if len(known_entities) < 2:
            return 0
        
        counts = Counter(known_entities)
        if counts:
            most_common = counts.most_common(1)[0][1]
            return (most_common / len(known_entities)) * 100
        
        return 0
    
    def _calc_wcc(self, holder_list: list) -> float:
        """Calculate Wallet Clustering Coefficient."""
        if not holder_list or len(holder_list) < 5:
            return 0
        
        # Simple heuristic: check for similar balance patterns
        balances = [self._f(h.get("usd_value", 0)) for h in holder_list[:20]]
        balances = [b for b in balances if b > 0]
        
        if len(balances) < 5:
            return 0
        
        # Check for suspiciously similar balances (within 5%)
        similar_count = 0
        for i in range(len(balances)):
            for j in range(i + 1, len(balances)):
                if balances[j] > 0:
                    ratio = balances[i] / balances[j]
                    if 0.95 <= ratio <= 1.05:
                        similar_count += 1
        
        max_pairs = len(balances) * (len(balances) - 1) / 2
        return (similar_count / max_pairs) * 100 if max_pairs > 0 else 0
    
    # ════════════════════════════════════════════════════════
    # NARRATIVE BUILDERS
    # ════════════════════════════════════════════════════════
    
    def _build_phase_narrative(self, r: ForensicReportV5) -> str:
        phase = r.convergence.phase
        fl = r.flows
        
        if phase == "ACCUMULATION":
            parts = [f"Phase: ACCUMULATION"]
            if fl.nbp > 0:
                parts.append(f"✅ NBP +{fl.nbp:.0f}% (pression acheteuse)")
            parts.append(f"→ Smart money accumule")
            return " | ".join(parts)
        
        elif phase == "DISTRIBUTION":
            parts = [f"Phase: DISTRIBUTION"]
            if fl.nbp < 0:
                parts.append(f"🔴 NBP {fl.nbp:.0f}% (pression vendeuse)")
            parts.append(f"→ Distribution active")
            return " | ".join(parts)
        
        elif phase == "RUPTURE":
            return f"Phase: RUPTURE | BPI {r.bull_flag.bpi:.2f} | Breakout imminent"
        
        else:
            return f"Phase: {phase} | NBP {fl.nbp:+.0f}% | EV {fl.ev:.2f}"
    
    def _build_insight(self, r: ForensicReportV5, price: float, mcap: float, liq: float) -> str:
        fhs = r.convergence.fhs
        cp = r.convergence.cp
        
        if fhs > 7 and cp > 60:
            return (f"💎 Structure solide (FHS {fhs}/10). "
                    f"CP {cp:.0f}%. LCR {r.liquidity.lcr:.1f}%, ICR {r.liquidity.icr:.2f}.")
        elif fhs < 4:
            alert_type = "manipulation" if r.forensic.wcc_alert else "structurel"
            return (f"⚠️ Critique (FHS {fhs}/10). "
                    f"Risque {alert_type}. ICR {r.liquidity.icr:.2f}. CP {cp:.0f}%.")
        else:
            return (f"⚪ Modéré (FHS {fhs}/10). "
                    f"CP {cp:.0f}%. Surveillance requise.")
    
    def _build_structure_narrative(self, r: ForensicReportV5) -> str:
        bf = r.bull_flag
        if not bf.detected:
            return "Pas de bull flag détecté."
        
        return (f"Bull Flag Classe {bf.flag_class} | "
                f"Retrace {bf.retracement_pct:.1f}% | "
                f"FQS {bf.fqs:.0f} ({bf.fqs_label}) | "
                f"BPI {bf.bpi:.2f} ({bf.bpi_label}) | "
                f"Target 1.618: ${bf.fib_target_1618:.6f} (+{bf.fib_upside_pct:.0f}%)")


# ════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json
    import sys
    
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
        
        # Si le JSON contient plusieurs tokens
        if "tokens" in data:
            for addr, token_data in data["tokens"].items():
                engine = ForensicEngineV5()
                report = engine.analyze(token_data)
                print(f"\n{'='*60}")
                print(f"Token: {report.symbol} ({report.token_address[:10]}...)")
                print(f"Phase: {report.convergence.phase}")
                print(f"FHS: {report.convergence.fhs}/10 ({report.convergence.fhs_label})")
                print(f"CP: {report.convergence.cp}%")
                print(f"ICR: {report.liquidity.icr:.2f}")
                print(f"NBP: {report.flows.nbp:.1f}%")
                print(f"Bull Flag: {report.bull_flag.detected} (BPI: {report.bull_flag.bpi:.2f})")
                print(f"Alerts: {len(report.alerts)}")
                for alert in report.alerts:
                    print(f"  - [{alert['severity']}] {alert['message']}")
        else:
            engine = ForensicEngineV5()
            report = engine.analyze(data)
            print(json.dumps(report.to_dict(), indent=2))
    else:
        print("Usage: python forensic_engine_v5_fixed.py <snapshot.json>")
