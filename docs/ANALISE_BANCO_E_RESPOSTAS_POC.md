# Objetivo da Tarefa
Analisar o esquema e os dados reais contidos no arquivo SQLite da Ninfa Alimentos, 
cruzando com os requisitos e perguntas pendentes da PoC (especialmente limites LSE/LIE, 
metadados em 'metadado_poc' e eventuais descrições em 'equipamento') para verificar 
se alguma das respostas em aberto já consta registrada na base.

O documento e a base que a Ninfa enviou sanaram praticamente **todas as dúvidas técnicas sobre o escopo do PoC** (dados, nós, máquinas e arquitetura imediata), mas deixaram em aberto pontos importantes de **regras de negócio, infraestrutura real de fábrica e experiência do usuário**.

Abaixo está o cruzamento detalhado entre o que foi respondido e o que ainda está pendente:

---

### O que FOI Respondido (Escopo do PoC Fechado)

1. **Temperatura do que?**
* **Respondido:** São temperaturas de componentes mecânicos dos equipamentos industriais monitorados (associadas a pontos de medição como mancais/motores junto com a vibração RMS).




2. **Quantas máquinas?**
* **Respondido:** 10 equipamentos (`DEV01` a `DEV10`).




3. **Quais máquinas?**
* **Respondido:** Todas listadas no Anexo A (ex.: Forno `MBF1.1FRN01`, Chiller `MWU3.0CRA01`, etc.).




4. **Temperatura contínua ou cíclica?**
* **Respondido:** Para a base do PoC, o regime é contínuo com leituras em intervalos regulares de 5 minutos cobrindo 1 ano inteiro de histórico.




5. **Integração com o sistema geral?**
* **Respondido:** O PoC roda em SQLite local com histórico simulado, mas a camada de dados precisa ser desacoplada para suportar migração direta para **Oracle / Projeto On Time**.




6. **Linguagem / Stack de desenvolvimento?**
* **Respondido:** A Ninfa deu liberdade de escolha para o time acadêmico (MEIU) desenvolver a aplicação Web e a API, exigindo apenas padrões que facilitem a futura conexão com o Oracle.




7. **Protocolos e Coleta:**
* **Respondido:** O padrão adotado é **OPC UA**, com os nós (`NodeId`), timestamps UTC e códigos de qualidade (`StatusCode`: Good, Uncertain e Bad) já especificados.





---

### ⚠️ O que FICOU PENDENTE (Pontos em Aberto)

Estes são pontos do questionário que o memorial descritivo **não definiu** e que você precisará arbitrar no desenvolvimento ou alinhar com eles:

#### 1. Limites de Referência Operacionais (LSE e LIE)

* O memorial explica o conceito de Limite Superior e Inferior Especificado (LSE/LIE) e exige que a aplicação tenha tela para cadastrá-los, mas **não forneceu os valores numéricos reais de temperatura e vibração** para cada máquina.


* *Impacto no dev:* Você precisará cadastrar limites fictícios/padrão no início para poder testar as condições de "Normal", "Atenção" e "Crítico".



#### 2. Objetivos da Análise Preditiva

* O documento cita apoio à análise preditiva, mas **não detalhou o modelo de predição esperado** (ex.: regressão linear simples de tendência térmica, projeção de tempo até atingir o limite crítico ou detecção de anomalias por desvio padrão).



#### 3. Canais de Notificação e Gestão de Alarmes

* Foi definido que a tela web deve destacar equipamentos em atenção/crítico e diferenciar falhas de dado (`Bad`/`Uncertain`).


* Porém, não especificaram se haverá envio de alertas externos (e-mail, WhatsApp, webhook) ou se o reconhecimento de alarmes com justificativa pelo operador será exigido nesta fase.



#### 4. Dispositivos e Usuários Finais (UX/UI)

* Não detalharam o perfil do operador (se a tela rodará em painel industrial/TV em modo quiosque no chão de fábrica ou apenas em navegadores de escritório).



#### 5. Infraestrutura Real de Rede e Sensores Físicos

* Toda a parte de conectividade de campo (se o chão de fábrica tem Wi-Fi, Ethernet, modelos dos sensores físicos, etc.) ficou suspensa, pois esta etapa foi restrita a **leitura exclusiva da base SQLite sintética** sem conexão à rede industrial viva.



---

**Resumo prático para o Antigravity:**

Você já tem **100% das informações necessárias para codificar a aplicação Web, o banco, os gráficos e o módulo de cadastro**. Para os limites de temperatura e vibração, crie a funcionalidade de configuração permitindo valores padrão configuráveis pelo usuário.