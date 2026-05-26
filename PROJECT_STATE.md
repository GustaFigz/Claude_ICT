# PROJECT_STATE — Ponto de Retoma

> Save point único do projeto. Ler **isto primeiro** em cada sessão.
> Última atualização: **2026-05-26** (Session 5 — Sprint 1 complete).  
> **Status:** Phases A-D + Phase 9 + Sprint 1 bug fixes complete. **72 tests passing**. 4 silent bugs fixed, 5 values configurable, CLAUDE.md updated.

---

## 1. O que é o projeto

Sistema de análise ICT para FTMO Challenge, a correr no Claude Code CLI. Python recolhe dados e
calcula tudo de forma determinística → JSON validado → Claude interpreta e gera relatório, **sem
inventar níveis nem ignorar bloqueios**. Execução manual.

**Ordem de leitura:** este ficheiro → `ANALISE_CRITICA_E_PLANO.md` (spec + roadmap) → `rules/`.
`ICT_System_Project_v2.md` é a visão original (contexto histórico).

---

## 2. Estado atual — CÓDIGO IMPLEMENTADO E TESTADO (TODAS AS FASES A-D)

Motor determinístico construído e **testado com 64 testes passando**. Todas as fases A-D implementadas:
- **Fase A (bugs ICT):** ✓ BSL/SSL labels, CHOCH/BOS logic, draw_direction computation, FVG ATR filter, target validation
- **Fase B (news resiliente):** ✓ Fail-safe blackout, Trading Economics fallback, retry+backoff, post-event window
- **Fase C (Claude análise):** ✓ Relatório narrativo com pré-filtros, 5 categorias confluência, SKILL.md reescrito
- **Fase D (ICT avançado):** ✓ OTE (Fib retracement), Order Blocks confluência, Sweep confirmation, Breakers, Multi-target (T1/T2/T3)

CLI corre end-to-end: `python -m cli.main analyze EURUSD` (MT5 live) ou `python -m cli.main analyze EURUSD --trend up` (fixtures).
O caminho **live** (`collect_live`, por injeção de dependências) testado com fakes e ligado ao CLI — basta meter credenciais e mudar `data_mode` para `mt5`/`oanda`.

**Módulos:**
- `data_pipeline/schemas.py` — contratos Pydantic; o JSON do Claude é um `AnalysisContext`.
- `data_pipeline/market_clock.py` — timezones/Kill Zones + rollover FTMO (zoneinfo, DST).
- `data_pipeline/fixtures.py` — candles sintéticas (corre sem MT5/OANDA).
- `data_pipeline/collector.py` — `build_context` (motor → `AnalysisContext`) + `collect_live`
  (caminho live por injeção: liga quality+news; testado com fakes).
- `data_pipeline/{mt5_client,oanda_client,news_client}.py` — clientes live (a LIGAR depois);
  `news_client` já normaliza data/hora FF → UTC e calcula blackout (testado offline).
- `data_pipeline/quality.py` — freshness + divergência MT5×OANDA (testado; falta LIGAR ao collector live).
- `data_pipeline/audit.py` — regista cada análise em `logs/analyses.jsonl`.
- `ict_engine/{swings,structure,liquidity,setups,risk,validator}.py` — cálculo ICT + FTMO + decisão.
- `cli/main.py` — comando `analyze`; escreve `context/<run_id>.json` e log de auditoria.
- `tests/` — swings, structure, liquidity, risk/FTMO, setup, validator, market_clock, schemas.

**Mapa de fases (do `ANALISE_CRITICA_E_PLANO.md`):**
Fase 0 (decisões) ✓ · Fase 1 (schemas) ✓ · Fase 2 (clientes dados: escritos, **live por ligar**) ·
Fase 3 (cálculos ICT) ✓ testado · Fase 4 (risk/FTMO) ✓ testado · Fase 5 (validator) ✓ testado ·
Fase 6 (camada Claude: `CLAUDE.md` + `rules/`) ✓ pronta · Fase 7 (logger) ✓ ·
Fases 8–10 (shadow → demo → FTMO real) — **operacionais, dependem de dados live + trading**.

---

## 3. Decisões tomadas (log)

- **2026-05-24 — Parâmetros (escolha do trader):** FTMO **2-Step**, capital **$10.000**, risco/trade
  **0.50%**, foco **EURUSD + NAS100**, modelo **NY AM Silver Bullet (10:00–11:00 NY)**.
  Sessões definidas (Londres/NY AM/NY PM) em `config/sessions.yaml`.
- **2026-05-24 — Construir primeiro com fixtures/sintético**, ligar MT5/OANDA depois (MT5 não está
  instalado nesta máquina). *Porquê:* não bloquear o motor por falta de terminal/credenciais.
- **2026-05-24 — Consolidação documental + git** (ver histórico git e [[feedback-docs-consolidation]]).
- **Princípios bloqueados:** Python calcula / Claude interpreta · proteção antes de lucro · JSON é a
  verdade · demo antes de FTMO (≥50 setups ou 4 semanas) · um modelo primeiro.

---

## 4. Sprint 1 — Bugs Críticos + Testes + Docs (✓ Concluído 2026-05-26)

**4 bugs silenciosos corrigidos:**
- ✓ `liquidity.py::_mark_filled()` → FVG filled por CLOSE não wick (ICT correto)
- ✓ `setups.py::_OTE_DEEP` → 0.786 em vez de 0.79 (Fibonacci 78.6% correto)
- ✓ `swings.py::detect_swings()` → `elif` impede mesmo candle como swing high+low
- ✓ `risk.py::evaluate_risk()` → `balance=0` hard-fails em vez de fallback silencioso

**5 valores configuráveis via YAML** (defaults iguais = comportamento inalterado):
- `fvg_atr_multiplier`, `stop_buffer_pips`, `pool_tol_pips`, `news_post_event_minutes`, `candle_counts`

**8 novos testes:** 64 → **72 passando**

**CLAUDE.md atualizado:** thresholds Phase 9 corretos (`min_confluence=2`, warn zone 1.5-2.0, `news_blackout=60min`)

---

## 4b. Novo em Phase 9 — Relaxação de Regras (✓ Implementado)

**2026-05-26 — Rule Relaxation Complete:**
- ✓ `min_confluence` configurável via YAML (era hardcoded 3, agora padrão 2)
- ✓ R:R warn zone (1.5–2.0) → AGUARDAR em vez de BLOCKED
- ✓ `max_consecutive_losses` 2 → 3 (1.5% max loss, não 1.0%)
- ✓ `news_blackout_minutes` 90 → 60 para EURUSD/NZDUSD
- ✓ Setups visíveis mesmo quando AGUARDAR (novo campo `setup_preview`)
- ✓ `.env` preparado com Trading Economics free tier (`guest:guest`)
- ✓ Todas as mudanças backward-compatible: 64 testes continuam passando

**Implicação:** Sistema agora mostra oportunidades (mesmo marginais) sem sacrificar proteção FTMO.

## 5. Próximo — Sprint 2 (Engine + Qualidade)

Itens de maior impacto por ordem de prioridade:
- [ ] **S2-10: Consolidar CLAUDE.md** (~228 → ~110 linhas, -600-800 tokens/sessão)
- [ ] **S2-9: Validação de config ao carregar** (fail-fast se YAML inválido)
- [ ] **S2-4: Lot sizing dinâmico por drawdown** (escala risco quando conta está em DD)
- [ ] S2-6: Reason codes standardizados no validator (`FailureCode` enum)
- [ ] S2-3: Confirmação multi-candle BOS/CHOCH (`confirm_closes: int`)
- [ ] S2-1: Filtro de distância mínima de swings (`min_swing_pips`)

---

## 5b. Pendente / questões em aberto

- [ ] **MT5 Credenciais (só tu):** instalar terminal MT5 + `pip install MetaTrader5` se necessário;
  preencher `account.yaml`: `MT5_ACCOUNT`, `MT5_PASSWORD`, `MT5_SERVER`; mudar `data_mode: "fixtures"` → `"mt5"`.
  Sistema live já está wired (CLI `_run_live` + `collect_live`); falta só credenciais + testar JSON vs gráfico.
- [ ] **NAS100: confirmar `broker_symbol` e `pip_value_per_lot`** no MT5 — em
  `config/symbols.yaml` está placeholder verificado; confirmar se broker usa `US100.cash` ou `USTEC` ou outro.
- [ ] **OANDA API key (opcional):** se quiser quality check MT5×OANDA, preencher `OANDA_API_KEY` em `.env`.
- [ ] **Phase 8 Log:** começar a preencher `logs/trades.md` durante NY AM (10:00–11:00 ET) com setups reais.

---

## 5. Realismo FTMO (já refletido em `config/account.example.yaml`)

2-Step: **5%** perda diária / **10%** total (estático), alvos **10%→5%**, **4 dias/fase**, tempo
ilimitado. Daily loss recalcula 00:00 CE(S)T sobre o balanço de fecho anterior, conta **equity**
intradiária (flutuante + swap + comissão). 1-Step (se mudares): 3% diário / 10% trailing.

---

## 6. PHASE 8 SHADOW TRADING — Em Progresso

**Status:** Sistema relaxado, documentação pronta, primeiro teste executado com sucesso.

### Checklist de Retoma (para próxima sessão):

- [x] Phases A-D implementadas e testadas (64 testes ✓)
- [x] Phase 9 (rule relaxation) implementada e testada (64 testes ✓)
- [x] `account.yaml` ajustado: `min_confluence=2`, `min_rr_ratio_warn=1.5`, `max_consecutive_losses=3`
- [x] `.env` preparado com Trading Economics (`guest:guest`)
- [x] Primeiro `/analyze EURUSD` executado com sucesso (teste de fixture)
- [ ] **Próximo:** MT5 credenciais (quando terminal instalado)
- [ ] Começar logs em `logs/trades.md` durante NY AM (10:00–11:00 ET)
- [ ] Após 15–20 setups: preencher `PHASE_8_SHADOW_TRADING_RESULTS.md`
- [ ] Após 30+ setups (2–4 semanas): avaliar correlação Phase D signals ↔ wins

### Como Começar Phase 8

**Diariamente durante NY AM (10:00–11:00 ET):**
```bash
python -m cli.main analyze EURUSD    # (ou NAS100 se broker symbol confirmado)
# Claude gera relatório
# Você decide: COMPRAR / VENDER / AGUARDAR / SEM TRADE
# Log em logs/trades.md: | data | run_id | symbol | model | dir | entry | stop | target | exit | result | notes |
```

**Setup esperado para Phase 8:**
1. Sistema em mode `fixtures` (até MT5 estar pronto) — OK ✓
2. Dados sintetizados com trend bias — OK ✓
3. Relatórios ICT com confluence + R:R visível — OK ✓
4. Setups marginais agora aparecem como AGUARDAR — OK ✓

> **Teste rápido de retoma:**  
> ```bash
> python -m pytest -q                     # confirma 64 testes
> python -m cli.main analyze EURUSD       # confirma CLI funcional
> ```
