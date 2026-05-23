# PROJECT_STATE — Ponto de Retoma

> Save point único do projeto. Ler **isto primeiro** em cada sessão.
> Última atualização: **2026-05-24**.

---

## 1. O que é o projeto

Sistema de análise ICT para FTMO Challenge, a correr no Claude Code CLI. Python recolhe dados e
calcula tudo de forma determinística → JSON validado → Claude interpreta e gera relatório, **sem
inventar níveis nem ignorar bloqueios**. Execução manual.

**Ordem de leitura:** este ficheiro → `ANALISE_CRITICA_E_PLANO.md` (spec + roadmap) → `rules/`.
`ICT_System_Project_v2.md` é a visão original (contexto histórico).

---

## 2. Estado atual — CÓDIGO IMPLEMENTADO E TESTADO

Motor determinístico construído e a correr **offline** (`data_mode=fixtures`). **25 testes passam.**
O CLI corre end-to-end: `python -m cli.main analyze EURUSD --now 2026-05-26T14:30 --trend up`.

**Módulos:**
- `data_pipeline/schemas.py` — contratos Pydantic; o JSON do Claude é um `AnalysisContext`.
- `data_pipeline/market_clock.py` — timezones/Kill Zones + rollover FTMO (zoneinfo, DST).
- `data_pipeline/fixtures.py` — candles sintéticas (corre sem MT5/OANDA).
- `data_pipeline/collector.py` — orquestra o motor → `AnalysisContext`.
- `data_pipeline/{mt5_client,oanda_client,news_client}.py` — clientes live (a LIGAR depois).
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

- [ ] **Ligar dados live:** instalar terminal MT5 + `pip install MetaTrader5`; criar `.env` com chave
  OANDA; mudar `account.yaml: data_mode` para `mt5`/`oanda`; ligar `collector` aos clientes.
- [ ] **NAS100: confirmar `broker_symbol` e `pip_value_per_lot`** contra o broker real (o sizing
  depende disto; em `config/symbols.yaml` está como placeholder a VERIFICAR).
- [ ] **Live data quality:** implementar freshness (<5 min) e divergência MT5×OANDA no collector
  (hoje o `DataQuality` é preenchido como fresh em modo fixtures).
- [ ] **ForexFactory:** normalizar timezone do feed para UTC antes do blackout; juntar 2ª fonte
  (risco de fonte única, ANALISE_CRITICA §3.5).
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

## 6. Próximo passo (ponto de retoma)

1. **Ligar dados live** (ver §4, primeiro item) e correr `analyze` contra MT5/OANDA; validar o JSON
   contra o gráfico numa amostra.
2. **Confirmar contrato do NAS100** (símbolo + valor por ponto) antes de qualquer sizing real.
3. **Iniciar shadow (Fase 8):** correr nas janelas NY AM, registar em `logs/` e comparar com o
   gráfico; afinar regras (não resultados).

> Teste de retoma: ler este ficheiro + `ANALISE_CRITICA_E_PLANO.md` basta para continuar.
> Correr o que existe: `python -m pytest -q` e `python -m cli.main analyze EURUSD --now <ISO> --trend up`.
