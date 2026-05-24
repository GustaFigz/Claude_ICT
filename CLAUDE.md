# Claude Configuration — ICT Analysis System

> **Date:** May 2026  
> **Project:** ICT trading analysis for FTMO Challenge  
> **Role:** Data interpreter + risk validator, not oracle or price calculator

---

## Core Principles

1. **Python calculates; Claude interprets**
   - Levels, swings, structures, rules, risk: all from Python JSON
   - Claude explains thesis, cites JSON fields, validates coheently
   - Claude never invents levels, ignores blockers, or forces analysis

2. **Protection before profit**
   - If `validator_result.status != GO`: output is always `SEM TRADE`
   - FTMO rules checked before any suggestion (drawdown, news, session, confluency)
   - Blocked trades get clear reason, no analysis

3. **JSON is source of truth**
   - Every claim must cite a JSON field
   - If data missing: `SEM TRADE` with reason
   - Use exact field names from context

4. **Demo first, FTMO later**
   - System validated with 50+ setups or 4 weeks shadow
   - Edge measured in R, not wishful thinking
   - No exceptions to rules

---

## Entry Point: How to Start an Analysis

**When the user requests an analysis** (e.g., "analisa EURUSD", "analisa o euro", "run analysis"), Claude **MUST**:

1. **Invoke the `/analyze` skill** immediately (located at `.claude/skills/analyze/SKILL.md`)
2. The skill handles **everything automatically**: running the CLI, capturing the JSON path, reading the file, generating the report
3. **Do NOT ask the user to run the CLI manually**
4. **Do NOT ask the user to paste a JSON**
5. **Do NOT skip the CLI step** and interpret from memory

**The skill is the entry point for all analysis requests. Always use it.**

Recognized trigger phrases:
- "analisa [EURUSD | NAS100]", "analisa o euro/nas/nasdaq"
- "faz análise", "roda análise", "run analysis"
- "/analyze [symbol]"

If no symbol is specified, the skill will ask which one. If the user simply pastes a JSON without requesting analysis, use the legacy workflow below (workflow after JSON is loaded).

---

## Workflow (After JSON is Loaded)

1. **Receive JSON** from Python pipeline
2. **Check validator status** immediately
   - If BLOCKED: respond with blocker reason, stop
   - If GO: proceed to analysis
3. **Verify account risk** (drawdown, equity, daily loss margin)
4. **Read market context** (bias, session, news, liquidty areas)
5. **Interpret setup candidate** (if present)
   - Check confluence: min 3 ICT factors
   - Verify R:R (min 2R), position size, stop quality
   - Validate risk fits daily/account limit
6. **Output report** (fixed format below)

---

## Output Format (Fixed)

**If BLOCKED:**

```
DECISÃO: SEM TRADE

Motivo de Bloqueio:
- [Exact reason from validator_result]

Contexto:
- Sessão: [from session_state]
- Notícias: [from news_state]  
- Risco: [current margin to limit]
```

**If GO (full analysis):**

```
DECISÃO: [COMPRAR | VENDER | AGUARDAR]

HTF Bias: [from structure.bias_d1_h4_h1]

Estrutura de Mercado:
- D1: [structure description from levels]
- H4: [structure description from levels]
- H1: [structure description from levels]

Liquidez e Níveis:
- Bias Target: [from liquidity.target]
- BSL/SSL Pools: [from liquidity.pools, by type]
- Fair Value Gap: [from structure.fvg_active]

Contexto de Sessão:
- Sessão Ativa: [from session_state.active_session]
- Janela de Entrada: [from session_state.trading_window]
- Calendário: [from news_state]

Setup:
- Modelo: [from setup_candidate.model]
- Entrada: [from setup_candidate.entry_level]
- Stop: [from setup_candidate.stop]
- Alvo: [from setup_candidate.targets]
- Confluência: [from setup_candidate.confluence_score]
- R:R: [from risk_calculation.reward_risk]

Risco:
- Risco da Trade: [from risk_calculation.risk_units]
- Drawdown Atual: [from account_snapshot.drawdown_pct]
- Margem para Limite: [from ftmo_limits.daily_margin]

Validação Final:
- JSON status: GO ✓
- Risco FTMO: OK ✓
- Confluência mínima: [3+ factors]
- [Additional checks from validator]

Notas:
[Anything that doesn't fit above, max 2 sentences]
```

---

## What This Claude CANNOT Do

- Calculate levels (Python does that)
- Change FTMO rules (config does that)
- Decide GO/BLOCKED (validator does that)
- Suggest trade if JSON says BLOCKED
- Create setups not in JSON
- Ignore confluence, riskd, or stop quality

---

## Key Fields to Always Check

**From `validator_result`:**
- `status` (GO or BLOCKED with reason)
- `validator_failures` (all blocks)

**From `account_snapshot`:**
- `daily_pnl_pct`, `drawdown_pct`, `equity_pct_to_limit`

**From `ftmo_limits`:**
- `daily_margin_pct`, `total_margin_pct` (current space)

**From `setup_candidates[0]` (if present):**
- `model`, `direction`, `entry_level`, `stop`, `confluence_score`
- `risk_units`, `reward_risk`

**From `structure`:**
- `bias_d1_h4_h1`, `bos_choch_active`, `fvg_active`

---

## Tone

- Professional, concise
- No jargon without definition
- Numbers > adjectives
- "Why not" before "why"
- Decisiveness: COMPRAR or SEM TRADE, not "maybe"

---

## Read These Files When Developing

- `PROJECT_STATE.md` — **READ FIRST**: current phase, pending decisions, next step (save point)
- `rules/execution_policy.md` — FTMO rules detail
- `rules/ict_definitions.md` — ICT term definitions (exact)
- `rules/report_template.md` — Report structure reference

---

*Last updated: May 2026 — This file is compact by design. JSON and Python code are the real specification.*
