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

## STEP 6: Generate the Report

Follow **exactly** the workflow defined in the project `CLAUDE.md`:

### Immediate Check: Validator Status

Read `validator_result.status`:
- If `BLOCKED` → go to "BLOCKED Report" section below
- If `GO` → go to "Full Analysis Report" section below

### BLOCKED Report

Output this format:
```
DECISÃO: SEM TRADE

Motivo de Bloqueio:
- [Exact reason from validator_result.failures array]

Contexto:
- Sessão: [from session_state.active_session]
- Notícias: [from news_state.blackout status]
- Risco: [from ftmo_limits.daily_margin_pct] / [from ftmo_limits.total_margin_pct]
```

**Then stop. Do NOT analyze setup or confluence.**

### Full Analysis Report (GO status)

Output this exact structure:

```
DECISÃO: [COMPRAR | VENDER | AGUARDAR]

HTF Bias: [from structure.bias_d1_h4_h1]

Estrutura de Mercado:
- D1: [read structure.by_tf.D1 — describe bias and last event/swings]
- H4: [read structure.by_tf.H4]
- H1: [read structure.by_tf.H1]

Liquidez e Níveis:
- Bias Target: [from liquidity.target]
- BSL/SSL Pools: [from liquidity.pools if array is non-empty, describe by type; if empty say "None identified"]
- Fair Value Gap: [from structure.fvg_active — list active FVGs with size_pips and kind]

Contexto de Sessão:
- Sessão Ativa: [from session_state.active_session]
- Janela de Entrada: [from session_state.in_entry_window — "Yes" or "No"]
- Calendário: [from news_state.events_next_48h — list events or "No events"]

Setup:
- Modelo: [from setup_candidates[0].model]
- Entrada: [from setup_candidates[0].entry_level]
- Stop: [from setup_candidates[0].stop]
- Alvo: [from setup_candidates[0].targets — join array with commas]
- Confluência: [from setup_candidates[0].confluence_factors — list each factor]
- Confluência Score: [from setup_candidates[0].confluence_score]
- R:R: [from risk_calculation.reward_risk]

Risco:
- Risco da Trade: [from risk_calculation.risk_units] R
- Drawdown Atual: [from account_snapshot.drawdown_pct]%
- Margem para Limite: [from ftmo_limits.daily_margin_pct]% diário / [from ftmo_limits.total_margin_pct]% total

Validação Final:
- JSON status: [from validator_result.status] ✓
- Risco FTMO: OK ✓
- Confluência mínima: [from setup_candidates[0].confluence_score] factors ✓
- [Any additional checks from validator_result.description]

Notas:
[Optional: add any critical context that doesn't fit above — max 2 sentences]
```

**Critical rules for report generation:**
- **EVERY number cited must reference its JSON field name** (e.g., "Entrada: 1.0993 (from setup_candidates[0].entry_level)")
- **Do NOT invent prices, levels, or risk values** not in the JSON
- **Do NOT ignore confluence factors** — list all from `confluence_factors` array
- **If a field is missing or array is empty** (e.g., no liquidity.pools) → state "None identified" or similar, do NOT skip the line
- **Use exact field values** — no rounding, no adjustments

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
| Risk Units | `risk_calculation.risk_units` |
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
- **Do NOT run tests before the CLI** — unnecessary overhead, the 35 tests already pass
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
