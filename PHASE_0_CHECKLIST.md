# Phase 0 Checklist — Scope & Configuration

> **Objective:** Before writing ANY code, define exactly what the system will trade, when, how much risk, and when to stop.
> 
> **Time:** 3-5 hours (mostly decision-making, not coding)
> **Deadline:** Complete before Phase 1 starts

---

## Section 1: Account & Challenge Parameters

### 1.1 FTMO Challenge Type

- [ ] Type chosen: **1-Step** or **2-Step**?
  - 1-Step: Single 5% profit target, 5% daily loss limit
  - 2-Step: Two phases, higher targets
  - **Decision:** ________________

### 1.2 Capital & Limits

- [ ] Initial capital: **$______________**
- [ ] Official daily loss limit: **___% (FTMO rule)**
- [ ] Your conservative buffer: **___% (when you'll stop trading that day)**
  - Recommendation: 3.5% buffer for 5% official limit
  - Decision: ________________

- [ ] Official total loss limit: **___% (FTMO rule)**
- [ ] Your conservative buffer: **___% (when you'll pause system)**
  - Recommendation: 8.0% buffer for 10% official limit
  - Decision: ________________

- [ ] Profit target: **___% (required to complete challenge)**
  - Usually: 5-10% depending on type
  - Decision: ________________

- [ ] Minimum trading days: **_____ days (FTMO requirement)**
  - Usually: 10-20 days
  - Decision: ________________

### 1.3 Account & Broker Details

- [ ] Broker/MT5 server: ________________
- [ ] Account number: ________________ (do NOT share)
- [ ] Currency: **USD** / EUR / GBP / Other: ______
- [ ] Leverage available: **up to 1:_____**
- [ ] Timezone (broker): ________________

---

## Section 2: Trading Parameters

### 2.1 Time Zone

- [ ] Your reference timezone: ________________ (e.g., Europe/Lisbon)
- [ ] Trading timezone: ________________ (e.g., America/New_York for NY sessions)
- [ ] System will track all times in: **UTC** (converted to your display timezone)

### 2.2 Primary Trading Assets

**Choose 1-3 symbols for Phase 0-5 shadow trading.**

- [ ] Symbol 1: **________________**
  - MT5 symbol: ________________
  - OANDA symbol: ________________ (e.g., EUR_USD)
  - Example: EURUSD, GBPUSD, USDJPY

- [ ] Symbol 2 (optional): **________________**
  - MT5 symbol: ________________
  - OANDA symbol: ________________

- [ ] Symbol 3 (optional): **________________**
  - MT5 symbol: ________________
  - OANDA symbol: ________________

**Recommendation:** Start with EURUSD (most liquid, best data availability).

### 2.3 Session Selection

**Choose the PRIMARY trading session for Phase 1-6.**

- [ ] Session: **NY AM** / London / Asian / Other: ________________

**Why NY AM (Silver Bullet)?**
- Highest volatility
- Most predictable
- Kill Zone is well-defined (13:00-16:00 CEST)
- Most tested ICT model

- [ ] Trading window (in CEST): **HH:MM - HH:MM**
  - Example for NY AM: 13:00 - 16:00 CEST
  - Window: ________________

- [ ] Maximum trades per window: **____ trades**
  - Recommendation: 1-3
  - Decision: ________________

---

## Section 3: Risk Management

### 3.1 Position Sizing

- [ ] Default risk per trade: **0.25%** / **0.50%** / **1.0%** / Other: _____%
  - Recommendation: 0.50% per trade
  - Decision: ________________

- [ ] Maximum risk per trade: **_____%**
  - Absolute ceiling (some days you might risk less)
  - Decision: ________________

- [ ] Risk calculation formula:
  - Risk = (Entry Price − Stop Price) in pips × Lot Size
  - Position Size = (Account Capital × Risk%) ÷ (Stop Distance in pips × 10)
  - **Understood:** [ ] Yes

### 3.2 Reward:Risk Ratio

- [ ] Minimum R:R ratio: **2:1** / **2.5:1** / **3:1** / Other: ___:___
  - Minimum acceptable: 2:1 (for every pip risked, you must make 2)
  - Decision: ________________

- [ ] If a setup has R:R < minimum:
  - [ ] Skip it (BLOCKED)
  - [ ] Accept if confluence is exceptional (rare)
  - Decision: ________________

### 3.3 Loss Management

- [ ] Maximum consecutive losses per day: **_____ losses**
  - After 1 loss: continue / after 2 losses: stop / custom: ______
  - Recommendation: Stop after 2 losses, max per day
  - Decision: ________________

- [ ] If daily buffer is hit:
  - [ ] Stop ALL trades for rest of day (BLOCKED)
  - [ ] Reduced risk only (not recommended for FTMO)
  - Decision: ________________

---

## Section 4: ICT Methodology — First Model

### 4.1 Choose Your Starting Model

- [ ] **NY AM Silver Bullet (RECOMMENDED)**
  - Session: NY AM (13:00-16:00 CEST)
  - Trigger: Kill Zone + liquidity grab + return
  - Confluence: HTF bias + FVG/OB + session timing
  - Timeframes: D1 → H4 → H1 → M5/M1

- [ ] Other (explain rationale): ________________
  - Note: Starting with Silver Bullet is strongly recommended
  - Other models are Phase 6+ additions

### 4.2 Timeframes for HTF Analysis

- [ ] Monthly (MN): Use for macro context only? [ ] Yes  [ ] No
- [ ] Weekly (W1): Use for bias confirmation? [ ] Yes  [ ] No
- [ ] Daily (D1): Primary bias source? [ ] Yes
- [ ] H4: Secondary structure? [ ] Yes
- [ ] H1: Entry confirmation? [ ] Yes
- [ ] M15/M5/M1: Micro entries? [ ] M5 and M1

**Standard:** MN [context] → W1/D1 [bias] → H4 [structure] → H1 [entry setup] → M5/M1 [micro]

### 4.3 Confluence Minimum

- [ ] Minimum confluence factors required for trade: **3** / **4** / Other: _____
  - Factors: HTF bias, Liquidity (DoL), Structure (FVG/OB), Session (Kill Zone), Correlation
  - Recommendation: Minimum 3, all conditions met
  - Decision: ________________

### 4.4 Stop Loss Rules

- [ ] Stop must be: **Fixed** / Trailing / Dynamic
  - Only fixed stops allowed for FTMO
  - Decision: Fixed

- [ ] Stop placement strategy:
  - Example: Below recent Swing Low − 2 pips (long entry)
  - Decision: ________________

- [ ] Minimum stop distance: **_____ pips**
  - Should exceed average spread on the pair
  - Example: EURUSD spread = 1.0 pip, so minimum stop = 20-30 pips
  - Decision: ________________

---

## Section 5: Data Sources

### 5.1 OHLCV Data

- [ ] Primary source: **MT5** (live account data)
  - Pros: Direct from broker, account state integrated
  - Cons: Known cache bugs (must handle)
  
- [ ] Secondary source: **OANDA REST API**
  - Pros: Clean API, validates MT5 data
  - Cons: Demo account (API key from free account)
  - OANDA Demo Account Needed? [ ] Yes → Create at oanda.com (free)
  - API Key (in .env): ________________

- [ ] Acceptable divergence (MT5 vs OANDA): **<0.5%** price difference
  - If > 0.5%: **Data BLOCKED** (unclear which is correct)
  - Decision: ________________

### 5.2 Economic Calendar

- [ ] Source: **ForexFactory XML feed** (public, no auth)
  - Pulls events for next 48 hours
  - Identifies high-impact events for trading pair
  - No configuration needed

### 5.3 Account State

- [ ] Source: **MT5 account_info()**
  - Equity, balance, drawdown, open trades, commission, swap
  - Used to calculate: daily loss %, total drawdown %
  - Refreshed: every analysis run

---

## Section 6: Validation Rules (What Blocks the System)

### 6.1 Data Quality Blocks

- [ ] Data older than **5 minutes**: BLOCKED? [ ] Yes (recommended)
- [ ] Sources (MT5 vs OANDA) diverge > 0.5%: BLOCKED? [ ] Yes (recommended)
- [ ] Any required data missing (account, calendar, prices): BLOCKED? [ ] Yes

### 6.2 News Blocks

- [ ] High-impact event in next **90 minutes**: BLOCKED? [ ] Yes (recommended)
- [ ] By currency: Block based on pair base/quote? [ ] Yes (example: USD event for EURUSD)

### 6.3 Session Blocks

- [ ] Outside valid Kill Zone: **AGUARDAR** (not BLOCKED, try next window)? [ ] Yes
- [ ] No valid session within next **24 hours**: BLOCKED? [ ] Yes (optional)

### 6.4 Account Risk Blocks

- [ ] Daily loss ≥ daily buffer: BLOCKED? [ ] Yes (recommended)
- [ ] Total loss ≥ total buffer: BLOCKED? [ ] Yes (FTMO account fails)
- [ ] Consecutive losses ≥ max per day: BLOCKED? [ ] Yes

### 6.5 Setup Quality Blocks

- [ ] Confluence < minimum (default: 3): BLOCKED? [ ] Yes (recommended)
- [ ] R:R < minimum (default: 2:1): BLOCKED? [ ] Yes
- [ ] Stop too tight (< min distance): BLOCKED? [ ] Yes
- [ ] Position size would be 0 (stop too wide): BLOCKED? [ ] Yes

---

## Section 7: Outputs & Logging

### 7.1 Report Format

- [ ] Report location: **reports/** (auto-created with timestamp)
- [ ] Report includes:
  - [ ] Bias (HTF)
  - [ ] Structure (current candles)
  - [ ] Liquidity (target pools, FVG, OB)
  - [ ] Setup (if present)
  - [ ] Risk calculation
  - [ ] Decision (COMPRAR / VENDER / AGUARDAR / SEM TRADE)

### 7.2 Trade Logging

- [ ] Manual log location: **logs/trades.md**
- [ ] Each logged trade includes:
  - [ ] Date/Time
  - [ ] Setup (from report)
  - [ ] Entry (price & time)
  - [ ] Exit (price, time, reason)
  - [ ] P&L (pips & %)
  - [ ] Notes (what went right/wrong)

### 7.3 Metadata Logging

- [ ] Structured log location: **logs/analyses.jsonl**
- [ ] Each line: one analysis (JSON, machine-readable)
- [ ] Includes: timestamp, symbol, decision, reason, risk, result

---

## Section 8: Demo vs Real Account

### 8.1 Testing Timeline

- [ ] Phase 0-5: Configuration, system building (no trading)
- [ ] Phase 6-8: Shadow trading (no real money, just logging ideas)
- [ ] Phase 8-9: **Demo account trading** (real execution, small risk)
  - [ ] Demo account opened? [ ] Yes, platform: ________________
  - [ ] Duration: [ ] 2-3 weeks  [ ] 4-6 weeks  [ ] Until 50+ trades

- [ ] Phase 10: **FTMO real challenge** (after demo validates edge)

### 8.2 Success Criteria (Shadow + Demo)

- [ ] Minimum setups logged: **50** or **4 weeks**, whichever is longer
- [ ] Winrate: **> 40%** (at least 4 wins per 10 trades)
- [ ] Expectancy: **> +1.5R** (average trade wins 1.5x the risk)
- [ ] Profit factor: **> 1.3** (gross profit / gross loss)
- [ ] Max drawdown: **< daily buffer** (e.g., < 3.5% for 5% limit)
- [ ] Max losing streak: **< max consecutive** (e.g., < 3 in a row)

---

## Section 9: Communication with Claude Code

### 9.1 CLAUDE.md Usage

- [ ] CLAUDE.md read and understood? [ ] Yes
- [ ] Key points:
  - [ ] Claude cites JSON fields (never guesses levels)
  - [ ] Claude respects validator.status (GO/BLOCKED)
  - [ ] Claude uses fixed report format
  - [ ] Claude can't change FTMO rules

### 9.2 System Architecture Understanding

- [ ] Flow understood (Python → JSON → Claude → Report)? [ ] Yes
- [ ] Separation of concerns:
  - [ ] Python: data + calculations + validation
  - [ ] Claude: interpretation + explanation + auditability
- [ ] JSON is source of truth? [ ] Yes

---

## Section 10: Final Sign-Off

### 10.1 All Decisions Locked In?

- [ ] All questions answered above? [ ] Yes
- [ ] Decisions documented? [ ] Yes
- [ ] config/account.yaml updated? [ ] Yes
- [ ] config/symbols.yaml updated? [ ] Yes
- [ ] .env created with credentials? [ ] Yes (add to .gitignore!)

### 10.2 Ready for Phase 1?

- [ ] Understand what Phase 1 builds (schemas, data contracts)? [ ] Yes
- [ ] Know where Phase 0 ends, Phase 1 begins? [ ] Yes
  - Phase 0: **Done now**
  - Phase 1: Start building Python schemas & models

### 10.3 Sign-Off

**Date Phase 0 Complete:** ________________

**What we're building:**
- System: ____________________
- Symbol(s): __________________
- Risk per trade: _____%
- Session: ________________
- Target: Complete FTMO **[1-Step / 2-Step]** with **_____%** profit

**First decision point:** After Phase 5 (end of Claude layer), can Claude analyze correctly?

---

## What's Next

Once all checkboxes above are [ ] checked:

1. **Commit Phase 0 answers** (document your decisions)
2. **Review README.md** for Phase 1 goals
3. **Start Phase 1** (Pydantic schemas, JSON contracts)
4. **Build incrementally** — don't skip phases

---

*Completion of Phase 0 is prerequisite for all subsequent phases. Do not proceed to Phase 1 until this checklist is 100% complete.*
