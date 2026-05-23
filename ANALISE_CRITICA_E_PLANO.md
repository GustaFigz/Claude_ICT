# Análise Crítica e Planeamento do ICT Analysis System

> Data da análise: 2026-05-24  
> Base analisada: `ICT_System_Project_v2.md`  
> Objetivo deste documento: transformar a visão do projeto numa especificação operacional, testável e realista.

---

## 1. Veredito Executivo

A ideia é boa como ferramenta de apoio à decisão, mas ainda está demasiado ambiciosa e subjetiva para ser usada diretamente numa FTMO Challenge. O documento original tem bons princípios: proteção primeiro, dados validados, execução manual e demo antes da conta real. O problema é que ele ainda mistura visão, crenças metodológicas e arquitetura sem converter tudo em critérios objetivos de teste.

O maior risco não é técnico. É epistemológico: acreditar que um modelo de linguagem, mesmo com bons dados, consegue aplicar uma metodologia de trading altamente interpretativa de forma estável, auditável e repetível. Para funcionar de facto, o sistema precisa reduzir drasticamente a margem de interpretação do Claude Code e mover o máximo possível para código determinístico: dados, risco, calendário, sessões, cálculo de níveis, definição de setups, sizing, bloqueios e score de confluência.

O Claude Code deve ser o analista narrativo e o auditor final, não o oráculo. A decisão de trade deve sair de uma combinação de regras objetivas e análise estruturada, com o LLM impedido de inventar níveis, ignorar bloqueios ou "forçar" uma leitura.

Minha recomendação central: transformar o projeto de "Claude aplica ICT completo" para "pipeline determinístico produz contexto, motor de regras filtra setups, Claude explica e valida a tese". Essa mudança aumenta muito a chance de sobreviver em ambiente FTMO.

---

## 2. O Que Está Forte no Documento Atual

### 2.1 Escopo de produto simples

A decisão de não criar painel web, bot de execução ou interface complexa é correta. Um sistema CLI reduz superfície de bugs, reduz distrações e mantém o trader responsável pela execução.

### 2.2 Separação entre dados e interpretação

A ideia de calcular níveis em Python antes de passar o JSON ao Claude é excelente. Essa separação deve ser preservada e reforçada.

### 2.3 Regra de bloqueio antes da análise

O conceito de parar o sistema antes de analisar quando dados, notícias, drawdown ou sessão falham é um dos pontos mais importantes do projeto.

### 2.4 Execução manual

Não executar trades automaticamente é uma decisão madura. Para FTMO, o risco operacional de automação cedo demais é muito maior do que o benefício.

### 2.5 Registro e auditoria

Guardar relatórios e manter um log de trades é essencial. Sem isso, o sistema vira uma máquina de confirmação seletiva: lembra os acertos e esquece os erros.

---

## 3. Fragilidades Críticas Que Precisam Ser Corrigidas

### 3.1 "Metodologia ICT completa" é ampla demais para MVP

O documento tenta incluir IPDA, Quarterly Shifts, PD Arrays, BOS, CHOCH, MSS, Power of Three, Judas Swing, OTE, OB Mitigation, FVG Fill, Silver Bullet, Turtle Soup, Kill Zones, Macros e leitura de Monthly até M1.

Isso é grande demais para a primeira versão. Quanto mais modelos incluídos, mais graus de liberdade o Claude terá para justificar qualquer direção. Isso aumenta overfitting e subjetividade.

Mudança recomendada:

- Começar com 1 ou 2 modelos específicos.
- Exemplo: NY AM Silver Bullet com HTF bias em D1/H4/H1 e confirmação em M5/M1.
- Só adicionar outros modelos após medir performance isolada do primeiro.
- Cada modelo deve ter critérios próprios de ativação, invalidação, entrada, stop, alvo e bloqueio.

Critério racional:

Se um conceito ICT não puder ser definido em regras verificáveis no gráfico, ele não deve entrar no motor da versão 1.

### 3.2 O Claude Code não deve calcular nem decidir sozinho

O documento diz que Python calcula e Claude interpreta. Isso é bom, mas ainda deixa espaço demais para o Claude decidir com linguagem natural.

Mudança recomendada:

- O Python deve gerar também um `setup_candidate` estruturado ou `no_candidate`.
- O Claude deve receber campos fechados: bias, liquidez alvo, nível de entrada, invalidação, stop sugerido, alvo, R:R, risco permitido e motivos de bloqueio.
- O Claude pode explicar, desafiar e resumir, mas não pode criar um setup novo fora dos dados.
- A decisão final deve respeitar uma regra: se `validator.status != GO`, output obrigatório é `SEM TRADE`.

### 3.3 Falta uma definição matemática dos conceitos ICT

Termos como Order Block válido, Fair Value Gap ativo, swing high/low, MSS, BOS, displacement, premium/discount e draw on liquidity precisam de definição exata.

Exemplos de especificação necessária:

- Swing high: candle cujo high é maior que os highs de N candles à esquerda e N candles à direita. Definir N por timeframe.
- BOS: fechamento além do swing ou apenas wick? Definir.
- CHOCH/MSS: exige displacement? Quantos pips? ATR mínimo?
- FVG: gap entre high/low de candles 1 e 3; tamanho mínimo em pips ou ATR; considerar apenas gaps não mitigados acima de X%.
- OB: última candle oposta antes de displacement; precisa quebrar estrutura? precisa ter volume? qual invalidação?
- Premium/discount: qual range ancora? último swing HTF, dealing range diário, semanal, IPDA?
- Liquidity pool: equal highs/lows com tolerância de quantos pips?

Sem isso, duas execuções podem produzir análises diferentes para o mesmo gráfico.

### 3.4 Validação de dados precisa considerar diferenças reais entre feeds

MT5 e OANDA podem divergir por motivo legítimo:

- bid, ask ou mid candles;
- timezone do broker;
- sessão diária e candle daily com fechamento diferente;
- spreads;
- símbolos diferentes;
- CFD vs spot;
- horários de rollover;
- liquidez de fim de dia;
- candle incompleto.

Mudança recomendada:

- Definir uma fonte primária por tipo de decisão. Para execução FTMO, o preço do broker/MT5 deve ser o decisivo.
- Usar OANDA como sanity check, não como verdade absoluta.
- Comparar apenas candles fechadas, nunca a candle atual.
- Criar tolerâncias por símbolo e timeframe.
- Registrar `source_price_type`: bid, ask, mid ou broker.
- Registrar `broker_timezone`, `server_time`, `utc_time` e `ny_time`.

### 3.5 O calendário económico não pode depender de uma única fonte

ForexFactory é útil, mas o próprio calendário informa que horários são aproximados e podem mudar. Isso é perigoso para bloqueios de notícias.

Mudança recomendada:

- Usar ForexFactory como fonte principal gratuita, mas adicionar pelo menos uma segunda fonte ou checklist manual antes da sessão.
- Bloquear high impact por moeda base/cotada, USD e eventos globais relevantes.
- Bloquear discursos de bancos centrais quando classificados como potencialmente relevantes, mesmo que o impacto não venha como "red folder".
- Registrar timezone original do calendário e timezone normalizado.
- Criar cache com hash do calendário para auditoria.

### 3.6 Regras FTMO precisam ser parametrizadas por tipo de challenge

O documento cita buffers de 3.5% diário e 8% total. Isso pode ser prudente, mas as regras oficiais variam entre 1-Step e 2-Step e podem mudar. O sistema não pode ter esses números fixos no prompt.

Mudança recomendada:

- Criar `config/account.yaml` com:
  - tipo de challenge: 1-Step ou 2-Step;
  - capital inicial;
  - moeda da conta;
  - daily loss limit;
  - max loss limit;
  - profit target;
  - minimum trading days;
  - timezone FTMO: CE(S)T;
  - buffer interno;
  - risco máximo por trade;
  - risco máximo por dia;
  - número máximo de trades por dia.

Importante:

O motor deve calcular perda diária com equity, P/L aberto, comissões e swaps, usando a virada diária correta em CE(S)T. Não basta olhar apenas para P&L fechado.

### 3.7 Falta gestão de risco por trade

O documento fala de drawdown, mas não especifica sizing operacional.

Adicionar regras obrigatórias:

- risco padrão por trade: 0.25% a 0.50% da conta;
- bloquear trade se stop técnico exigir lote abaixo do mínimo ou acima do risco permitido;
- bloquear trade se R:R líquido for menor que 2R, salvo modelo validado separadamente;
- bloquear após 1 ou 2 perdas no dia;
- bloquear após atingir meta diária conservadora;
- proibir martingale, aumento de lote após loss e múltiplas entradas correlacionadas;
- incluir spread, comissão e slippage no cálculo;
- bloquear trade se a distância do stop for inferior ao ruído médio/spread.

### 3.8 "Passar FTMO" não deve ser a métrica inicial

Passar FTMO é resultado. A métrica do sistema deve ser edge mensurável.

Mudança recomendada:

Antes de tentar FTMO:

- mínimo de 50 setups documentados em modo shadow/demo;
- expectancy positiva em R;
- profit factor acima de 1.3 como mínimo inicial;
- max losing streak conhecida;
- drawdown simulado inferior ao buffer;
- resultados separados por ativo, sessão e modelo;
- comparação entre análise do sistema e decisão manual do trader.

Duas ou três semanas de demo podem ser pouco se houver poucos setups. Melhor usar número mínimo de trades/setups e cobrir diferentes condições de mercado.

### 3.9 CLAUDE.md não deve virar um livro gigante

O documento atual vê o `CLAUDE.md` como o cérebro completo. Isso é perigoso por custo, limite de contexto e ruído. A documentação oficial do Claude Code indica que `CLAUDE.md` do projeto é carregado no contexto. Logo, um arquivo enorme será custo fixo em todas as sessões.

Mudança recomendada:

- `CLAUDE.md` deve conter apenas política operacional, comandos e regras absolutas.
- A metodologia deve ficar em arquivos menores dentro de `rules/`, lidos sob demanda.
- O JSON deve ser a fonte da verdade.
- O prompt deve exigir que o Claude cite campos do JSON para justificar qualquer conclusão.

### 3.10 Falta estratégia de testes

O projeto só fala em validar manualmente no gráfico. Isso é necessário, mas insuficiente.

Adicionar:

- testes unitários para cada cálculo;
- fixtures com candles conhecidas e níveis esperados;
- testes de timezone/DST;
- testes de regras FTMO;
- testes de schema do JSON;
- golden files para relatórios;
- backtest visual/manual por amostragem;
- auditoria de divergência entre MT5 e OANDA.

### 3.11 Falta controle de segredos e privacidade

O sistema vai lidar com API keys, login de conta, equity e histórico de trades. O Claude Code pode ler arquivos locais e enviar contexto ao provedor do modelo. Isso precisa ser tratado.

Mudança recomendada:

- `.env` para credenciais;
- `.gitignore` forte para `.env`, `context/`, `reports/`, `logs/` se houver dados sensíveis;
- redigir login, nome da conta e servidor em relatórios;
- nunca passar API key ou senha ao Claude;
- Python coleta dados sensíveis e entrega apenas campos necessários.

---

## 4. Arquitetura Recomendada

### 4.1 Estrutura de pastas

```text
ICT/
  CLAUDE.md
  README.md
  pyproject.toml
  .env.example
  .gitignore

  config/
    account.example.yaml
    symbols.yaml
    sessions.yaml
    risk.yaml

  data_pipeline/
    __init__.py
    collector.py
    mt5_client.py
    oanda_client.py
    news_client.py
    market_clock.py
    schemas.py

  ict_engine/
    __init__.py
    swings.py
    structure.py
    liquidity.py
    pd_arrays.py
    setups.py
    risk.py
    validator.py

  cli/
    main.py

  context/
    .gitkeep

  reports/
    .gitkeep

  logs/
    trades.md
    analyses.jsonl

  rules/
    execution_policy.md
    ict_definitions.md
    report_template.md

  tests/
    fixtures/
    test_swings.py
    test_structure.py
    test_risk_ftmo.py
    test_validator.py
    test_schemas.py
```

### 4.2 Fluxo operacional recomendado

```text
Trader executa:
  python -m cli.main analyze EURUSD --model silver-bullet

Sistema:
  1. Carrega config da conta e do símbolo.
  2. Coleta MT5.
  3. Coleta fonte secundária.
  4. Normaliza timezones e candles.
  5. Remove/identifica candle incompleto.
  6. Calcula níveis e setups candidatos.
  7. Executa risk engine.
  8. Executa validator.
  9. Gera context/run_id.json.
  10. Se BLOCKED, gera relatório curto de bloqueio.
  11. Se GO, Claude lê o JSON e produz relatório final.
```

### 4.3 JSON mínimo recomendado

O JSON não deve ser apenas dumping de candles. Ele deve conter fatos prontos para decisão.

Campos essenciais:

- `run_id`
- `created_at_utc`
- `symbol`
- `broker_symbol`
- `account_snapshot`
- `ftmo_limits`
- `session_state`
- `news_state`
- `data_quality`
- `timeframes`
- `levels`
- `liquidity`
- `structure`
- `setup_candidates`
- `risk_calculation`
- `validator_result`

### 4.4 Decisão final

O output final deve ter esta precedência:

1. Se dados inválidos: `SEM TRADE`.
2. Se risco FTMO inválido: `SEM TRADE`.
3. Se notícia bloqueia: `SEM TRADE`.
4. Se fora da janela operacional: `AGUARDAR`.
5. Se setup candidato não atinge score mínimo: `AGUARDAR`.
6. Se setup válido e risco aprovado: `COMPRAR` ou `VENDER`.

---

## 5. Alterações Diretas no Documento Original

### 5.1 Trocar "Claude Code é o cérebro" por uma formulação mais segura

Atual:

> O Claude Code é o cérebro do sistema.

Melhor:

> O pipeline Python é a fonte da verdade para dados, níveis, validação e risco. O Claude Code atua como analista final, explicando a tese, verificando coerência e produzindo o relatório com base em fatos estruturados.

### 5.2 Trocar "metodologia ICT completa" por "modelos ICT versionados"

Atual:

> aplica a metodologia ICT completa

Melhor:

> aplica modelos ICT versionados, cada um com critérios objetivos de ativação, invalidação, entrada, stop, alvo e bloqueio.

### 5.3 Adicionar uma fase zero

Antes da Fase 1, adicionar:

**Fase 0 — Escopo e Especificação**

Escolher ativos, tipo de challenge, modelo ICT inicial, timeframes, timezone, regras de risco, critérios de sucesso e critérios de bloqueio.

### 5.4 Adicionar fase de testes antes do prompt

Antes de construir o `CLAUDE.md`, o motor de dados e risco deve ter testes automatizados.

### 5.5 Reescrever validação demo

Atual:

> Mínimo de duas a três semanas em conta demo.

Melhor:

> Mínimo de 50 setups registrados ou 4 semanas de shadow/demo, o que vier por último, com expectancy positiva, drawdown controlado e análise por modelo/sessão/ativo.

### 5.6 Adicionar regra de não generalização

O sistema não deve dizer "ICT funciona" ou "o modelo é bom". Ele deve dizer:

- este modelo;
- neste ativo;
- nesta sessão;
- com este risco;
- neste período de validação;
- teve estes resultados.

---

## 6. Plano de Execução Completo

### Fase 0 — Escopo, Configuração e Critérios

Objetivo: reduzir ambiguidade antes de escrever o motor.

Tarefas:

- escolher 1 a 3 ativos iniciais;
- escolher tipo de FTMO: 1-Step ou 2-Step;
- definir capital inicial;
- definir timezone operacional: Lisboa, Nova York, UTC e CE(S)T;
- escolher o primeiro modelo ICT;
- definir risco por trade e risco diário;
- definir horários permitidos;
- definir fontes de dados por ativo;
- criar `config/*.yaml`;
- criar `.env.example`;
- criar `.gitignore`.

Critério de conclusão:

- O projeto consegue responder objetivamente: "quando o sistema pode operar, o que ele procura, quanto pode arriscar e quando deve bloquear".

### Fase 1 — Schema e Contratos de Dados

Objetivo: impedir que o projeto vire dados soltos sem contrato.

Tarefas:

- criar modelos Pydantic para candles, eventos, conta, níveis, setups e validação;
- definir JSON final;
- criar exemplos estáticos em `tests/fixtures/`;
- criar validação de schema;
- criar `run_id` e metadados de auditoria.

Critério de conclusão:

- Um JSON inválido falha antes de chegar ao Claude.

### Fase 2 — Coleta de Dados

Objetivo: recolher dados confiáveis e auditáveis.

Tarefas:

- implementar cliente MT5;
- implementar cliente OANDA ou fonte secundária;
- implementar cliente de calendário;
- implementar normalização de símbolos;
- implementar timezone handling;
- remover candle incompleto;
- salvar dados brutos e normalizados;
- registrar erros e latência.

Critério de conclusão:

- Para cada ativo inicial, o sistema gera candles consistentes em todos os timeframes exigidos.

### Fase 3 — Cálculos ICT Determinísticos

Objetivo: converter conceitos subjetivos em regras testáveis.

Tarefas:

- implementar swing highs/lows;
- implementar premium/discount;
- implementar FVG;
- implementar OB com critérios estritos;
- implementar liquidez BSL/SSL;
- implementar estrutura BOS/CHOCH/MSS;
- implementar session ranges;
- implementar setup candidato do primeiro modelo escolhido.

Critério de conclusão:

- Os níveis calculados batem visualmente com o gráfico em uma amostra de casos e passam nos testes unitários.

### Fase 4 — FTMO Rules Engine e Risk Engine

Objetivo: proteger a conta antes de procurar lucro.

Tarefas:

- implementar cálculo de daily loss;
- implementar cálculo de max loss;
- implementar buffer interno;
- implementar sizing por stop técnico;
- incluir spread, comissão e slippage;
- bloquear por número de perdas/trades no dia;
- bloquear por correlação de posições;
- gerar motivo claro de bloqueio.

Critério de conclusão:

- O sistema prefere perder oportunidade a violar risco.

### Fase 5 — Validator

Objetivo: decidir GO/BLOCKED antes do Claude.

Tarefas:

- validar freshness dos dados;
- validar divergência MT5 vs fonte secundária;
- validar sessão;
- validar notícias;
- validar estado da conta;
- validar setup mínimo;
- emitir `validator_result`.

Critério de conclusão:

- `BLOCKED` é explicado por motivo específico e rastreável.

### Fase 6 — Claude Layer

Objetivo: fazer o Claude produzir análise útil sem inventar fatos.

Tarefas:

- criar `CLAUDE.md` compacto;
- criar `rules/report_template.md`;
- criar `rules/execution_policy.md`;
- criar prompt que obriga citar campos do JSON;
- criar formato fixo de relatório;
- criar relatório curto para bloqueios;
- criar relatório completo para GO.

Critério de conclusão:

- O Claude não cria níveis que não estão no JSON e não ignora bloqueios.

### Fase 7 — Logger e Auditoria

Objetivo: medir performance real.

Tarefas:

- salvar relatório em `reports/`;
- salvar linha estruturada em `logs/analyses.jsonl`;
- manter `logs/trades.md`;
- criar campos de resultado em R;
- registrar screenshots manualmente ou caminhos para imagens;
- criar resumo semanal.

Critério de conclusão:

- Qualquer trade pode ser reconstruído: dados, tese, risco, decisão e resultado.

### Fase 8 — Validação Shadow

Objetivo: medir sem arriscar FTMO.

Tarefas:

- rodar sistema nas sessões escolhidas;
- registrar setups aceitos e bloqueados;
- comparar com gráfico manual;
- medir winrate, expectancy, profit factor, drawdown e sequência de perdas;
- identificar falsos positivos;
- ajustar regras, não o resultado.

Critério de conclusão:

- Mínimo de 50 setups ou 4 semanas, com métricas positivas e drawdown dentro do buffer.

### Fase 9 — Demo Controlada

Objetivo: validar execução humana e disciplina.

Tarefas:

- operar apenas setups GO;
- risco reduzido;
- sem exceções manuais fora do sistema;
- registrar slips, hesitação, entrada tardia e erros humanos;
- rever semanalmente.

Critério de conclusão:

- O trader consegue seguir o sistema sem quebrar regras.

### Fase 10 — FTMO Real

Objetivo: executar com risco conservador.

Tarefas:

- reduzir risco por trade no início;
- limitar número de trades por dia;
- parar após perda definida;
- não operar em dias de alta incerteza macro;
- rever diariamente;
- aumentar risco apenas após evidência.

Critério de conclusão:

- A conta permanece dentro do plano mesmo em sequência negativa.

---

## 7. Roadmap Sugerido

### Semana 1

- Fase 0 completa.
- Estrutura de pastas.
- Configs.
- Schemas.
- Primeiros fixtures.

### Semana 2

- MT5 collector.
- Fonte secundária.
- Calendário.
- Normalização de timezone.
- Testes básicos.

### Semana 3

- Swings.
- Estrutura.
- FVG.
- Liquidez.
- Premium/discount.

### Semana 4

- Primeiro modelo ICT.
- FTMO risk engine.
- Validator.
- Relatórios de bloqueio.

### Semana 5

- CLAUDE.md compacto.
- Templates de relatório.
- Integração end-to-end.
- Primeiras análises em shadow.

### Semanas 6 a 9

- Shadow/demo.
- Correção de falsos positivos.
- Métricas.
- Revisão semanal.

### Semana 10+

- Decisão racional: continuar demo, ajustar modelo ou iniciar FTMO com risco mínimo.

---

## 8. Métricas Que Devem Mandar no Projeto

Métricas de dados:

- porcentagem de runs com dados válidos;
- divergência média MT5 vs fonte secundária;
- número de bloqueios por fonte;
- latência de coleta.

Métricas de setups:

- setups por semana;
- taxa de bloqueio;
- taxa de GO;
- winrate;
- expectancy em R;
- profit factor;
- max drawdown;
- max losing streak;
- resultado por ativo;
- resultado por sessão;
- resultado por modelo.

Métricas humanas:

- trades ignorados;
- trades feitos fora do sistema;
- entradas tardias;
- stops movidos;
- targets alterados;
- violações de regra.

---

## 9. Prioridades Imediatas

1. Escolher apenas um modelo ICT inicial.
2. Definir exatamente o tipo de FTMO e regras da conta.
3. Criar configs e schemas.
4. Construir coleta MT5 robusta.
5. Construir risk engine antes de qualquer prompt complexo.
6. Escrever testes para regras de risco e timezone.
7. Só depois montar o `CLAUDE.md`.

---

## 10. Conclusão

O projeto pode funcionar, mas não como "um grande prompt ICT" apoiado por dados. Para funcionar de facto, precisa ser tratado como um sistema de decisão sob risco: determinístico onde importa, conservador por defeito, mensurável por R, auditável por run e humilde perante incerteza.

A versão forte deste projeto não tenta prever tudo. Ela bloqueia quase tudo, aceita poucos setups, explica claramente porquê e mede se esses poucos setups têm edge real.

Essa é a diferença entre uma ferramenta interessante e uma ferramenta que talvez sobreviva a uma FTMO Challenge.

---

## 11. Referências Verificadas

- FTMO Trading Objectives: https://ftmo.com/pt/trading-objectives/
- Claude Code com plano Pro/Max: https://support.claude.com/pt/articles/11145838-use-claude-code-com-seu-plano-pro-ou-max
- Claude Code project memory / CLAUDE.md: https://code.claude.com/docs/en/memory
- MetaTrader5 Python account_info: https://www.mql5.com/en/docs/python_metatrader5/mt5accountinfo_py
- MetaTrader5 PyPI: https://pypi.org/project/metatrader5/
- ForexFactory Calendar: https://www.forexfactory.com/calendar
- OANDA REST v20 documentation: https://oanda-api-v20.readthedocs.io/
