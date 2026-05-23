# Execution Policy — FTMO Rules Engine

> These are the hard stops. If ANY condition fails, output is always SEM TRADE.

---

## 1. Data Quality Gates

**Freshness:**
- Data older than 5 minutes: BLOCKED
- Incomplete current candle: excluded from analysis
- Missing any required timeframe: BLOCKED

**Source Agreement:**
- MT5 vs OANDA price divergence > 0.5% (by symbol): BLOCKED
- Both sources unavailable: BLOCKED

**Metadata:**
- Account equity readable: required
- Current session identifiable: required
- Time zone consistent (UTC, NY, broker): required

---

## 2. Economic Calendar Gates

**High-Impact News Blackout:**
- If ANY high-impact event in next 90 minutes: BLOCKED
  - Base currency of pair (EUR, GBP, USD, JPY, etc.)
  - Secondary currency if different
  - Major indices (DXY, SPX, Treasuries) if relevant
  - Central Bank speeches if classified high-impact

**News State:**
- Calendar must load successfully
- Time must normalize to CEST/CE(S)T correctly
- If feed fails twice in session: BLOCKED for remainder

---

## 3. Account Risk Gates (FTMO)

**Daily Loss:**
- Daily P&L (closed + floating): may not exceed `daily_buffer_pct`
- Calculation includes: closed trades + unrealized P&L + swap + commission
- Timestamp: broker's daily rollover time (usually 00:00 CET)
- If reached: BLOCKED all trades for rest of day

**Total Loss:**
- Total cumulative loss from account start: may not exceed `max_total_buffer_pct`
- Includes all drawdowns in account lifetime
- If reached: account fails challenge

**Margin to Limit:**
- Remaining space = limit − current_loss
- If space < 1 position minimum: BLOCKED

**Consecutive Losses:**
- If N consecutive losing trades in current day: BLOCKED for rest of day
- Resets at next daily rollover

---

## 4. Session & Timing Gates

**Valid Trading Sessions:**
- Only during defined windows per symbol (e.g., NY AM 13:00-16:00 CEST)
- Outside window: output `AGUARDAR` (wait for next window), not `SEM TRADE`

**Kill Zone Timing:**
- Setup must occur within valid Kill Zone
- If outside: output `AGUARDAR`

**Macro ICT Timing:**
- If active macro like Judas Swing or Power of Three: confirm alignment
- Misalignment doesn't block, but reduces confidence

---

## 5. Setup Quality Gates

**Confluence Minimum:**
- Setup candidate must have ≥ 3 ICT confluency factors
- If < 3: BLOCKED (insufficient setup)

**Risk:Reward Ratio:**
- Minimum: 2R (2 units of reward per 1 unit of risk)
- If RR < 2R: output `SEM TRADE` with reason

**Position Size:**
- Risk amount = account_capital × risk_per_trade_pct
- Stop distance must fit account constraints
- If required lot size is 0 (stop too tight) or > max lot: BLOCKED

**Entry Proximity:**
- Entry must not be >20% inside invalidation level
- Entry must allow min stop distance without breach

---

## 6. Correlation Gates

**Conflicting Positions:**
- No overlapping trades in correlated pairs
- Example: Can't hold both EURUSD and GBPUSD in same direction
- If position exists and new setup correlated: BLOCKED

**DXY Alignment:**
- If setup is USD sell, DXY must not be in severe uptrend
- If setup is USD buy, DXY must not be in severe downtrend
- Misalignment doesn't block strong setup but noted as caution

---

## 7. Output Decision Tree

```
Start: Is validator.status == GO?
  ├─ NO → Output: SEM TRADE + reason
  └─ YES
      ├─ Account risk violated?
      │  ├─ YES → SEM TRADE
      │  └─ NO
      │      ├─ Session valid (timing)?
      │      │  ├─ NO → AGUARDAR (next window)
      │      │  └─ YES
      │      │      ├─ Setup candidate exists?
      │      │      │  ├─ NO → AGUARDAR (no setup)
      │      │      │  └─ YES
      │      │      │      ├─ All gates passed?
      │      │      │      │  ├─ NO → SEM TRADE + reason
      │      │      │      │  └─ YES → COMPRAR or VENDER (with full analysis)
```

---

## 8. BLOCKED vs AGUARDAR

**BLOCKED (SEM TRADE):**
- Data invalid
- News high-impact close
- Account risk violated
- Setup does not meet confluence/RR
- Position conflicts
- Risk/reward impossible to achieve

**AGUARDAR (not now, try later):**
- Outside valid session window (wait for next Kill Zone)
- No setup candidate yet
- Insufficient confluence (wait for better alignment)
- News clearing in < 30 min (wait for safe passage)

**COMPRAR/VENDER (execute):**
- All gates passed
- Setup meets all criteria
- Risk fits account limits
- Confluence ≥ 3
- Entry, stop, targets clear and validatable

---

*This policy is law. If in doubt, BLOCK. A missed setup is acceptable; wrong execution is not.*
