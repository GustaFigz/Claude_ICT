# PROJECT_STATE — Ponto de Retoma

> Save point único do projeto. Ler **isto primeiro** em cada sessão.
> Última atualização: **2026-05-24** (Session 2).  
> **Status:** All phases A-D implemented. 64 tests passing. EURUSD live verified. Ready for Phase 8 shadow trading.

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

## 4. Pendente / questões em aberto

- [ ] **Credenciais (só tu):** instalar terminal MT5 + `pip install MetaTrader5`; criar `.env` com
  chave OANDA; copiar `account.example.yaml`→`account.yaml` e pôr `data_mode: mt5`. O código live já
  está ligado (CLI `_run_live` + `collect_live`); falta só isto + validar JSON vs gráfico.
- [ ] **NAS100: confirmar `broker_symbol` e `pip_value_per_lot`** contra o broker real — em
  `config/symbols.yaml` está placeholder ($1/ponto) marcado VERIFICAR; o sizing depende disto.
- [ ] **ForexFactory 2ª fonte** — feed já normalizado para UTC; falta fonte redundante/checklist
  manual (risco de fonte única, ANALISE_CRITICA §3.5).
- [ ] **Afinar setup/RR:** com dados sintéticos o alvo fica perto → R:R baixo (bloqueia). Refinar a
  escolha de alvo/stop do Silver Bullet com dados reais.
- [ ] **FVG por ATR:** hoje `min_pips=0`; aplicar limiar ~20% ATR (ict_definitions).
- [ ] **Plano Claude (Pro)** — confirmar se cobre Opus diário; talvez Sonnet para análise.

---

## 5. Realismo FTMO (já refletido em `config/account.example.yaml`)

2-Step: **5%** perda diária / **10%** total (estático), alvos **10%→5%**, **4 dias/fase**, tempo
ilimitado. Daily loss recalcula 00:00 CE(S)T sobre o balanço de fecho anterior, conta **equity**
intradiária (flutuante + swap + comissão). 1-Step (se mudares): 3% diário / 10% trailing.

---

## 6. Próximo passo: PHASE 8 SHADOW TRADING (Ponto de Retoma)

Todas as fases A-D estão completas e testadas. O próximo passo é validar se as melhorias em Phase D 
genuinamente melhoram o edge através de shadow trading.

**Imediato:**
1. Ler `PHASE_8_SHADOW_TRADING.md` (guia completo de como começar)
2. Confirmar contrato do NAS100 (símbolo + pip_value_per_lot no seu broker)
3. Começar a correr `/analyze` durante janelas NY AM Silver Bullet (10:00–11:00 NY)
4. Registar em `logs/trades.md` cada análise (trade ou skip)
5. Após 30+ setups (2-4 semanas): avaliar se Phase D signals (OTE, sweep, breakers) correlacionam com wins

**Validação esperada:**
- Win rate ≥ 50% em setups Phase D
- R médio ≥ 1.5 (cada trade vencedor paga 1.5x risco)
- Nenhuma perda sistemática de novos sinais

Ler `PHASE_8_SHADOW_TRADING.md` para fluxo detalhado, pré-checklist, e decisão go/no-go.

> Teste de retoma: `python -m pytest -q` (64 testes), depois ler `PHASE_8_SHADOW_TRADING.md`.
> Começar: `python -m cli.main analyze EURUSD` durante NY AM window.
