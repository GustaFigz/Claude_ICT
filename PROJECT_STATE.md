# PROJECT_STATE — Ponto de Retoma

> Save point único do projeto. Ler **isto primeiro** em cada sessão.
> Última atualização: **2026-05-24**.

---

## 1. O que é o projeto

Sistema de análise ICT para FTMO Challenge, a correr no Claude Code CLI. Python recolhe dados
(MT5 + OANDA + ForexFactory) e calcula tudo de forma determinística → JSON validado → Claude
interpreta e gera relatório, **sem inventar níveis nem ignorar bloqueios**. Execução manual.

**Ordem de leitura:** este ficheiro → `ANALISE_CRITICA_E_PLANO.md` (spec autoritativa + roadmap)
→ `rules/` (regras FTMO, definições ICT, template). `ICT_System_Project_v2.md` é a visão original
(contexto histórico). O roadmap detalhado **não** é repetido aqui — vive na análise crítica (secções
4, 6, 7).

---

## 2. Estado atual

- **Fase 0** (escopo e configuração) — por fechar.
- **Código Python: inexistente.** Ainda não há `data_pipeline/`, `ict_engine/`, `cli/`, `tests/`.
- Documentação **consolidada** em 2026-05-24 (ver decisões abaixo).
- Repositório **git** inicializado nesta data (commits locais, sem remoto).

---

## 3. Decisões tomadas (log)

- **2026-05-24 — Consolidação documental.** Apagados 4 `.md` redundantes (`NEXT_STEPS`,
  `SETUP_COMPLETE`, `COMECE_AQUI_PT`, `PHASE_0_CHECKLIST`); `README.md` encolhido; criado este
  ficheiro único de continuidade. *Porquê:* 5 ficheiros repetiam o mesmo onboarding — custo de
  tokens e ruído em cada sessão.
- **2026-05-24 — git inicializado** antes da limpeza, como rede de segurança/auditoria.
- **Princípios bloqueados** (herdados dos docs, não renegociáveis): Python calcula / Claude
  interpreta · proteção antes de lucro · JSON é a fonte da verdade · demo antes de FTMO real
  (≥50 setups ou 4 semanas) · escopo pequeno (um modelo ICT primeiro, não a metodologia toda).

---

## 4. Decisões pendentes (bloqueiam a Fase 1)

Hoje só existem *recomendações*, não decisões assumidas pelo trader:

- [ ] **Tipo de challenge FTMO: 1-Step ou 2-Step** (muda os números da config — ver §5).
- [ ] Capital inicial.
- [ ] Símbolo(s) inicial(is) — recomendado: EURUSD.
- [ ] Sessão e janela operacional — recomendado: NY AM (Silver Bullet).
- [ ] Risco por trade — recomendado: 0.25–0.50%.
- [ ] Primeiro modelo ICT — recomendado: NY AM Silver Bullet.
- [ ] Confluência mínima — recomendado: 3 fatores.

---

## 5. Questões em aberto / riscos de realismo

1. **FTMO desatualizado em `config/account.example.yaml`** (verificado online 2026-05):
   `daily_loss_limit_pct: 5.0` e `minimum_trading_days: 10` estão errados.
   - **1-Step:** perda diária **3%**, trailing max loss **10%**, mínimo **4 dias**, alvo 10%.
   - **2-Step:** diária **5%** / total **10%**, alvos **10%→5%**, **4 dias/fase**.
   - Limite de 30 dias **removido** (tempo ilimitado). Daily loss recalcula às 00:00 CE(S)T sobre o
     balanço de fecho do dia anterior, mas conta **equity** intradiária (inclui flutuante + swap +
     comissão). → Corrigir a config **depois** de escolher o tipo de challenge.
2. **ForexFactory fonte única** — feed XML (`nfs.faireconomy.media/ff_calendar_thisweek.xml`)
   funciona e basta para o blackout (hora+impacto), mas é frágil. A análise crítica (3.5) já pede
   2ª fonte ou checklist manual antes da sessão.
3. **Limites do plano Claude (Pro)** — a visão assume Opus a cobrir todas as Kill Zones diárias num
   plano Pro $20. A confirmar; pode exigir Sonnet para a análise ou plano Max. Sem impacto na Fase 0–1.
4. **MT5 Python** — Windows-only (OK, máquina é Win11). Cuidados a tratar na Fase 2: tempos em UTC,
   "Max bars in chart" limita histórico, terminal tem de estar aberto e logado.

---

## 6. Próximo passo (ponto de retoma)

1. **Fechar a Fase 0:** o trader decide os pontos de §4 (em especial o **tipo de challenge**).
2. **Corrigir `config/account.example.yaml`** com os números FTMO 2026 corretos (§5.1).
3. **Iniciar a Fase 1** — schemas Pydantic e contratos de JSON, conforme `ANALISE_CRITICA_E_PLANO.md`
   secção 6 (Fase 1). Nada de código de coleta/engine antes dos schemas.

> Teste de retoma: ler este ficheiro + a análise crítica deve bastar para continuar sem reanalisar
> tudo do zero.
