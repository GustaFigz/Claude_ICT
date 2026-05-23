# ICT Analysis System — FTMO Challenge

Ferramenta de análise de trading que corre no **Claude Code CLI**. O Python recolhe dados e
calcula tudo de forma determinística (níveis ICT, risco, regras FTMO) e produz um JSON validado.
O Claude lê o JSON, explica a tese e gera o relatório — **nunca inventa níveis nem ignora
bloqueios**. A execução do trade é sempre manual.

> Princípio central: **Python calcula, Claude interpreta.** Proteção antes de lucro.
> Sem dados validados não há análise; sem análise não há trade.

## Estado atual

**Fase 0** (escopo e configuração) — ainda sem código Python. Ver `PROJECT_STATE.md` para o estado
exato, decisões pendentes e o próximo passo.

## Por onde começar (ordem de leitura)

1. **`PROJECT_STATE.md`** — ponto de retoma: em que fase está, o que falta decidir, próximo passo.
2. **`ANALISE_CRITICA_E_PLANO.md`** — especificação autoritativa: arquitetura + roadmap de 10 fases.
3. **`ICT_System_Project_v2.md`** — visão original (contexto histórico do "porquê").
4. **`CLAUDE.md`** — como o Claude se comporta nas análises.
5. **`rules/`** — `execution_policy.md` (regras FTMO), `ict_definitions.md` (definições exatas),
   `report_template.md` (formato do relatório).

## Fluxo previsto (quando construído)

```
python -m cli.main analyze EURUSD --model silver-bullet
  → coleta MT5 + OANDA + calendário  → normaliza/valida
  → calcula níveis e setup candidato → risk engine → validator (GO/BLOCKED)
  → context/<run_id>.json            → Claude lê e produz relatório → reports/
```

## Configuração

- `config/account.example.yaml` → copiar para `config/account.yaml` e preencher (gitignored).
- `config/symbols.yaml` → símbolos a analisar.
- `.env.example` → copiar para `.env` com credenciais MT5/OANDA (gitignored).

## Stack

Python (Windows, por causa da lib `metatrader5`) · MT5 + OANDA v20 + ForexFactory · Claude Code CLI.
