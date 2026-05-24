# Report Template — ICT Analysis

> **Fonte canônica do formato:** `.claude/skills/analyze/SKILL.md` → STEP 6.
> Este arquivo é a referência rápida dos campos reais do JSON (`AnalysisContext`) e da
> estrutura narrativa. Todo número vem do JSON; nada é improvisado.

---

## Fluxo

1. **Pré-filtros** (SKILL.md 6.0): direção do target, qualidade dos FVGs, convergência de bias,
   diversidade de confluência (5 categorias ICT).
2. **Status do validator** (`validator_result.status`): `BLOCKED` → relatório curto e PARE;
   `GO` → relatório completo.

---

## Se BLOCKED

```
DECISÃO: SEM TRADE

Bloqueador:
- [validator_result.failures[0] em linguagem de trader]

Contexto:
- Sessão: [session_state.active_session] | Próxima: [session_state.next_window]
- Notícias: [news_state.blackout_reason se blackout, senão "sem blackout"]
- Risco: [ftmo_limits.daily_margin_pct]% diário / [ftmo_limits.total_margin_pct]% total
- Dados: source=[data_quality.source], fresh=[data_quality.fresh]
```

---

## Se GO

Seções, em ordem (detalhe completo em SKILL.md STEP 6):

1. **DECISÃO** — COMPRAR / VENDER / AGUARDAR
2. **Narrativa de Mercado** — 1 parágrafo: bias HTF + último evento + premium/discount + draw on
   liquidity + divergências. O que o mercado está tentando fazer.
3. **Estrutura Multi-Timeframe** — D1/H4/H1: `bias`, `last_event` interpretado, range de swings.
4. **Premium / Discount** — `liquidity.equilibrium`, zona do preço atual, implicação.
5. **Liquidez e Draw** — `draw_direction`, `target`, pools BSL (acima) / SSL (abaixo).
6. **FVGs Válidos** — `fvg_active[]` ordenados por proximidade (já filtrados por ATR).
7. **Confluência ICT** — 5 categorias [Bias][Structure][Liquidity][Session][DoL], cobertura N/5.
8. **Setup** — `setup_candidates[0]`: model, direction, entry, stop, target, R:R.
9. **Risco FTMO** — `account_snapshot` + `ftmo_limits` + `risk_calculation`.
10. **Calendário** — `news_state.events_next_48h[]` (High/Medium; Low só se ≤ 2h).
11. **Validação** — data quality, target válido, confluência, decisão final.
12. **Próximas Ações** — invalidação + gatilho, ou o que aguardar.

---

## Mapa de Campos Reais (schema `AnalysisContext`)

| Conceito | Campo JSON |
|---|---|
| Status / decisão / falhas | `validator_result.status`, `.decision`, `.failures[]`, `.description` |
| Bias HTF | `structure.bias_d1_h4_h1` |
| Estrutura por TF | `structure.by_tf.{D1,H4,H1}.bias`, `.last_event`, `.last_swing_high`, `.last_swing_low` |
| FVGs | `structure.fvg_active[]` (`kind`, `top`, `bottom`, `size_pips`, `filled`) |
| Draw / equilíbrio | `liquidity.draw_direction`, `liquidity.equilibrium` |
| Premium/Discount | `liquidity.premium_zone`, `liquidity.discount_zone` |
| Pools | `liquidity.pools[]` (`kind` BSL/SSL, `price`, `touches`), `liquidity.target` |
| Setup | `setup_candidates[0]` (`model`, `direction`, `entry_level`, `stop`, `targets[]`, `confluence_factors[]`, `confluence_score`) |
| Risco | `risk_calculation` (`reward_risk`, `stop_pips`, `reward_pips`, `lot_size`, `risk_amount`, `risk_pct`, `approved`, `reason`) |
| Conta | `account_snapshot` (`balance`, `equity`, `daily_pnl_pct`, `drawdown_pct`) |
| Limites FTMO | `ftmo_limits.daily_margin_pct`, `.total_margin_pct` |
| Sessão | `session_state.active_session`, `.in_entry_window`, `.in_kill_zone`, `.next_window` |
| Notícias | `news_state.events_next_48h[]`, `.blackout`, `.blackout_reason` |
| Dados | `data_quality.source`, `.fresh`, `.age_seconds`, `.max_divergence_pct` |

---

## Regras

- Todo número vem do JSON (Python calcula, Claude interpreta).
- A narrativa é obrigatória — diferencia análise de preenchimento de formulário.
- Campo ausente/array vazio → "nenhum"/"N/A", nunca pular a linha.
- Conceitos ICT: ver `rules/ict_definitions.md` e CLAUDE.md → "Interpretação ICT".
