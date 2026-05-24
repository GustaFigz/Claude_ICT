# ICT Definitions — Exact Criteria

> Every term here is measured, not subjective. Python calculates these precisely.

---

## Price Structure

**Swing High:**
- A candle whose `high` exceeds:
  - The `high` of the N candles immediately to its left, AND
  - The `high` of the N candles immediately to its right
- N = 2 for intraday (M5, M15, H1), 3 for higher timeframes (H4, D1, W1)

**Swing Low:**
- A candle whose `low` is lower than:
  - The `low` of the N candles immediately to its left, AND
  - The `low` of the N candles immediately to its right
- N = same as Swing High

**Break of Structure (BOS) — continuation:**
- Price **close** (not wick) breaks the last swing **in the same direction as the prior bias**.
- `BOS_UP` = close > last swing high while prior bias was UP (or SIDEWAYS).
- `BOS_DOWN` = close < last swing low while prior bias was DOWN (or SIDEWAYS).
- Meaning: the existing trend is confirmed/extended.

**Change of Character (CHOCH) — reversal:**
- Price **close** breaks the last swing **against the prior bias** — the first structural sign of
  a trend change. More significant than a BOS; treat with caution until HTF confirms.
- `CHOCH_UP` = close > last swing high while prior bias was DOWN.
- `CHOCH_DOWN` = close < last swing low while prior bias was UP.
- *Engine:* `ict_engine/structure.py::_last_event` compares the close to the last swing and the
  previous bias (`_bias_from_swings(swings[:-1])`). The schema validates exactly these four values.

---

## Liquidity Structures

**Fair Value Gap (FVG):**
- Gap between candle N and candle N+2 where:
  - High[N+2] < Low[N] (bullish FVG), OR
  - Low[N+2] > High[N] (bearish FVG)
- Candle N+1 is neutral/indecisive
- FVG is **active** if not yet filled by price action
- **Size threshold:** FVG must be > 20% of average ATR on the timeframe
- *Engine:* `ict_engine/liquidity.py::detect_fvg` (3-candle gap) + `atr_pips`; the collector passes
  `min_pips = 0.20 * ATR` so sub-threshold noise is dropped before reaching the report.

**Liquidity Pool (BSL/SSL):**
- Concentration of equal highs or equal lows (tolerance: ±2 pips)
- **BSL (Buy Side Liquidity):** cluster of equal **highs ABOVE** the market. Buy stops (from
  shorts) and breakout buy orders rest here — price is drawn up to "grab" them.
- **SSL (Sell Side Liquidity):** cluster of equal **lows BELOW** the market. Sell stops (from
  longs) and breakout sell orders rest here — price is drawn down to "grab" them.
- **Validation:** Must have 2+ confluent points within tolerance
- *Engine:* `ict_engine/liquidity.py::detect_pools` — equal highs → BSL, equal lows → SSL.
  (Mnemonic: the side names where the *stops* are, not where price currently is.)

**Premium Zone:**
- Price range above the weekly/daily balance/equilibrium level
- Area where price typically corrects back into structure
- Not entry area; potential resistance

**Discount Zone:**
- Price range below the weekly/daily balance/equilibrium level
- Area where price typically rebounds into structure
- Not entry area; potential support

**Draw on Liquidity (DoL):**
- Direction of the next expected liquidity grab (toward BSL above or SSL below).
- *Engine:* `ict_engine/liquidity.py::compute_draw_direction` — the **nearest unswept pool** to the
  current price sets the immediate draw: nearest BSL above → `UP`, nearest SSL below → `DOWN`.
  Falls back to the structural bias when there are no qualifying pools.
- The draw **can diverge from HTF bias** (e.g. bias DOWN but price reaching up for BSL before
  continuing down). That divergence is signal, not error — surface it in the narrative.

---

## ICT Models (Phase 1 Focus: Silver Bullet)

**Silver Bullet (SB):**
- **Trigger:** NY AM session open (13:00-14:00 CEST)
- **Structure:** Kill Zone in NY with HTF bias alignment
- **Bias Check:**
  - Identify directional bias on D1 and H4
  - H1 must align with HTF direction
- **Liquidity Draw:**
  - First hour moves to grab one liquidity pool (BSL or SSL)
  - Must occur in designated SB time window
- **Entry:**
  - After DoL, price may reverse into structure
  - Entry on return to FVG, OB, or premium/discount zone
  - Stop below structure
  - Target = next liquidity pool or HTF resistance/support
- **Confluence minimum:** HTF bias + FVG/OB + session alignment = 3 factors

**Other Models (Phase 2+):**
- OB (Order Block) Mitigation
- Power of Three (PoT)
- Judas Swing (JS)
- Turtle Soup (TS)
- (Each adds when proven in shadow trading)

---

## Entry Models

**Optimal Trade Entry (OTE):**
- Entry at the exact point where probability is highest
- Typically at FVG fill, OB breach, or premium/discount re-entry
- Requires: BOS/CHOCH + FVG/OB confluence

**Order Block (OB) Entry:**
- Entry on retest/breach of order block after structure break
- OB = last strong candle before displacement
- Validity: Must not have been broken previously

**FVG Fill:**
- Entry when price fills (closes within) a Fair Value Gap
- Bias direction from bias confirmation
- Stop beyond opposite side of FVG

**Silver Bullet Entry (SB):**
- NY AM: price leaves zone, grabs liquidity, returns
- Entry on return candle or following candle with confirmation
- Higher probability if H1 aligns with D1/H4 bias

---

## Invalidation & Stops

**Technical Stop:**
- Stop placement that protects against the thesis being wrong
- Typically:
  - Short: above recent Swing High + 2 pips
  - Long: below recent Swing Low − 2 pips
- Must allow 20 pips minimum (worse case: wide market spreads)
- Must be > average spread on the pair

**Invalidation Level:**
- Price point that invalidates the entire setup
- Differs from stop: invalidation means "thesis broken," stop means "exit for loss"
- Stop should NOT be below invalidation for directional trades

**Trailing vs Fixed Stop:**
- Only fixed stops are acceptable for FTMO challenge
- No moving stops mid-trade
- No adjusting targets
- Discipline = exit at pre-defined levels only

---

## Confluence Scoring

A setup requires **minimum 3 confluency factors** to be considered valid:

- Bias alignment (HTF bias matches entry direction) — 1 factor
- Liquidity draw (DoL confirms direction) — 1 factor
- Structure (FVG, OB, BOS, CHOCH present) — 1 factor
- Session timing (Kill Zone, Silver Bullet window, etc.) — 1 factor
- Correlation support (DXY, other pairs don't conflict) — 1 factor

**Score < 3:** output `AGUARDAR` or `SEM TRADE`
**Score ≥ 3:** eligible for entry if risk/reward approved

---

## Risk Calculation

**Risk in Units (R):**
- R = (Entry − Stop) in pips × lot size (in micro-lots)
- Account risk = (Stop distance in pips) × lot size

**Reward in Units:**
- Reward = (Target − Entry) in pips × lot size

**Reward:Risk Ratio:**
- R:R = Reward ÷ Risk
- Minimum acceptable: 2R (you risk 1 to make 2)

**Position Size:**
- Lot size = (Account capital × risk_per_trade_pct) ÷ (Stop distance in pips × 10)
- Example: $100k account, 0.5% risk, 50 pip stop = 0.10 lots

**Margin Check:**
- Position must not require > max leverage allowed on account
- Typical: < 50:1 for FTMO

---

## Time & Kill Zones

**Kill Zone:**
- A specific timeframe window when a model is active
- Example: NY AM SB = 13:00-16:00 CEST
- Outside zone = NO entry

**Session Open:**
- Start of major trading session (NY, London, Asian, etc.)
- Each session has its own momentum pattern

**Session Bias:**
- Direction that each session typically trades initially
- Based on central bank actions, economic calendar, overnight news
- Informs silver bullet direction

**Macro ICT Timing:**
- Events that occur on monthly/quarterly timeframes
- Example: IPDA (Institutional Positioning Diagram Area)
- Adds confluence when aligned with micro (daily) setups

---

## Quality Checks

**Is this a true Swing High/Low?**
- Can I visually confirm it on the chart?
- Are there no adjacent candles higher/lower?
- Is it separated (not immediately adjacent to another)?

**Is this FVG real?**
- Can I see the gap with naked eye?
- Is it un-filled (price hasn't closed in it)?
- Is it > 20% ATR (not noise)?

**Is this OB valid?**
- Is it the last strong candle before the move?
- Was structure broken after it?
- Do I see a return/retest opportunity?

**Is confluence real?**
- Can I count 3+ factors from different categories?
- Would this setup work in hindsight too?

---

## Implementation Status (o que o engine realmente computa)

Para o relatório não alegar features inexistentes. Atualizar conforme o engine evolui.

**Implementado e usado nos setups:**
- Swings, bias por TF, BOS/CHOCH (`structure.py`)
- FVG com filtro ATR (`liquidity.py::detect_fvg` + `atr_pips`)
- Pools BSL/SSL com rótulos corretos (`detect_pools`)
- Draw on Liquidity pela proximidade dos pools (`compute_draw_direction`)
- Premium/Discount (`premium_discount`)
- Silver Bullet com validação de direção do target (`setups.py::build_silver_bullet`)
- **OTE** (Fibonacci 61.8–79% do displacement leg do H1) → `setups.py::_ote_zone`; entra como
  fator de confluência quando a entrada cai na banda (`ote_zone`, `entry_in_ote`)
- **Order Blocks na confluência**: OB não-mitigado do tipo certo que contém a entrada soma fator
- **Liquidity Sweep confirmation**: `setups.py::_sweep_confirmed` (LONG varre SSL, SHORT varre BSL)
  → `sweep_confirmed` + fator de confluência
- Validação de risco/FTMO e gate do validator (`risk.py`, `validator.py`)

**Planejado (Fase D restante — confiança live ainda gated em shadow trading; ver plano):**
- Breaker Blocks (OB mitigado que inverte de papel)
- Multi-target exits (T1=CE do FVG, T2=próximo pool, T3=extremo do range HTF)
- OB mitigation/anchoring explícito ao BOS/CHOCH mais recente (hoje a detecção é por displacement)

---

*These definitions are law. If Python can't calculate it or you can't see it in hindsight, it's not in the system.*
