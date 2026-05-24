# Phase 8: Quick Start Checklist

> Before you start shadow trading, work through this checklist. Estimated time: 15–30 minutes.

---

## 1. Verify System Integrity (5 min)

```bash
# In project root:
python -m pytest -q
```

**Expected:** 64 tests passing (all green dots)  
**If failures:** Git pull latest, check for uncommitted changes

```bash
git status
```

**Expected:** Clean working tree (no uncommitted changes)

---

## 2. Choose Trading Period & Symbol (2 min)

**Which symbol first?**
- [ ] **EURUSD** (recommended) — more stable, tested extensively
- [ ] **NAS100** (if broker symbol confirmed)
- [ ] Both (advanced)

**Availability during NY AM window (10:00–11:00 New York)?**
- [ ] Yes, can watch for 30–60 min most weekdays
- [ ] Yes, but only certain days (specify: ______)
- [ ] No, wait for Phase 8.5 (async validation)

**Target collection period:**
- [ ] 2 weeks (12 trading days, ~15–20 setups)
- [ ] 3–4 weeks (20+ trading days, 30–50 setups) — recommended
- [ ] Continuous (no end date)

---

## 3. NAS100 Setup (if trading NAS100)

**Check your MT5:**
1. Open Market Watch → Search for Nasdaq 100 index
   - Write down the **exact symbol name:** __________
   - (Common names: NAS100, USTEC, US100, NDX)

2. Right-click symbol → Properties → Specifications
   - Write down **Contract size** (usually 1 lot = $1 per point): __________
   - Write down **Point size** (usually 1.0): __________

3. Update `config/symbols.yaml`:
   ```yaml
   NAS100:
     broker_symbol: "{your_symbol}"     # Replace with actual
     pip_value_per_lot: {contract_size}  # Replace with actual
   ```

4. Test:
   ```bash
   python -m cli.main analyze NAS100
   ```
   **Expected:** JSON with valid setup, NOT a "no candles" error

---

## 4. Prepare Logging (3 min)

**Open `logs/trades.md` in your editor**

This is where you'll record every analysis (traded or skipped).

**Template reminder:**
```
| 2026-05-26 | abc123def45 | EURUSD | silver_bullet | LONG | 1.0950 | 1.0920 | 1.1010 | 1.1010 | +2.0R | Swept pool before entry, clean confluenza 5/5 |
```

- Date (UTC): YYYY-MM-DD
- run_id: From stdout after running CLI
- Symbol: EURUSD or NAS100
- Model: Always `silver_bullet`
- Dir: LONG or SHORT
- Entry, Stop, Target: Levels from JSON
- Exit: Actual exit price (or `—` if not traded)
- Result (R): (exit - entry) / (entry - stop), positive or negative
- Notes: Why you traded it / why you skipped it / observations

**Create a blank row template:**

```markdown
| DATE    | run_id | SYMBOL | MODEL | DIR | ENTRY | STOP | TARGET | EXIT | RESULT | NOTES |
|---------|--------|--------|-------|-----|-------|------|--------|------|--------|-------|
| 2026-05 |        |        |       |     |       |      |        |      |        |       |
```

Paste this at the end of `logs/trades.md` so you can fill in quickly.

---

## 5. Understand Phase D Signals (5 min)

When you run the analysis and review the JSON, look for these **Phase D signals**:

| Signal | JSON Field | What It Means |
|--------|-----------|---------------|
| **OTE** | `setup_candidates[0].entry_in_ote` | Entry within Fibonacci 61.8–79% retracement zone? |
| **OTE zone** | `setup_candidates[0].ote_zone` | The calculated retracement band (low, high) |
| **Sweep** | `setup_candidates[0].sweep_confirmed` | Did price sweep a liquidity pool before entry? |
| **Breakers** | `liquidity.breakers[]` | Any mitigated order blocks (inverted S/R)? |
| **Multi-target** | `setup_candidates[0].targets[]` | Are there 3 targets (T1/T2/T3)? |

**For each trade, note:**
- Was OTE active? (Y/N)
- Was sweep confirmed? (Y/N)
- How many breakers detected? (#)
- Were multi-targets present? (Y/N)

---

## 6. Chart Setup (2 min)

**On your MT5 chart (EURUSD or NAS100):**

1. **Timeframes visible:** D1, H4, H1, M5
   - Use "Profiles" or four-chart layout
   - This matches the CLI data (D1 bias, H4 structure, H1 entry, M5 confirmation)

2. **Levels to draw (optional but helpful):**
   - FVG zones (from JSON `structure.fvg_active[]`)
   - Swing highs/lows (from JSON `structure.by_tf[]`)
   - Entry level (from JSON `setup_candidates[0].entry_level`)
   - Stop level (from JSON `setup_candidates[0].stop`)
   - Target level (from JSON `setup_candidates[0].targets[0]`)

3. **Time zone:** Set MT5 to UTC or NY (ET)
   - Silver Bullet window is 10:00–11:00 NY (14:00–15:00 UTC in summer)

---

## 7. Pre-Trade Decision Framework (3 min)

Before you execute any trade, ask yourself:

**1. Does the JSON setup match the chart?**
- [ ] Entry level: Is it at the FVG/pool you see?
- [ ] Stop level: Is it beyond the swing or OB?
- [ ] Target level: Is it at a realistic liquidity level?
- **If NO to any:** Skip this trade. Log it anyway with reason "Setup mismatch with chart"

**2. Does the confluence make sense?**
- [ ] Bias aligned (D1/H4/H1 agree on direction)?
- [ ] BOS/CHOCH recent (last event within last 3 candles)?
- [ ] FVG in entry zone (not stale)?
- [ ] Session window active (10:00–11:00 NY)?
- [ ] News clear (no blackout)?
- **Minimum:** 3 of 5. If < 3, skip.

**3. Is the R:R acceptable?**
- [ ] R:R ≥ 2.0 on target 1? (e.g., 30 pip stop, 60 pip target = 2.0R)
- [ ] Or is this a "learning setup" where you skip due to low R?
- **Standard:** Require 2.0R. Exception: OK to skip low-R setups (don't force trades).

**4. Can you actually execute?**
- [ ] Entry price achievable (not way off the current M5 price)?
- [ ] Stop placeable below/above without triggering on spreads?
- [ ] Position size fits your account (using 0.5% risk rule)?
- **If NO:** Skip this one. Log it with reason "Not executable at market".

**If YES to all:** Execute the trade.  
**If NO to any:** Skip it. Log it. Move to next analysis.

---

## 8. Daily Execution Rhythm (During NY AM Window)

**09:50 ET:** Start your MT5, open the relevant chart, open `logs/trades.md`

**10:00–11:00 ET:** Watch and analyze
- Run CLI 1–3 times in this window (not more, you'll chase)
- For each setup: decide trade/skip within 30 seconds
- Log immediately (don't wait until end of day)

**11:00 ET+:** Close positions or let winners run (based on your plan)
- If trade is open and target not hit, decide:
  - Hold to the next day? (Overnight risk)
  - Close at market? (Lock in partial)
  - Let stop execute? (Full risk)
- **For Phase 8:** Close all positions by end of day (keep it simple)

**15:00–16:00 ET (end of US market):** Update your weekly summary in `logs/trades.md`

---

## 9. What to Expect in First Week

**Week 1 is calibration, not performance.**

### Likely scenarios:
1. **"The entry I missed"** — Setups you skip actually win
   - → Normal. You're validating logic, not forcing trades
   - → Log it with reason "Confluence low" or "Skipped due to risk check"

2. **"Why did this lose?"** — A high-confluence setup stops out
   - → Normal. Win rate will be ~50%, variance is expected
   - → Log it with reason "Hit stop at [level], market reversed"

3. **"I didn't see any setups"** — Market slow, only 1–2 analyses in the window
   - → Normal. Some weeks are slow
   - → Keep running analyses, data still counts

4. **"The chart doesn't match the JSON"** — Entry level 5 pips away from FVG
   - → Possible. Log with reason "Chart mismatch, need to verify"
   - → This might indicate bugs in swing/FVG detection (report in notes)

**No judgment in Week 1.** You're learning the system's behavior under live conditions.

---

## 10. First Run (Try This Now)

**Right now, test the system in fixtures mode:**

```bash
python -m cli.main analyze EURUSD --trend up
```

**You should see:**
1. CLI runs for 5–10 seconds
2. Outputs analysis with timeframes (D1, H4, H1)
3. Last line shows: `context JSON  : context\{run_id}.json`
4. JSON file created in `context/` folder

**What to check in the JSON:**
```json
{
  "run_id": "some12hex",
  "created_at_utc": "2026-05-24T...",
  "symbol": "EURUSD",
  "validator_result": {
    "status": "GO"  ← If this is GO, you're ready
  },
  "setup_candidates": [
    {
      "direction": "LONG",  ← Direction
      "entry_level": 1.0950,
      "stop": 1.0920,
      "targets": [1.1010],  ← Target 1
      "confluence_score": 4,  ← Out of 5
      "ote_zone": [1.0970, 1.0990],  ← Phase D signal
      "entry_in_ote": true,
      "sweep_confirmed": false
    }
  ]
}
```

**If you see this:** System is working. You're ready for Phase 8.  
**If you see errors:** Check git status, run tests, ask for debugging.

---

## 11. Final Pre-Trade Checklist (Before First Real Trade)

- [ ] 64 tests passing
- [ ] NAS100 symbol confirmed (if trading it)
- [ ] `logs/trades.md` prepared with template
- [ ] MT5 chart ready with D1/H4/H1/M5
- [ ] Timezone set to NY (ET) in MT5
- [ ] First fixture test run successful (JSON generated)
- [ ] Pre-trade decision framework understood (6 questions)
- [ ] Account risk: 0.5% per trade, daily limit 5%, total limit 10%
- [ ] Realistic expectation: 50% win rate, 1.5R average
- [ ] Understand that Phase 8 is validation, not performance test

---

## 12. Support & Debugging

**If you hit an error:**

| Error | Action |
|-------|--------|
| "No candles for NAS100" | Update broker_symbol in `config/symbols.yaml` |
| "Invalid data_mode" | Check `config/account.yaml` has `data_mode: mt5` or `fixtures` |
| "MT5 not found" | Install MetaTrader5: `pip install MetaTrader5` |
| "Validator says BLOCKED" | Check `validator_result.failures[]` for reason, skip trade |
| "JSON doesn't match chart" | Report in `PHASE_8_SHADOW_TRADING_RESULTS.md` as issue |

**Questions?**

Refer to:
- `PHASE_8_SHADOW_TRADING.md` — Full Phase 8 guide
- `PHASE_8_SHADOW_TRADING_RESULTS.md` — Results tracking (fill as you go)
- `CLAUDE.md` — Interpretation guide
- `PROJECT_STATE.md` — System status

---

## Ready? 

**Once you've worked through this checklist:**

```bash
# Confirm system
python -m pytest -q

# Test one analysis
python -m cli.main analyze EURUSD

# Watch during NY AM (10:00–11:00 ET)
# Log results in logs/trades.md
# Track in PHASE_8_SHADOW_TRADING_RESULTS.md after 15+ setups
```

**Good luck. Collect data, stay disciplined, make informed decision.**
