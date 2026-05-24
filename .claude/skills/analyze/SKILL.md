# Skill: /analyze — ICT Live Analysis Runner

## Overview

This skill automates the complete analysis workflow:
1. Extract symbol from user request (EURUSD or NAS100)
2. Infer trend bias from conversation context
3. Run CLI: `python -m cli.main analyze <SYMBOL> --trend <trend>`
4. Parse JSON path from stdout
5. Read JSON context file
6. Generate report per CLAUDE.md format

**Goal:** User writes "analisa EURUSD" → Claude handles everything automatically, no manual JSON copying.

---

## STEP 1: Extract Symbol

Read the user's message and identify which symbol to analyze.

**Symbol mapping (case-insensitive):**
- "EURUSD", "euro", "eur/usd", "eurusd", "eur" → **EURUSD**
- "NAS100", "nas100", "nasdaq", "nas", "nas 100", "nasdaq 100" → **NAS100**

**Logic:**
- If the message clearly contains one symbol → use it
- If message contains BOTH symbols → analyze both in sequence (one after another), labeling each clearly
- If no symbol is identifiable → ask the user: "Qual símbolo? EURUSD ou NAS100?"

---

## STEP 2: Infer Trend Bias

The `--trend` parameter only affects **fixture mode** (synthetic candles). In live mode (MT5/OANDA) it is ignored. Always pass it for uniformity.

**Inference logic (from conversation context):**
- If user's message or recent conversation contains: "baixa", "bearish", "down", "short", "vender", "sell" (case-insensitive) → **trend = `down`**
- Otherwise → **trend = `up`** (default)

**Explicit override:**
- If user's message contains "trend down" or "trend up" explicitly → use that value

---

## STEP 3: Run the CLI

Use the **Bash** tool to execute:

```bash
cd C:\Users\Gusta\Documents\ICT && python -m cli.main analyze <SYMBOL> --trend <trend>
```

**Important rules:**
- Always run from `C:\Users\Gusta\Documents\ICT` (the project root)
- Do NOT add `--now` unless user explicitly specifies a time
- Do NOT modify the command otherwise
- Capture FULL stdout output
- If command exits with non-zero code → print stderr + stdout → STOP and report error to user

---

## STEP 4: Extract JSON Path from stdout

The CLI's last line has this exact format:
```
  context JSON  : context\<run_id>.json
```

Where `<run_id>` is a 12-character hex string (e.g., `7e2dfc50c7ea`).

**Parsing logic:**
1. Look for the line starting with `  context JSON  :`
2. Extract everything after the colon and space: `context\<run_id>.json` (relative path)
3. Convert to absolute path by prepending `C:\Users\Gusta\Documents\ICT\`: 
   ```
   C:\Users\Gusta\Documents\ICT\context\<run_id>.json
   ```

If no such line is found in stdout → report error and stop.

---

## STEP 5: Read the JSON File

Use the **Read** tool with the absolute path from STEP 4.

The JSON will be a complete `AnalysisContext` object with these top-level fields:
- `run_id`, `created_at_utc`, `symbol`
- `data_quality`, `account_snapshot`, `ftmo_limits`
- `session_state`, `news_state`
- `structure` (by timeframe D1/H4/H1 with bias and swings)
- `liquidity` (pools, target, zones)
- `setup_candidates` (array, usually 1 element)
- `risk_calculation` (risk units, reward/risk ratio)
- `validator_result` (status: GO or BLOCKED, failures, decision)

If file does not exist → report error and stop.

---

## STEP 6: Generate the Report (Análise ICT com Pré-Filtros)

The report is an **ICT analysis**, not a field dump. Run the pre-filters first, then write a
market narrative, then the structured sections. See `CLAUDE.md` → "Interpretação ICT" for the
meaning of each concept. All numbers still come from the JSON — never invent levels.

### STEP 6.0 — Pré-Filtros (rodar ANTES de escrever o relatório)

These catch engine inconsistencies and noise before they reach the trader.

**Filtro 1 — Direção do target (engine sanity):**
For `setup_candidates[0]` (if present): LONG must have `targets[0] > entry_level`; SHORT must have
`targets[0] < entry_level`. The engine (A5) already rejects bad setups, so if you ever see a
violation, output **SEM TRADE** with reason "Inconsistência do engine: target na direção errada"
and stop.

**Filtro 2 — Qualidade dos FVGs:** From `structure.fvg_active[]`, treat gaps with `size_pips < 5`
as noise. The engine already applies an ATR filter (A4), so list what remains, ordered by
proximity to current price (H1 close). If the list is empty, say "Nenhum FVG válido".

**Filtro 3 — Convergência de bias:** Compare `structure.by_tf.D1/H4/H1.bias`. If all equal → strong.
If H1 diverges from D1/H4 (e.g. H1 CHOCH_UP under D1/H4 DOWN) → flag "Estrutura em transição —
aguardar confirmação do H4 antes de operar a favor do H1".

**Filtro 4 — Diversidade de confluência (5 categorias ICT):** Map `confluence_factors[]` +
context into these UNIQUE buckets and count coverage (max 5):
- **[Bias]** HTF bias alinhado (D1/H4/H1)
- **[Structure]** evento BOS/CHOCH recente (`last_event`)
- **[Liquidity]** FVG/OB válido na zona de entrada
- **[Session]** Kill Zone / janela Silver Bullet ativa
- **[DoL]** `liquidity.draw_direction` casa com a direção do setup

Minimum viable = 3 categorias. Note that the engine's `confluence_score` counts raw factors, which
may differ from category coverage — report both if they diverge.

### Verificação imediata: status do validator

- `validator_result.status == BLOCKED` → "Relatório BLOCKED" abaixo, e PARE.
- `validator_result.status == GO` → "Relatório Completo" abaixo.

### Relatório BLOCKED

```
DECISÃO: SEM TRADE

Bloqueador:
- [validator_result.failures[0] — explique em linguagem de trader]

Contexto:
- Sessão: [session_state.active_session] | Próxima janela: [session_state.next_window]
- Notícias: [se news_state.blackout: blackout_reason; senão "sem blackout"]
- Risco: [ftmo_limits.daily_margin_pct]% diário / [ftmo_limits.total_margin_pct]% total
- Dados: source=[data_quality.source], fresh=[data_quality.fresh]
```
**Pare. Não analise setup nem confluência.**

### Relatório Completo (GO)

```
DECISÃO: [COMPRAR | VENDER | AGUARDAR]

Narrativa de Mercado:
[1 parágrafo: bias HTF + último evento estrutural + preço em premium/discount do dealing range +
draw on liquidity (para onde o mercado está sendo puxado) + qualquer divergência HTF vs LTF.
Diga o que o mercado está TENTANDO fazer, não só os números.]

Estrutura Multi-Timeframe:
- D1: [bias] | [last_event interpretado: ex "BOS_DOWN = baixa confirmada, rompeu o swing low"] | range [last_swing_low]–[last_swing_high]
- H4: [idem]
- H1: [idem; se diverge do HTF, explique a implicação]

Premium / Discount:
- Equilíbrio (50% do range D1): [liquidity.equilibrium]
- Preço atual (H1 close) em: [Premium se > eq | Discount se < eq | Equilíbrio]
- Implicação: [ex "Discount + bias UP = zona de compra preferencial"]

Liquidez e Draw on Liquidity:
- Draw: [liquidity.draw_direction] → buscando [BSL se UP | SSL se DOWN]
- Target do bias: [liquidity.target]
- BSL (equal highs, acima): [pools kind=BSL com price + touches; senão "nenhum"]
- SSL (equal lows, abaixo): [pools kind=SSL com price + touches; senão "nenhum"]

FVGs Válidos (após filtro, ordenados por proximidade):
- [top]–[bottom] ([size_pips] pips) [bullish/bearish]
[se nenhum: "Nenhum FVG válido"]

Confluência ICT (categorias):
- [Bias] [✓/✗ + nota]
- [Structure] [✓/✗ + last_event]
- [Liquidity] [✓/✗ + FVG/OB]
- [Session] [✓/✗ + sessão]
- [DoL] [✓/✗ + draw vs direção]
Cobertura: [N]/5 categorias  (engine confluence_score: [setup_candidates[0].confluence_score])
[se < 3: "⚠️ Confluência fraca"]

Setup [se setup_candidates não vazio]:
- Modelo: [model] | Direção: [direction]
- Entrada: [entry_level]  (FVG da zona mais próxima)
- Stop: [stop]  ([risk_calculation.stop_pips] pips)
- Alvo: [targets[0]]  ([risk_calculation.reward_pips] pips)
- R:R: [risk_calculation.reward_risk]  [✓ ≥ 2R | ✗ < 2R]
[se vazio: "Sem setup válido no momento"]

Risco FTMO:
- Conta: $[account_snapshot.balance] | Equity: $[account_snapshot.equity] | PnL hoje: [daily_pnl_pct]%
- Drawdown: [account_snapshot.drawdown_pct]%
- Margem: [ftmo_limits.daily_margin_pct]% diário / [ftmo_limits.total_margin_pct]% total
- Tamanho: [risk_calculation.lot_size] lote | Risco: $[risk_calculation.risk_amount] ([risk_pct]%)

Calendário (próximas 48h — High/Medium; Low só se ≤ 2h):
[para cada evento relevante: horário UTC, moeda, impacto, título]
[se blackout: "⚠️ BLACKOUT: [blackout_reason]"]

Validação:
- Dados: source=[data_quality.source] | fresh=[data_quality.age_seconds]s | MT5×OANDA div=[max_divergence_pct]%
- Target válido: ✓ | FVGs: [N] válidos | Confluência: [N]/5
- Decisão final: [COMPRAR/VENDER/AGUARDAR/SEM TRADE]

Próximas Ações:
- Se COMPRAR/VENDER: nível de invalidação = [swing que quebra a tese]; gatilho de entrada = [ex retração ao FVG]
- Se AGUARDAR: o que precisa acontecer + próxima janela ([session_state.next_window])
```

**Regras críticas:**
- **Todo número vem do JSON** — cite o campo quando útil; nunca invente preços/níveis/risco.
- **Não ignore confluence_factors** — mapeie todos para as 5 categorias.
- **Campo ausente / array vazio** → escreva "nenhum"/"N/A", não pule a linha.
- **A narrativa é obrigatória** — é o que diferencia análise de preenchimento de formulário.

---

## Summary of Field References (Quick Lookup)

| Report Section | JSON Path |
|---|---|
| Decision | `setup_candidates[0].direction` (LONG→COMPRAR, SHORT→VENDER) |
| HTF Bias | `structure.bias_d1_h4_h1` |
| D1 Structure | `structure.by_tf.D1.bias`, `.last_event`, `.last_swing_high/low` |
| H4 Structure | `structure.by_tf.H4.*` (same fields) |
| H1 Structure | `structure.by_tf.H1.*` (same fields) |
| FVG | `structure.fvg_active[]` (array of objects with `kind`, `top`, `bottom`, `size_pips`) |
| Bias Target | `liquidity.target` |
| Pools | `liquidity.pools[]` (array) |
| Session | `session_state.active_session`, `.in_entry_window`, `.in_kill_zone` |
| News | `news_state.events_next_48h[]`, `.blackout` |
| Model | `setup_candidates[0].model` |
| Entry | `setup_candidates[0].entry_level` |
| Stop | `setup_candidates[0].stop` |
| Targets | `setup_candidates[0].targets[]` |
| Confluence | `setup_candidates[0].confluence_factors[]`, `.confluence_score` |
| R:R | `risk_calculation.reward_risk` |
| Stop/Reward pips | `risk_calculation.stop_pips`, `.reward_pips` |
| Lot / Risk $ / Risk % | `risk_calculation.lot_size`, `.risk_amount`, `.risk_pct` |
| Setup approved | `risk_calculation.approved`, `.reason` |
| Draw Direction | `liquidity.draw_direction`, `liquidity.equilibrium` |
| Premium/Discount | `liquidity.premium_zone`, `liquidity.discount_zone` |
| Drawdown | `account_snapshot.drawdown_pct` |
| Daily Margin | `ftmo_limits.daily_margin_pct` |
| Total Margin | `ftmo_limits.total_margin_pct` |
| Validator Status | `validator_result.status` (GO or BLOCKED) |
| Failures | `validator_result.failures[]` (array of reason strings) |

---

## Notes & Constraints

- This skill works in both **fixture mode** (offline, no credentials) and **live mode** (MT5/OANDA after setup)
- The CLI determines the data source from `config/account.yaml` → `data_mode` field
  - `data_mode: "fixtures"` → synthetic candles (test mode)
  - `data_mode: "mt5"` → live MT5 data (requires terminal + credentials)
  - `data_mode: "oanda"` → live OANDA data (requires API key)
- The `--trend` parameter only affects fixture mode; it is safe and harmless to always pass it
- **Do NOT run tests before the CLI** — unnecessary overhead, the suite already passes
- **Do NOT ask the user to copy/paste JSON** — always read directly via Read tool
- **Do NOT skip the CLI step** — even if a recent context JSON exists, re-run the CLI to get fresh data
- The skill operates in Portuguese context (report is in Portuguese, but accepts English user input for triggers)

---

## Example Execution (EURUSD, GO Status)

**User input:** "analisa EURUSD"

**Skill execution:**
1. Symbol: EURUSD ✓
2. Trend: up (default) ✓
3. Bash: `cd C:\Users\Gusta\Documents\ICT && python -m cli.main analyze EURUSD --trend up`
4. Capture stdout → find last line → extract `context\<run_id>.json`
5. Read: `C:\Users\Gusta\Documents\ICT\context\<run_id>.json`
6. Check `validator_result.status`: GO ✓
7. Generate full report citing each field

**Example output (truncated):**
```
DECISÃO: COMPRAR

HTF Bias: UP

Estrutura de Mercado:
- D1: bias UP, last_swing_high 1.0983, last_swing_low 1.0917
- H4: bias UP, last_swing_high 1.0983, last_swing_low 1.0917
- H1: bias UP, last_swing_high 1.1033, last_swing_low 1.0967

... [rest of report]
```

---

**This skill is the entry point for all analysis requests. Always invoke it when the user asks to analyze a symbol.**
