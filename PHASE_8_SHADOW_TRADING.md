# Phase 8: Shadow Trading & Edge Validation

> **Status:** Ready to execute. All phases A-D implemented, 64 tests passing, EURUSD live verified.  
> **Goal:** Collect 30+ setups over 2 weeks to validate whether Phase D signals genuinely improve the edge.  
> **Timeline:** Flexible (shadow trading doesn't require immediate execution), measured in trading days not calendar days.

---

## Why Phase 8 Matters

Phases A-D added sophisticated ICT enhancements:
- **D1b:** Order Blocks now detected and scored in confluence
- **D2:** OTE (Optimal Trade Entry) zone computed as Fib 61.8-79%
- **D3:** Liquidity sweep confirmation as a confluence factor
- **D4:** Breaker Blocks (mitigated OBs with inverted role) detected
- **D5:** Multi-target exits (T1/T2/T3) instead of single target

**Problem:** These are theoretically sound but **not yet validated in live trading**. Phase 8 answers: _Do these actually improve win rate or just add complexity?_

**Method:** Run 30+ analyses during NY AM Silver Bullet windows (live data, real setups), compare Phase D signals against actual price action, decide whether to trust them in FTMO real mode.

---

## Pre-Phase-8 Checklist

Before starting shadow trading, confirm:

### ✓ Code is stable
```bash
python -m pytest -q  # Should show 64 passing tests
git status           # Should be clean
```

### ✓ Fixture mode works
```bash
python -m cli.main analyze EURUSD --now 2026-05-26T15:00 --trend up
# Should output AnalysisContext JSON with valid setup_candidates[]
```

### ✓ Live MT5 is wired (if available)
- [ ] Terminal MT5 running and logged in
- [ ] `config/account.yaml` has `data_mode: mt5`
- [ ] `.env` file populated (if using OANDA as secondary)
- [ ] Test one symbol: `python -m cli.main analyze EURUSD`
  - Should return fresh data (age_seconds ≈ 0-60)
  - JSON should have `data_quality.source = "mt5"`

### ✓ NAS100 broker symbol confirmed
- [ ] Check your broker's exact symbol name for Nasdaq 100
  - Possible names: `NAS100`, `USTEC`, `US100`, `NDX`
- [ ] Update `config/symbols.yaml` line 29 if different from `NAS100`
- [ ] Verify `pip_value_per_lot` matches your broker's contract specs
  - Most brokers: $1 per point per lot (CFD standard)
  - Some brokers: $0.10 or $10 per point — check your contract!

### ✓ Trading window is realistic
- [ ] Timezone is set to NY (ET) in `config/account.yaml`
- [ ] Silver Bullet window 10:00–11:00 NY AM is accessible (not pre-market in your time zone)
- [ ] Can execute trades during that window (not sleeping/working/unavailable)

---

## Phase 8 Workflow (Per Analysis)

### Step 1: Time + Trigger
- **When:** During NY AM Silver Bullet window (10:00–11:00 NY, ~14:00–15:00 UTC)
- **Where:** Main EURUSD or NAS100 chart open in MT5, watching M1 candles
- **What:** When you see a potential setup forming (FVG forming, BOS just occurred, structure breaking):

### Step 2: Run Analysis
```bash
# Live MT5 data
python -m cli.main analyze EURUSD
# OR
python -m cli.main analyze NAS100

# Capture the run_id from stdout:
#   context JSON  : context\{run_id}.json
```

### Step 3: Review JSON + Manual Check
1. Read the generated `context/{run_id}.json`
   - Validator status: GO or BLOCKED?
   - If BLOCKED: log reason, move to next setup (don't trade)
   - If GO: proceed
   
2. Cross-check against the chart:
   - Entry level: Does it match the FVG/zone on screen?
   - Stop: Is it logically placed (beyond swing/OB)?
   - Target: Does it align with next liquidity pool/HTF level?
   - Confluence factors: Do they match what you see (bias, draw, session)?
   
3. **Validate Phase D signals specifically:**
   - **OTE zone:** Is entry within the Fib band shown? Logical?
   - **Sweep:** Did the nearest pool just get swept (wick beyond, close inside)?
   - **Breaker Blocks:** Any mitigated OBs visible? Do they align?
   - **Multi-target:** Are T1/T2/T3 spaced logically (T1 at OB/FVG CE, T2 at pool, T3 at range)?

### Step 4: Execute (Optional) or Skip
- **If confident:** Enter at suggested entry level, place stop/target
  - Real trade: track in `logs/trades.md` as you close
  - Record: entry time, entry price, exit time, exit price, profit/loss in pips
  
- **If unsure:** Skip this one
  - **Do NOT trade to collect data** — only trade if the setup genuinely looks good
  - Shadow trading = validation, not forced compliance

### Step 5: Log Analysis (Always)
Even if you don't trade it, log the setup:

```bash
# Copy this line to logs/trades.md:
| 2026-05-26 | {run_id} | EURUSD | silver_bullet | LONG | 1.0950 | 1.0920 | 1.1010 | — | — | Not traded: confluence 3/5 but RTH close imminent |
```

**Fields:**
- `Date (UTC)` — when you ran the analysis
- `run_id` — from stdout (also filename in `context/`)
- `Symbol` — EURUSD or NAS100
- `Model` — always `silver_bullet` (our only model)
- `Dir` — LONG or SHORT from JSON `setup_candidates[0].direction`
- `Entry`, `Stop`, `Target` — from JSON `entry_level`, `stop`, `targets[0]`
- `Exit` — actual exit price if traded, `—` if not
- `Result (R)` — (exit - entry) / (entry - stop) if traded, `—` if not
- `Notes` — why you traded it / why you skipped it / Phase D observations

---

## Data Collection Goals

**Minimum:** 30 setups over 2 weeks  
**Ideal:** 50+ setups, or 4 weeks of NY AM windows

**Why these numbers?**
- 30 setups = statistical minimum to detect edge
- 4 weeks = captures variance (good days + slow days)
- NY AM window = consistent session (no PM volatility bias)

**What counts as a "setup"?**
- Validator returns GO (not BLOCKED)
- Confluence ≥ 3/5 categories
- R:R ≥ 2.0
- Entry, stop, target all clear and executable

---

## Phase D Validation Matrix

After collecting data, score each setup on Phase D signals:

| Signal | Indicator | Expected Value | Validation |
|--------|-----------|-----------------|------------|
| OTE | entry_in_ote | true | Was entry within Fib 61.8-79% band? |
| OTE | ote_zone | (float, float) | Accurate zone calculated? |
| Sweep | sweep_confirmed | true/false | Did price sweep a pool before entry? |
| OB | confluence_factors includes "OB" | true | Were OBs detected and scored? |
| Breaker | breakers[] not empty | varies | Any mitigated OBs detected? |
| Multi-target | targets[] length | 3 | Are T1/T2/T3 all present? |

**Decision rules after data collection:**

1. **If Phase D signals correlate with wins:** Trust them (confluence score +1 each)
2. **If Phase D signals correlate with losses:** Disable them (remove from confluence)
3. **If no correlation:** Keep them (neutral, better to have options for trader judgment)

Example:
- Hypothesis: Trades with sweep_confirmed=true have higher win rate
- After 30 setups: sweep trades won 12/15 (80%), non-sweep won 8/15 (53%)
- Decision: Keep sweep_confirmation in confluence scoring ✓

---

## Shadow Trading Cadence

### Weekly rhythm
- **Monday–Friday 10:00–11:00 NY AM:** Run analysis 1-3 times per window
  - Don't force trades; only trade if setup genuinely looks good
  - Run analysis even if you don't trade it (validate Phase D signals)
  
- **Friday end-of-day:** Update `logs/trades.md` with the week's data
  - Count: setups analyzed, setups traded, wins, losses, average R
  
- **Every 2 weeks (after 15+ setups):** Interim review
  - Are Phase D signals showing edge? Any surprises?
  - Update `PHASE_8_SHADOW_TRADING_RESULTS.md` with findings

### Example week (May 26–30, 2026)
```
Mon 05-26: 2 analyses (1 traded, won 1.5R)
Tue 05-27: 3 analyses (1 traded, lost 0.8R)
Wed 05-28: 1 analysis (skipped, low confluence)
Thu 05-29: 2 analyses (1 traded, won 2.1R)
Fri 05-30: 2 analyses (2 traded, 1 won 1.8R, 1 lost 0.5R)
WEEK TOTAL: 10 analyses, 5 traded, 3 won, 2 lost, avg +1.2R
```

---

## Contingency: What If Phase 8 Finds Issues?

### Issue: Low win rate on Phase D signals
- **Example:** OTE entries = 20% win rate vs non-OTE = 60%
- **Action:** Disable OTE from confluence scoring; keep code but don't score
- **Keep Phase D implementation** for future refinement (don't revert commits)

### Issue: No setups in 2 weeks (market slow)
- **Decision:** OK — collect for 3-4 weeks instead
- **Reason:** Need enough data; slow market is valid state

### Issue: Breaker Blocks cause false confluence
- **Example:** Every breaker block trade loses
- **Action:** Set `confluence_factors` to exclude breaker blocks temporarily
- **Investigate:** Why are mitigated OBs causing losses? (Risk management issue? Wrong invalidation level?)

### Issue: Targets unrealistic (T1 never filled)
- **Example:** T1 is at a HTF pool that price doesn't reach in session
- **Action:** Adjust target selection logic in `setups.py:_build_targets()`
- **Refinement:** Use session-length timeframe (don't pick HTF targets for intraday exit)

---

## Ending Shadow Trading (Transition to FTMO)

After 4 weeks / 50 setups, make a GO/NO-GO decision:

### GO (Phase 9: Demo)
- [ ] Win rate ≥ 50% on Phase D-enhanced setups
- [ ] Average R ≥ 1.5 (every winning trade pays 1.5x risk)
- [ ] Confluence ≥ 3/5 is statistically valid (not luck)
- [ ] No systematic losses from new Phase D signals

**Next:** 2-4 weeks **demo trading** (real money, FTMO 2-Step simulator or small account) to prove edge holds under pressure.

### NO-GO (Phase 8 Extension or Phase D Review)
- [ ] Win rate < 50%
- [ ] Average R < 1.5
- [ ] Phase D signals uncorrelated with wins (just noise)

**Next:** 
1. Analyze why (review `logs/trades.md`)
2. Either extend Phase 8 for more data
3. Or refine Phase D logic and repeat Phase 8

---

## Files to Monitor/Update

**`logs/trades.md`** — Main shadow trading record (update weekly)  
**`logs/analyses.jsonl`** — Automatic audit log (do NOT edit, append-only)  
**`context/`** — Analysis JSON files (keep for reference, can archive after 1 month)  
**`PHASE_8_SHADOW_TRADING_RESULTS.md`** — Create after 15+ setups (this file, tracking progress)

---

## Quick Start Command

```bash
# During NY AM window (10:00–11:00 NY):
python -m cli.main analyze EURUSD

# Review JSON + chart
# Log to logs/trades.md
# Trade if confident (optional)
```

---

## When to Escalate to Phases 9–10

**Phase 9 (Demo):** After Phase 8 confirms edge (50+ setups, win rate ≥ 50%, avg R ≥ 1.5)

**Phase 10 (FTMO Real):** After Phase 9 validates on real capital with pressure

**If Phase 8 finds issues:** Fix in code, return to Phase 8 for re-validation.

---

**Phase 8 is not a race.** Collect data, validate signals, make informed decision. The entire FTMO Challenge is still ahead — better to spend 2-4 weeks validating now than to fail Phase 1 with overconfidence.

Good luck. Track everything in `logs/`.
