# ICT Analysis System for FTMO Challenge

> A professional trading analysis tool that runs in Claude Code CLI, supporting FTMO Challenge attempts through systematic ICT analysis, strict risk management, and complete auditability.

---

## Quick Start

### 1. Read the Foundation (First)

```bash
# Read these documents IN ORDER to understand the project:
1. ICT_System_Project_v2.md       — Original vision and principles
2. ANALISE_CRITICA_E_PLANO.md     — Critical analysis + implementation roadmap
3. This README                     — How to use the system
```

### 2. Complete Phase 0 (Configuration)

```bash
# Edit these configuration files with YOUR account details:
cp config/account.example.yaml config/account.yaml
cp config/symbols.yaml config/symbols.yaml  # Select 1-3 symbols to focus on
cp .env.example .env                        # Add MT5 and OANDA credentials
```

**What you decide in Phase 0:**
- FTMO account type (1-Step or 2-Step)
- Initial capital and daily/total loss limits
- Risk per trade (typically 0.25% - 0.50%)
- Trading timezone and session windows
- Which 1-3 symbols to focus on
- Which ICT model to implement first (recommend: NY AM Silver Bullet)

### 3. Review Key Rules

```bash
# These files define how the system works:
CLAUDE.md                         — How Claude Code behaves (compact, essential)
rules/execution_policy.md         — FTMO rules and decision gates
rules/ict_definitions.md          — Exact ICT term definitions (measurable)
rules/report_template.md          — Report structure (always the same)
```

### 4. Project Structure

```
ICT/
├── CLAUDE.md                     ← Claude's instructions (already configured)
├── .env.example                  ← Credential template
├── .gitignore                    ← (Add: .env, context/, reports/, logs/)
│
├── config/
│   ├── account.example.yaml      ← COPY to account.yaml, fill in values
│   ├── symbols.yaml              ← Choose trading symbols
│   └── ...                        ← (risk.yaml, sessions.yaml added in Phase 3)
│
├── rules/
│   ├── execution_policy.md       ← FTMO rules and gates
│   ├── ict_definitions.md        ← ICT definitions (exact)
│   └── report_template.md        ← Report format (fixed)
│
├── data_pipeline/                ← (Python, built in Phase 2)
│   ├── collector.py              ← Collects MT5 + OANDA data
│   ├── validator.py              ← Checks data quality + FTMO rules
│   └── calculator.py             ← Computes ICT levels
│
├── ict_engine/                   ← (Python, built in Phase 3)
│   ├── swings.py                 ← Swing high/low calculation
│   ├── structure.py              ← BOS, CHOCH, structure analysis
│   ├── liquidity.py              ← FVG, OB, pools
│   └── setups.py                 ← Setup candidate generation
│
├── context/                      ← (Auto-generated, .gitignore)
│   └── *.json                    ← Analysis context for each run
│
├── reports/                      ← (Auto-generated, .gitignore)
│   └── *.md                      ← Analysis reports with timestamp
│
└── logs/
    ├── trades.md                 ← Manual log: your executed trades + results
    └── analyses.jsonl            ← Structured analysis metadata (Phase 7)
```

---

## How the System Works

### Typical Workflow (Once Fully Built)

```bash
# 1. Trader opens terminal and runs:
python -m cli analyze EURUSD --model silver-bullet

# 2. System automatically:
#    a. Loads account config (risk limits, account state)
#    b. Collects fresh OHLCV from MT5 and OANDA
#    c. Fetches economic calendar for next 48h
#    d. Validates data (freshness, agreement between sources)
#    e. Validates account state (drawdown, margin, daily loss)
#    f. Calculates all ICT levels and potential setups
#    g. Runs FTMO rules engine (blocker check)
#    h. Generates JSON context file with all decisions
#
# 3. If JSON says BLOCKED:
#    - Claude reads JSON
#    - Outputs short blocker report
#    - System stops
#
# 4. If JSON says GO:
#    - Claude reads JSON
#    - Applies ICT rules (must cite JSON fields)
#    - Produces full analysis report
#    - Saves report to reports/ with timestamp
#
# 5. Trader:
#    - Reads report
#    - Opens chart in MT5
#    - Confirms analysis matches chart
#    - Executes trade ONLY if conviction matches
#    - Records trade in logs/trades.md with result
```

---

## Development Phases

### Phase 0: Scope & Configuration (Week 1)
- [ ] Choose 1-3 symbols (recommend: EURUSD initially)
- [ ] Choose FTMO type (1-Step or 2-Step)
- [ ] Define all risk parameters (daily loss, position size, etc.)
- [ ] Set trading timezone (NY, London, etc.) and session windows
- [ ] Choose first ICT model to implement (recommend: NY AM Silver Bullet)
- [ ] Create config/ files with your values
- **Criteria:** System can answer: "What do we trade, when, how much risk, when to stop?"

### Phase 1: Schema & Data Contracts (Week 1-2)
- [ ] Create Pydantic models for: candles, events, account state, levels, setups
- [ ] Define JSON schema that ALL data must follow
- [ ] Create test fixtures with known data
- [ ] Create validation: invalid JSON fails before Claude sees it
- **Criteria:** JSON structure is enforced; no garbage data gets through

### Phase 2: Data Collection (Week 2)
- [ ] Build MT5 connector (robustly)
- [ ] Build OANDA connector (secondary validation)
- [ ] Build economic calendar fetcher
- [ ] Build timezone normalization (critical: DST handling)
- [ ] Remove incomplete current candle from analysis
- [ ] Test: For each symbol, generate consistent candles across all timeframes
- **Criteria:** You can trace: raw MT5 data → normalized candles → JSON

### Phase 3: ICT Calculations (Week 3)
- [ ] Implement swing high/low (testable, visual on chart)
- [ ] Implement Fair Value Gap (exact definition from rules/ict_definitions.md)
- [ ] Implement Order Blocks (with validation rules)
- [ ] Implement liquidity pools (BSL/SSL)
- [ ] Implement structure (BOS/CHOCH/MSS)
- [ ] Implement first model's setup candidate generator (e.g., Silver Bullet)
- [ ] Test: All calculated levels match manual chart analysis
- **Criteria:** Every level is verifiable on a chart in hindsight

### Phase 4: FTMO Rules & Risk (Week 4)
- [ ] Implement daily loss calculation (exact FTMO timestamp)
- [ ] Implement total drawdown tracking
- [ ] Implement position sizing (risk % → lot size)
- [ ] Implement blocker checks (news, session, confluency, RR)
- [ ] Implement validator: GO / BLOCKED + reason
- [ ] Test: Rules prevent forbidden trades, allow valid ones
- **Criteria:** System always protects account before suggesting trades

### Phase 5: Claude Layer (Week 4-5)
- [ ] CLAUDE.md already prepared (see CLAUDE.md file)
- [ ] Verify Claude cites JSON fields (never invents levels)
- [ ] Verify Claude respects GO/BLOCKED decision
- [ ] Test: Claude output always includes all required sections
- [ ] Create short blocker reports (template provided)
- [ ] Create full GO reports (template provided)
- **Criteria:** Claude can't make up rules or create setups outside JSON

### Phase 6: Logging & Auditability (Week 5)
- [ ] Save reports to reports/ with timestamp
- [ ] Save JSON context to context/ for each run
- [ ] Create logs/trades.md (manual: trade idea + result)
- [ ] Create logs/analyses.jsonl (structured: all analysis metadata)
- [ ] Build audit trail: can you replay any trade decision?
- **Criteria:** Every trade is reconstructible: data → decision → result

### Phase 7-8: Shadow Trading (Weeks 6-9)
- [ ] Run system live during chosen session windows
- [ ] Record setups in logs/trades.md (whether taken or not)
- [ ] Track: winrate, expectancy (in R), profit factor, max drawdown, max losing streak
- [ ] Separate results by: symbol, session, model
- [ ] Look for false positives (setups that fail) and adjust rules, NOT results
- [ ] Minimum: 50 setups or 4 weeks shadow (whichever is later)
- **Criteria:** Edge is measurable and positive; no overfitting to hindsight

### Phase 9: Demo Execution (Week 10+)
- [ ] Open small demo account (if not already)
- [ ] Trade ONLY setups marked GO by system
- [ ] Use 0.25% - 0.50% position size (smaller than planned FTMO)
- [ ] Never break rules manually (no averaging down, moving stops, etc.)
- [ ] Record discipline metrics: ignored signals, manual deviations, entrySlips
- [ ] Review weekly: Why did we deviate? Can we fix it in code?
- **Criteria:** Trader can follow system without emotional override

### Phase 10: FTMO Real (Week 11+)
- [ ] Start with 1-Step Challenge
- [ ] Use 0.25% - 0.50% position size (conservative start)
- [ ] Stop after N losses or hitting daily buffer (defined in config)
- [ ] Don't increase until shadow + demo prove consistency
- [ ] Measure: Can we pass 1-Step? Can we pass 2-Step?
- **Criteria:** Account survives challenge; probability increases with data

---

## Key Decisions (Phase 0 — Before Code Starts)

Fill these in before you write any Python:

```yaml
# Account
FTMO Challenge Type: [ ] 1-Step   [ ] 2-Step
Initial Capital: $______
Daily Loss Limit: __% (official) → ___% (buffer)
Total Loss Limit: __% (official) → ___% (buffer)

# Trading
Primary Symbol: EURUSD / GBPUSD / USDJPY (choose 1 initially)
Secondary Symbols: _____ (optional)
Session: NY AM / London / Asian (choose 1 initially)
Time Zone: America/New_York (or your reference)
Trading Window: HH:MM - HH:MM (CEST/NY)

# Risk per Trade
Default Risk %: [ ] 0.25%  [ ] 0.50%  [ ] Other: ___%
Max Risk per Trade: ___%
Min R:R Ratio: [ ] 2:1  [ ] 3:1  [ ] Other
Max Consecutive Losses per Day: [ ] 1  [ ] 2  [ ] Other

# ICT Model (Phase 1)
First Model: [X] NY AM Silver Bullet  [ ] Other: _____
Confluence Minimum: [ ] 3 factors  [ ] 4 factors
Timeframes: MN, W1, D1, H4, H1, M15, M5, M1

# Data Sources
MT5 Account: [broker] / Account#: [____]
OANDA Demo: [Account ID] / [API Key stored in .env]
Economic Calendar: ForexFactory (public, no auth)
```

---

## Important Notes

### Do NOT do this in Phase 0-1:
- Don't start coding Python yet (Phase 0-1 is planning)
- Don't start CLAUDE.md (it's ready)
- Don't trade on real account yet (phases 6-9 first)
- Don't assume your edge is proven (it needs data)

### Do this first:
- Answer the Phase 0 questions above
- Read the critical analysis document
- Understand the phasing plan
- Plan which ICT model to start with (recommend: Silver Bullet)

### Resources:
- `ICT_System_Project_v2.md` — Complete original vision
- `ANALISE_CRITICA_E_PLANO.md` — Realistic roadmap + all critiques
- `CLAUDE.md` — How Claude behaves (read completely)
- `rules/execution_policy.md` — FTMO rules (law of the system)
- `rules/ict_definitions.md` — ICT term definitions (exact)

---

## FAQ

**Q: When do I start writing Python code?**
A: After Phase 0 is complete (scope defined) and Phase 1 (schema designed). Not before.

**Q: Why not use the complete ICT methodology in Phase 1?**
A: Too many degrees of freedom = too much room for bias in Claude's analysis. Start with 1 model (Silver Bullet), measure its edge, then add others.

**Q: Why require 50 setups or 4 weeks shadow trading?**
A: Because 2-3 weeks might not cover different market conditions. You need statistical significance and real-world testing before risking FTMO capital.

**Q: What if my symbol is XYZ, not EURUSD?**
A: Update config/symbols.yaml, make sure MT5 has the symbol, get OANDA equivalent, update data sources. System supports any forex pair.

**Q: Can I use this on other assets (crypto, stocks)?**
A: Not yet. System is designed for forex (MT5 + OANDA). Crypto/stocks would need different data sources and risk models. Possible in future.

**Q: Where do I check if an analysis was right?**
A: logs/trades.md (manual) and logs/analyses.jsonl (structured). Compare report → entry → exit → P&L.

---

## Getting Help

- If CLAUDE.md seems unclear: re-read it. It's dense intentionally.
- If a Python phase blocks you: check ANALISE_CRITICA_E_PLANO.md for that phase's full spec.
- If you need to customize rules: update rules/*.md and CLAUDE.md, then test thoroughly.

---

## Commitment

Building this system properly takes 10+ weeks. This is not a shortcut to trading. It's a systematic, measurable, auditable approach to reducing trading bias through automation and strict rules.

The goal is not to predict markets. It's to follow a process, measure the edge of that process, and only take the risks that the data justifies.

**Start with Phase 0. Answer the questions. Then come back.**

---

*Last updated: May 2026*
