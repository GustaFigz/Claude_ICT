# ICT Analysis System — Documento de Referência do Projeto

> **Versão 1.0 — Maio 2026**
> Este documento define a visão, arquitetura, ferramentas e responsabilidades do sistema.
> Deve ser lido e relido antes de escrever qualquer linha de código ou prompt.
> É um contrato com o projeto — não uma introdução superficial.

---

## Visão Geral

Este é um sistema de análise de mercado profissional que roda **dentro do Claude Code via CLI**, no computador do trader. O Claude Code é o cérebro do sistema — é ele que recebe todos os dados, aplica a metodologia ICT completa, e entrega o relatório de trading. O trader executa o sistema a partir do terminal, lê o relatório, confirma no gráfico, e decide se entra ou não.

Não há interface gráfica. Não há painel web. Não há bot a executar trades. O fluxo é deliberadamente simples: o trader corre o sistema, o Claude Code pensa, o trader age.

O objetivo imediato é **passar uma conta FTMO Challenge**, o que significa que cada decisão de design tem consequências financeiras reais. Nada aqui é académico.

---

## Porquê o Claude Code e Não Outra Solução

O Claude Code pelo CLI tem capacidades que tornam este projeto possível sem custos adicionais:

Consegue ler ficheiros locais diretamente — o data pipeline gera um JSON no disco e o Claude Code lê-o sem intermediários. Consegue executar código Python via Bash tool — o que significa que pode chamar os scripts de recolha de dados, validação e cálculo de níveis como parte do próprio fluxo de análise. Tem um contexto de raciocínio suficientemente longo para processar dados de oito timeframes, correlações, calendário económico e estado da conta numa única sessão. E com o plano Pro ($20/mês), uma análise completa bem estruturada — com um único prompt grande em vez de subagentes paralelos — cabe dentro dos limites diários para cobrir todas as Kill Zones relevantes.

A alternativa de usar a API da Anthropic por chamada seria mais barata por token mas adiciona complexidade de autenticação, gestão de custos variáveis e ausência das ferramentas nativas do Claude Code (Bash, Read, Write). Para este projeto, o Claude Code CLI é a escolha certa.

---

## Como o Sistema Funciona na Prática

O trader abre o terminal. Corre um comando simples com o ativo que quer analisar. O Claude Code, configurado com o CLAUDE.md do projeto, executa automaticamente os seguintes passos:

**Passo 1 — Recolha de Dados (Python via Bash tool)**
O Claude Code chama o script Python de recolha de dados, que vai buscar OHLCV a duas fontes independentes (MT5 Python lib + OANDA free API), recolhe o calendário económico da ForexFactory, lê o estado real da conta diretamente do MT5, e calcula todos os níveis ICT matematicamente. O resultado é um ficheiro JSON estruturado e validado em disco.

**Passo 2 — Validação Automática (Python via Bash tool)**
Antes de qualquer análise, o Claude Code chama o módulo de validação. Este módulo verifica se os dados têm menos de cinco minutos, se as duas fontes de preço concordam, se há eventos de alto impacto nas próximas 90 minutos, se o drawdown diário está dentro do limite de segurança, e se o momento atual está dentro de uma Kill Zone válida. Se qualquer verificação falhar, o sistema para aqui e informa o motivo. Não há análise com dados duvidosos ou condições de mercado inadequadas.

**Passo 3 — Análise ICT (Claude Code, raciocínio interno)**
Com o JSON validado lido em contexto, o Claude Code aplica a metodologia ICT completa na ordem correta: HTF bias top-down, estrutura de mercado por timeframe, mapeamento de liquidez, identificação de PD Arrays válidos, contexto de sessão, correlações, e por fim o modelo de entrada e gestão de risco. Todo este raciocínio acontece dentro do Claude Code — é aqui que está o valor real do sistema.

**Passo 4 — Relatório e Logger (Write tool)**
O relatório final é escrito automaticamente num ficheiro Markdown com timestamp, guardado localmente. O trader lê o relatório, abre o gráfico no MT5, confirma o que o sistema identificou, e decide se executa o trade.

---

## Estrutura do Projeto

O projeto vive numa pasta local no computador do trader e é chamado via Claude Code CLI a partir dessa pasta. A estrutura é a seguinte:

**CLAUDE.md** — O ficheiro mais importante do projeto. Define ao Claude Code quem ele é, o que sabe, como deve pensar, e como deve agir. Contém a metodologia ICT completa, as regras FTMO embutidas, o formato de output obrigatório, e as instruções de execução do fluxo. Este ficheiro é o "cérebro em repouso" do sistema.

**data_pipeline/** — Scripts Python responsáveis pela recolha, validação e cálculo de dados. Nenhum destes scripts tem lógica de trading — são apenas recolha e matemática. O Claude Code chama-os via Bash tool.

**data_pipeline/collector.py** — Recolhe OHLCV do MT5 e da OANDA para os oito timeframes necessários, recolhe o calendário económico da ForexFactory, e lê o estado da conta do MT5.

**data_pipeline/validator.py** — Verifica qualidade dos dados, concordância entre fontes, blackout de notícias, estado do drawdown, e condição da sessão. Retorna um status claro: GO ou BLOCKED com motivo.

**data_pipeline/calculator.py** — Calcula matematicamente os níveis ICT: swing highs/lows, equilíbrio, zonas premium/discount, ranges IPDA, pools de liquidez BSL/SSL, Order Blocks válidos, Fair Value Gaps ativos, correlação DXY.

**context/** — Ficheiros JSON gerados pelo pipeline a cada análise. São temporários mas ficam guardados para auditoria.

**reports/** — Relatórios Markdown gerados pelo Claude Code após cada análise, com timestamp. Cada ficheiro é o registo permanente de uma sessão de análise.

**logs/trades.md** — Log manual mantido pelo trader: cada trade executado com base numa análise do sistema, resultado, e notas. Essencial para medir a performance real do sistema ao longo do tempo.

---

## O Ficheiro CLAUDE.md — O Coração do Sistema

O CLAUDE.md não é um README. É o document de instruções que o Claude Code lê automaticamente ao ser iniciado na pasta do projeto. Define completamente o comportamento do sistema.

Contém as seguintes secções, cada uma elaborada ao máximo detalhe:

**Identidade e Propósito** — O Claude Code sabe que é um analista ICT profissional cujo único objetivo é apoiar decisões de trading numa conta FTMO. Sabe que erros têm consequências financeiras reais. Sabe que é preferível não dar nenhuma análise a dar uma análise incorreta.

**Fluxo de Execução Obrigatório** — A sequência exata de passos que deve seguir quando o trader pede uma análise: chamar o collector, chamar o validator, ler o JSON resultante, e só depois iniciar o raciocínio ICT. Nunca começar a análise sem dados frescos e validados.

**Metodologia ICT Completa** — A totalidade do conhecimento ICT necessário escrito de forma estruturada: IPDA e Quarterly Shifts, hierarquia completa de PD Arrays, tipos de liquidez e como os identificar, modelos de estrutura de mercado (BOS, CHOCH, MSS), Power of Three e Judas Swing, todos os modelos de entrada (OTE, OB Mitigation, FVG Fill, Silver Bullet, Turtle Soup), timing de Kill Zones e Macros ICT, e leitura top-down obrigatória de Monthly até M1.

**Regras FTMO Incorporadas** — As condições de bloqueio que o Claude Code verifica antes de qualquer sugestão de trade: drawdown diário acima de 3.5% de buffer (antes do limite real de 5%), drawdown total acima de 8% de buffer (antes do limite real de 10%), eventos de alto impacto nas próximas 90 minutos, fora de Kill Zone válida, e menos de três confluências ICT identificadas. Qualquer uma destas condições resulta em output de bloqueio com motivo claro.

**Formato de Output Obrigatório** — O relatório segue sempre a mesma estrutura: Bias HTF, Estrutura de Mercado, Liquidez e Níveis, Contexto de Sessão, Notícias e Risco Macro, Correlações, Setup de Entrada, Gestão de Risco, Decisão Final. A decisão final é sempre uma de quatro: COMPRAR, VENDER, AGUARDAR, ou SEM TRADE.

---

## As Fontes de Dados e Porquê

Cada fonte foi escolhida por ser gratuita, confiável o suficiente com validação, e acessível sem autenticação paga.

**MT5 Python Library (metatrader5 via PyPI)** — Fonte primária para dados de preço e, a única fonte possível para estado da conta (equity, drawdown, trades abertos). Gratuita, mas tem bugs conhecidos de cache e dados stale que requerem workarounds específicos no collector.py. Usada em conjunto com a OANDA para validação cruzada de preços.

**OANDA REST API v20 (conta demo gratuita)** — Fonte secundária de preços. API REST pura, sem bugs de estado, com dados históricos desde 2005 para todos os timeframes necessários. Requer criação de conta demo gratuita na OANDA para obter API key. É o padrão de qualidade que valida os dados do MT5.

**ForexFactory Calendar XML** — Calendário económico semanal disponível publicamente em formato XML sem autenticação. Recolhido pelo collector.py para identificar eventos de alto impacto nas próximas 48 horas. Não é scraping — é um feed público.

**yfinance (Yahoo Finance Python lib)** — Usado para recolher dados de DXY e outros índices de correlação que não estão disponíveis diretamente no MT5 ou OANDA. Gratuito, sem autenticação.

**Cálculo local (calculator.py)** — Todos os níveis ICT (swing points, equilíbrio, IPDA ranges, OBs, FVGs, pools de liquidez) são calculados matematicamente pelo Python antes de chegar ao Claude Code. O Claude Code não calcula — interpreta e raciocina sobre factos já calculados. Esta separação é crítica para a fiabilidade do sistema.

---

## O Que o Claude Code Recebe

Quando inicia a análise, o Claude Code recebe um JSON com cinco categorias de dados:

**Dados de Preço** — OHLCV de oito timeframes (MN, W1, D1, H4, H1, M15, M5, M1) com quantidade de velas suficiente para contexto ICT em cada um. Cada timeframe inclui os níveis pré-calculados relevantes: PDH/PDL, PWH/PWL, NDOG, NWOG, OBs válidos, FVGs ativos, e swing points.

**Níveis Calculados** — Equilíbrio do range atual, zonas premium e discount, ranges IPDA de 20/40/60 dias, todos os pools de liquidez BSL e SSL identificados por tipo e timeframe, e o Draw on Liquidity atual com direção e alvo.

**Contexto de Sessão** — Kill Zone ativa ou mais próxima com tempo até início, se há Macro ICT ativo, se estamos dentro de Silver Bullet window, e fase atual do Power of Three.

**Calendário Económico** — Eventos das próximas 48 horas para as moedas do ativo analisado, com hora, impacto, forecast e anterior. Flag de blackout se evento high-impact em menos de 90 minutos.

**Estado da Conta** — Balance, equity, P&L do dia em percentagem, drawdown total acumulado, trades abertos, e o cálculo de espaço restante antes dos limites FTMO.

---

## O Que o Sistema NÃO Faz

Não executa trades. A execução é sempre manual, sempre com confirmação visual no gráfico.

Não funciona sem dados validados. Se o validator.py retornar BLOCKED, o Claude Code informa e para.

Não usa subagentes paralelos. A análise ICT é sequencial e interdependente — o bias HTF determina o que procurar no LTF. Fragmentar em subagentes paralelos gera contradições e desperdiça contexto. Um único agente com contexto completo é mais preciso e mais eficiente em tokens.

Não substitui o trader. O relatório é uma análise de alta qualidade, não uma ordem. O trader confirma sempre no gráfico antes de agir.

Não opera em condições inadequadas. Fora de Kill Zone, com notícias próximas, drawdown no limite, ou confluência insuficiente — o output é bloqueio com motivo, nunca uma análise forçada.

---

## Fases de Construção — Ordem Obrigatória

A ordem das fases não é sugestão. Cada fase é pré-requisito da seguinte.

**Fase 1 — Data Pipeline**
Construção e teste do collector.py, validator.py e calculator.py. O objetivo é ter um JSON limpo, validado e com todos os níveis ICT calculados. Nenhuma análise é feita nesta fase. O critério de sucesso é simples: o JSON produzido está correto e verificável manualmente no gráfico.

**Fase 2 — FTMO Rules Engine**
As condições de bloqueio são implementadas e testadas antes de qualquer outra coisa. O sistema de proteção existe antes do sistema de análise. Sempre.

**Fase 3 — CLAUDE.md — ICT Engine**
Construção do CLAUDE.md com a metodologia ICT completa e o fluxo de execução. Esta fase requer iteração — o prompt é testado com dados reais e os resultados são comparados manualmente com análise ICT feita pelo trader. Só avança quando a qualidade for consistentemente alta.

**Fase 4 — Logger Automático**
O Claude Code escreve o relatório automaticamente em reports/ com timestamp. Cada análise fica arquivada para auditoria.

**Fase 5 — Validação em Demo**
Mínimo de duas a três semanas em conta demo. Cada setup sugerido é registado em logs/trades.md com resultado. O sistema só é usado numa conta FTMO real após esta validação produzir dados de performance suficientes para justificar confiança.

---

## Princípios Inegociáveis

**Proteção primeiro.** O FTMO Rules Engine é construído antes do motor de análise. Sempre.

**Dados ou nada.** Sem dados validados não há análise. Sem análise não há trade.

**O Claude Code pensa, o trader decide.** A ferramenta aumenta a capacidade de análise. Não a substitui.

**Qualidade acima de velocidade.** Perder um setup é aceitável. Entrar com análise incompleta não é.

**Confiança gradual.** Demo primeiro, semanas de dados depois, FTMO real só quando os números justificarem.

---

*Quando a construção parecer completa, volta a este documento e faz uma pergunta honesta: cada componente está realmente à altura do que aqui está escrito? Se a resposta for "mais ou menos", não está pronto.*
