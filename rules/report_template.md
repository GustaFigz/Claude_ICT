# Report Template

> Use this structure for every report. Fill blanks from JSON, don't improvise.

---

## Header

```markdown
# ICT Analysis Report

**Data:** [from context.created_at_utc]
**Symbol:** [from context.symbol]
**Analyst:** Claude Code (ICT Engine)
**Status:** [GO / BLOCKED]

---
```

## If BLOCKED

```markdown
## Bloqueio

Motivo Principal:
- [from validator_result.validator_failures[0]]

Detalhes:
- [from validator_result.description]

Contexto:
- Sessão: [from session_state.session_name]
- Hora: [from context.created_at_utc in NY time]
- Dados Frescos: [timestamp check]
- Calendário: [from news_state.events_next_48h or "Clear"]

---

Próximo Evento Viável:
- [from session_state.next_kill_zone or session_state.next_window]

---
```

## If GO

### Market Bias

```markdown
## 1. Viés do Mercado (HTF)

**Tendência Principal (D1):**
- Direção: [from structure.bias_d1 - UP, DOWN, or SIDEWAYS]
- Suporte: [from structure.d1_support_zone]
- Resistência: [from structure.d1_resistance_zone]

**Tendência H4:**
- Direção: [from structure.bias_h4 - UP, DOWN, or SIDEWAYS]
- Estrutura: [BOS/CHOCH/MSS status if present]

**Alinhamento H1 com HTF:**
- H1 está em linha com D1/H4: YES / NO
- [Validation note if misaligned]

---
```

### Market Structure

```markdown
## 2. Estrutura de Mercado

**Swings Recentes (D1):**
- Último Swing Alto: [from levels.d1_last_swing_high_price] @ [candle]
- Último Swing Baixo: [from levels.d1_last_swing_low_price] @ [candle]

**Estrutura Ativa (H4):**
- [BOS / CHOCH / MSS / None] - [description from structure]
- Implicação: [directional bias]

**Estrutura H1:**
- [Current formation]

---
```

### Liquidity & Targets

```markdown
## 3. Liquidez e Alvos

**Liquidez Alvo (próximas 48h):**
- Tipo: [BSL (Buy Side) / SSL (Sell Side)]
- Localização: [level]
- Distância: [pips or %]

**Fair Value Gaps Ativos:**
- [If any FVG present, describe]

**Order Blocks Válidos:**
- [If any OB present, describe]

**Premium / Discount:**
- Zona Premium (acima do equilíbrio): [price range]
- Zona Discount (abaixo do equilíbrio): [price range]
- Preço atual em: [which zone]

---
```

### Session Context

```markdown
## 4. Contexto da Sessão

**Kill Zone Ativa:**
- Nome: [from session_state.active_session]
- Horário: [start - end in CEST]
- Tempo até início: [if upcoming]
- Modelo Típico: [Silver Bullet / PoT / JS / etc.]

**Calendário Económico:**
- Próximas 90 min: [Clear / [Event Name] @ time - Impact]
- Próximas 24h: [List high/medium impact events]
- Moedas Afetadas: [Base/Quote]

**Contexto Macro:**
- [DXY direction if relevant]
- [Other major pair movements]
- [Any central bank news/speeches]

---
```

### Setup (If Candidate Exists)

```markdown
## 5. Setup Candidato

**Modelo:** [from setup_candidate.model]
**Direção:** [LONG / SHORT]

**Confluência:**
1. [Factor 1 - name & source]
2. [Factor 2 - name & source]
3. [Factor 3 - name & source]
*Score: [N/5] — [Minimum 3 required]*

**Entrada:**
- Nível: [from setup_candidate.entry_level]
- Tipo: [FVG Fill / OB Retest / SB Return / etc.]
- Validação: [Must see candle close at level or momentum confirmation]

**Stop:**
- Nível: [from setup_candidate.stop]
- Distância: [N pips]
- Invalidação: [What happens if this breaks]

**Alvo(s):**
- Alvo 1: [from setup_candidate.targets[0]]
- Alvo 2: [from setup_candidate.targets[1], if present]
- *R:R Ratio: [from risk_calculation.reward_risk]*

---
```

### Risk Management

```markdown
## 6. Gestão de Risco

**Dimensionamento da Posição:**
- Capital em Risco: [from risk_calculation.risk_units]% da conta
- Lote Sugerido: [from risk_calculation.lot_size]
- Risco em R: [from risk_calculation.r_value] R

**Limites da Conta (FTMO):**
- P&L Diário Atual: [from account_snapshot.daily_pnl_pct]%
- Margem para Limite Diário: [from ftmo_limits.daily_margin_pct]%
- Drawdown Acumulado: [from account_snapshot.drawdown_pct]%
- Margem para Limite Total: [from ftmo_limits.total_margin_pct]%

**Risco da Trade:**
- Risco: [N pips] × [lot size] = [R units]
- Recompensa: [N pips] × [lot size] = [R × 2 or more]
- Aprovado: YES [if RR ≥ 2R]

**Restrições:**
- [Max consecutive losses today: 1 remaining / OK]
- [Max trades today: 2 remaining / OK]
- [Correlations: No conflicts / Conflict with PAIR]

---
```

### Final Validation

```markdown
## 7. Validação Final

**Verificações:**
- ✓ Dados validados e frescos (< 5 min)
- ✓ Risco FTMO dentro dos limites
- ✓ Sessão ativa e viável
- ✓ Confluência ≥ 3 fatores
- ✓ R:R ≥ 2:1
- ✓ Stop técnico respeitado
- ✓ Sem conflitos de correlação

**Decisão:** [COMPRAR / VENDER / AGUARDAR / SEM TRADE]

---
```

### Decision & Notes

```markdown
## 8. Decisão Final

**COMPRAR**
*Tome posição LONG com os parâmetros acima. Confirme a entrada no gráfico antes de executar.*

**VENDER**
*Tome posição SHORT com os parâmetros acima. Confirme a entrada no gráfico antes de executar.*

**AGUARDAR**
*Nenhum setup válido neste momento. Próxima Kill Zone: [time]. Revisite então.*

**SEM TRADE**
*Condições inadequadas. Motivo: [list]. Não há trade hoje neste ativo.*

---

**Notas:**
- [Anything not covered above, max 2-3 sentences]
- [Edge case handling or caution]
- [Reminder: always confirm visual on chart before execution]

---

**Relatório Gerado:** [timestamp]
**Próxima Análise Recomendada:** [next window or "6h"]

---
```

---

## Notes on Structure

- Every claim cites a JSON field
- Every number is from Python, not guessed
- Every recommendation is checked against FTMO rules
- No jargon without definition in same sentence
- Numbers before adjectives
- Decision first, details second
