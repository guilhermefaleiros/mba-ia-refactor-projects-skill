# Plano de Implementação — Skill `refactor-arch`

## Visão Geral

Criar uma Skill para Claude Code que automatiza a análise, auditoria e refatoração de projetos legados para o padrão MVC. A skill deve ser agnóstica de tecnologia e funcionar nos 3 projetos fornecidos.

---

## 1. Análise Manual dos Projetos

### Projeto 1 — `code-smells-project` (Python/Flask — E-commerce API)

**Arquitetura atual:** 4 arquivos sem separação de camadas clara. `models.py` contém queries SQL diretas, `controllers.py` contém handlers HTTP, `app.py` mistura roteamento com endpoints admin, `database.py` usa conexão global.

| # | Severidade | Problema | Arquivo:Linha | Justificativa |
|---|-----------|----------|---------------|---------------|
| 1 | **CRITICAL** | **SQL Injection** — Todas as queries em `models.py` usam concatenação de strings ao invés de queries parametrizadas | `models.py:28,47-49,57-60,68,92,109-111,126-128,140,148-150,157-161,163-165,174,188,220,279-280,289-297` | Permite execução arbitrária de SQL. Atacante pode ler/modificar/deletar qualquer dado do banco. |
| 2 | **CRITICAL** | **Credenciais hardcoded** — SECRET_KEY exposta no código-fonte e no endpoint health | `app.py:7`, `controllers.py:289` | Chave secreta em texto plano no repositório. Endpoint `/health` expõe a SECRET_KEY e modo debug para qualquer requisição. |
| 3 | **CRITICAL** | **Endpoint admin sem autenticação** — `/admin/query` aceita SQL arbitrário sem nenhuma verificação | `app.py:59-78` | Backdoor completo: qualquer pessoa pode executar qualquer SQL no banco, incluindo DROP TABLE. |
| 4 | **CRITICAL** | **Senhas em texto plano** — Senhas armazenadas sem hash no banco de dados | `models.py:122-131`, `database.py:76-83` | Senhas dos usuários visíveis em texto puro. `login_usuario()` compara senha em plaintext. `get_todos_usuarios()` e `get_usuario_por_id()` retornam a senha nos dados. |
| 5 | **HIGH** | **God File** — `models.py` com ~315 linhas contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios | `models.py:1-315` | Impossível testar em isolamento. Qualquer mudança pode afetar todos os domínios. Viola SRP. |
| 6 | **HIGH** | **Conexão global de banco** — Singleton mutável compartilhado entre threads | `database.py:4,9` | `check_same_thread=False` em SQLite com variável global. Race conditions em ambiente multi-thread. |
| 7 | **HIGH** | **Lógica de negócio nos controllers** — Validação de regras (categorias válidas, status de pedidos) hardcoded no controller | `controllers.py:52-54,242` | Duplicação de regras de negócio. Categorias e status válidos estão espalhados em strings mágicas. |
| 8 | **MEDIUM** | **N+1 Queries** — Listagem de pedidos faz query individual para cada item e cada produto | `models.py:186-200,219-232` | Dois loops aninhados com queries individuais: cursor2 para itens_pedido + cursor3 para nome do produto, multiplicado por cada pedido. |
| 9 | **MEDIUM** | **Código duplicado** — Funções `get_pedidos_usuario()` e `get_todos_pedidos()` são praticamente idênticas | `models.py:171-233` | ~60 linhas duplicadas. Mesma lógica de montagem de pedido + itens copiada/colada. |
| 10 | **MEDIUM** | **Serialização manual repetitiva** — Conversão row→dict repetida em cada função | `models.py:10-21,31-40,79-86,94-102` | Mapeamento campo-a-campo replicado em ~8 funções. Qualquer mudança no schema exige alterar múltiplos locais. |
| 11 | **LOW** | **Print statements como logging** — `print()` usado para logging em produção | `controllers.py:8,57,106,161,179,182,208-210,219,248,250` | Sem níveis de log, sem formatação estruturada, sem rotação. Inviável em produção. |
| 12 | **LOW** | **Debug mode em produção** — `app.run(debug=True)` e `app.config["DEBUG"] = True` | `app.py:8,88` | Debug mode expõe stack traces e console interativo para qualquer usuário. |
| 13 | **LOW** | **Magic numbers** — Valores de desconto hardcoded sem constantes | `models.py:257-262` | Thresholds (10000, 5000, 1000) e percentuais (0.1, 0.05, 0.02) sem nomes descritivos. |

---

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express — LMS API)

**Arquitetura atual:** 3 arquivos. `AppManager.js` é uma God Class com toda a lógica (DB init + rotas + business logic). `utils.js` contém credenciais hardcoded. `app.js` é o entry point minimal.

| # | Severidade | Problema | Arquivo:Linha | Justificativa |
|---|-----------|----------|---------------|---------------|
| 1 | **CRITICAL** | **Credenciais hardcoded** — Senha de banco, chave de gateway de pagamento e credenciais SMTP em texto plano | `utils.js:2-5` | `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`. Chave LIVE de pagamento no código. |
| 2 | **CRITICAL** | **Dados de cartão logados em console** — Número do cartão e chave do gateway impressos no log | `AppManager.js:46` | `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` — dados PCI expostos em logs. |
| 3 | **CRITICAL** | **Criptografia falha** — Função `badCrypto()` que não é hash real | `utils.js:18-22` | Repete `Buffer.from(pwd).substring(0,2)` 10000 vezes e trunca. Não é hash criptográfico, é reversível e previsível. |
| 4 | **HIGH** | **God Class** — `AppManager` concentra inicialização do DB, definição de rotas, lógica de checkout, relatório financeiro e deleção de usuário | `AppManager.js:1-120` | Uma única classe com todas as responsabilidades. Impossível testar isoladamente. Viola SRP completamente. |
| 5 | **HIGH** | **Callback Hell** — Endpoint de checkout com 6 níveis de callbacks aninhados | `AppManager.js:29-73` | Aninhamento profundo: route→db.get(course)→db.get(user)→db.run(insert user)→db.run(enrollment)→db.run(payment)→db.run(audit). Ilegível e não-testável. |
| 6 | **HIGH** | **Deleção de usuário sem cascade** — DELETE de user não remove enrollments e payments órfãos | `AppManager.js:104-108` | A própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco". Integridade referencial violada. |
| 7 | **MEDIUM** | **N+1 Queries no relatório financeiro** — Loop de courses → enrollments → users → payments com queries individuais | `AppManager.js:77-100` | Para cada curso, query de enrollments; para cada enrollment, queries de user e payment. Escala O(cursos × alunos). |
| 8 | **MEDIUM** | **Estado global mutável** — `globalCache` e `totalRevenue` como variáveis globais no módulo utils | `utils.js:8-9` | Cache em memória sem invalidação, compartilhado entre requests. `totalRevenue` nunca é atualizado. |
| 9 | **MEDIUM** | **Nomes de variáveis crípticos** — Parâmetros do checkout com nomes de 1-3 letras | `AppManager.js:30-34` | `u`, `e`, `p`, `cid`, `cc` — zero legibilidade. Dificulta manutenção e code review. |
| 10 | **LOW** | **Lógica de pagamento falsa** — Cartão aprovado/recusado baseado apenas no primeiro dígito | `AppManager.js:48` | `cc.startsWith("4") ? "PAID" : "DENIED"` — simulação frágil que pode mascarar bugs em integração real. |
| 11 | **LOW** | **Sem validação de input no checkout** — Sem verificação de formato de email, tamanho de senha, formato do cartão | `AppManager.js:36` | Apenas verifica se campos existem (`!u || !e || !cid || !cc`), sem validar formato ou conteúdo. |
| 12 | **LOW** | **Express deprecated** — Versão `^4.18.2` (Express 4.x está em modo manutenção, Express 5.x é o recomendado) | `package.json:10` | Express 4 está em manutenção. Express 5 traz melhorias de segurança e async handling nativo. |

---

### Projeto 3 — `task-manager-api` (Python/Flask — Task Manager)

**Arquitetura atual:** Organização parcial com `models/`, `routes/`, `services/`, `utils/`. Usa SQLAlchemy ORM. Porém, falta camada de controllers — toda lógica de negócio está nas routes. Services praticamente não são usados.

| # | Severidade | Problema | Arquivo:Linha | Justificativa |
|---|-----------|----------|---------------|---------------|
| 1 | **CRITICAL** | **Hash MD5 para senhas** — Usa `hashlib.md5()` que é criptograficamente inseguro para hashing de senhas | `models/user.py:29,32` | MD5 é vulnerável a rainbow tables e colisões. Deve usar bcrypt ou argon2. |
| 2 | **CRITICAL** | **Credenciais SMTP hardcoded** — Email e senha do serviço de notificação em texto plano | `services/notification_service.py:9-10` | `email_password = 'senha123'` diretamente no código. Credenciais expostas no repositório. |
| 3 | **HIGH** | **Senha exposta no to_dict()** — O método `to_dict()` do User retorna o hash da senha nas respostas da API | `models/user.py:21` | Todo GET de usuário retorna o campo `password`. Dados sensíveis vazam na API. |
| 4 | **HIGH** | **Ausência de camada Controller** — Lógica de negócio (validação, transformação, orquestração) vive nas routes | `routes/task_routes.py:85-154`, `routes/user_routes.py:42-90` | Routes fazem validação de dados, consultas ao banco, transformação e resposta. Viola MVC — routes deveriam ser apenas views/roteamento. |
| 5 | **HIGH** | **Token JWT falso** — Login retorna `'fake-jwt-token-' + str(user.id)` | `routes/user_routes.py:210` | Não há autenticação real. Qualquer endpoint pode ser acessado sem token. Sem middleware de auth. |
| 6 | **MEDIUM** | **Código duplicado — lógica overdue** — Mesma verificação de task atrasada repetida 5 vezes em 3 arquivos | `routes/task_routes.py:30-39,71-80,283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43` | Lógica idêntica copiad/colada. O model `Task` já tem `is_overdue()` mas nunca é usado nas routes. |
| 7 | **MEDIUM** | **SECRET_KEY hardcoded** — Chave secreta no código-fonte | `app.py:13` | `SECRET_KEY = 'super-secret-key-123'` — deve vir de variável de ambiente. |
| 8 | **MEDIUM** | **Bare except clauses** — `except:` sem capturar a exceção em múltiplos locais | `routes/task_routes.py:62,137,204,236`, `routes/user_routes.py:130,149`, `routes/report_routes.py:186,208,221` | Engole qualquer exceção sem logging. Bugs silenciosos. Inclui SystemExit e KeyboardInterrupt. |
| 9 | **LOW** | **Imports não utilizados** — Módulos importados mas nunca usados | `routes/task_routes.py:7` (`json, os, sys, time`), `app.py:7` (`os, sys, json`) | Imports mortos poluem o namespace e confundem leitores. |
| 10 | **LOW** | **Funções utilitárias não usadas** — `process_task_data()` e constantes definidas em helpers nunca são chamadas | `utils/helpers.py:57-116` | Código morto. `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH` etc. definidos mas cada route re-define seus próprios valores inline. |
| 11 | **LOW** | **`datetime.utcnow()` deprecated** — Uso de `datetime.utcnow()` que foi deprecated no Python 3.12+ | `models/task.py:15-16`, `models/user.py:14`, `models/category.py:11`, e em várias routes | Deve usar `datetime.now(datetime.UTC)` a partir do Python 3.12. |
| 12 | **LOW** | **Print statements como logging** — `print()` e f-strings para logging | `routes/task_routes.py:149,153,219,234`, `routes/user_routes.py:83,89,147` | Sem nível de log, sem formatação, inadequado para produção. |

---

## 2. Estrutura da Skill

### Localização

```
code-smells-project/.claude/skills/refactor-arch/
├── SKILL.md                    # Prompt principal (orquestrador das 3 fases)
├── 01-project-analysis.md      # Heurísticas de detecção de stack e mapeamento de arquitetura
├── 02-anti-patterns-catalog.md # Catálogo de anti-patterns com sinais de detecção
├── 03-audit-report-template.md # Template padronizado do relatório de auditoria
├── 04-mvc-architecture.md      # Guidelines da arquitetura MVC alvo
└── 05-refactoring-playbook.md  # Padrões de transformação com exemplos antes/depois
```

### Design do SKILL.md

O SKILL.md é o prompt principal que instrui o agente. Deve:

1. Definir as 3 fases sequenciais com outputs claros
2. Referenciar os arquivos de referência para cada fase
3. Ser agnóstico de tecnologia (não mencionar Python/Flask ou Node/Express especificamente)
4. Incluir a pausa obrigatória entre Fase 2 e Fase 3
5. Definir critérios de validação para a Fase 3

### Conteúdo dos Arquivos de Referência

#### 01-project-analysis.md — Análise de Projeto
- Heurísticas para detectar linguagem (extensões, imports, package managers)
- Detecção de framework (imports/requires específicos, config files)
- Mapeamento de banco de dados (imports de drivers, ORM patterns, schema definitions)
- Classificação de arquitetura (monolítica, parcialmente organizada, já MVC)
- Contagem de arquivos, linhas de código, tabelas/models
- Detecção do domínio da aplicação (endpoints, models, tabelas)
- Output esperado formatado

#### 02-anti-patterns-catalog.md — Catálogo de Anti-Patterns (mínimo 8)
Cada anti-pattern deve ter: nome, severidade, sinais de detecção, impacto.

1. **SQL Injection** (CRITICAL) — Concatenação de strings em queries SQL
2. **Hardcoded Credentials** (CRITICAL) — Senhas, API keys, secrets no código
3. **Insecure Hashing** (CRITICAL) — MD5/SHA1 para senhas, crypto caseira
4. **God Class / God File** (HIGH) — Arquivo/classe com múltiplas responsabilidades
5. **Business Logic in Routes/Controllers** (HIGH) — Lógica de negócio fora do model/service
6. **N+1 Queries** (MEDIUM) — Query dentro de loop
7. **Code Duplication** (MEDIUM) — Blocos de código repetidos
8. **Deprecated APIs** (MEDIUM) — Uso de APIs/funções/frameworks obsoletos
9. **Bare Except / Silent Errors** (MEDIUM) — Except genérico sem tratamento
10. **Missing Authentication/Authorization** (HIGH) — Endpoints sensíveis sem auth
11. **Sensitive Data Exposure** (HIGH) — Senhas/tokens retornados em respostas da API
12. **Print Statements as Logging** (LOW) — print() ao invés de logging estruturado
13. **Dead Code** (LOW) — Código não utilizado (imports, funções, variáveis)
14. **Magic Numbers/Strings** (LOW) — Valores literais sem constantes nomeadas

#### 03-audit-report-template.md — Template de Relatório
- Header com metadados (projeto, stack, arquivos, LOC)
- Summary com contagem por severidade
- Findings ordenados por severidade (CRITICAL → LOW)
- Cada finding: severidade, nome, arquivo:linhas, descrição, impacto, recomendação
- Footer com total de findings

#### 04-mvc-architecture.md — Guidelines MVC
- Estrutura de diretórios alvo para Python/Flask e Node.js/Express
- Responsabilidades de cada camada:
  - **Models:** Representação de dados, validação de schema, acesso ao banco
  - **Views/Routes:** Roteamento HTTP, serialização de request/response
  - **Controllers:** Orquestração, lógica de negócio, coordenação entre models
- Config: extração de configurações para módulo separado (env vars)
- Error handling: middleware centralizado
- Entry point: composition root limpo
- Regras de dependência entre camadas

#### 05-refactoring-playbook.md — Playbook de Refatoração (mínimo 8 transformações)
Cada transformação com exemplo antes/depois:

1. **SQL Injection → Parameterized Queries** — Concatenação → `?` placeholders / ORM
2. **Hardcoded Credentials → Environment Variables** — Literais → `os.environ` / `process.env`
3. **Insecure Hashing → Secure Hashing** — MD5 → bcrypt/argon2
4. **God Class → Separated Modules** — Monolito → models + controllers + routes
5. **Business Logic in Routes → Controller Layer** — Route handler → controller + route
6. **N+1 Queries → JOINs / Eager Loading** — Loop queries → query única com JOIN
7. **Callback Hell → Async/Await** — Callbacks aninhados → async/await (Node.js)
8. **Global State → Dependency Injection** — Variáveis globais → injeção de dependências
9. **Print → Logging** — `print()` → `logging` module / winston
10. **Bare Except → Specific Exception Handling** — `except:` → `except SpecificError as e:`
11. **Sensitive Data Exposure → Response Filtering** — Remover campos sensíveis dos dicts de resposta
12. **Dead Code → Cleanup** — Remover imports e funções não utilizados

---

## 3. Plano de Execução

### Etapa 1 — Criar a Skill (dentro de `code-smells-project/`)

1. Criar diretório `code-smells-project/.claude/skills/refactor-arch/`
2. Escrever `SKILL.md` — prompt principal com as 3 fases
3. Escrever `01-project-analysis.md`
4. Escrever `02-anti-patterns-catalog.md`
5. Escrever `03-audit-report-template.md`
6. Escrever `04-mvc-architecture.md`
7. Escrever `05-refactoring-playbook.md`

### Etapa 2 — Executar no Projeto 1 (`code-smells-project/`)

1. Navegar até `code-smells-project/`
2. Invocar `claude "/refactor-arch"`
3. Validar Fase 1 (stack detectada corretamente)
4. Validar Fase 2 (≥5 findings, ≥1 CRITICAL/HIGH, relatório no template)
5. Confirmar Fase 3
6. Validar resultado (app inicia, endpoints funcionam)
7. Salvar relatório em `reports/audit-project-1.md`
8. Commitar código refatorado

### Etapa 3 — Executar no Projeto 2 (`ecommerce-api-legacy/`)

1. Copiar `.claude/skills/refactor-arch/` de `code-smells-project/` para `ecommerce-api-legacy/`
2. Navegar até `ecommerce-api-legacy/`
3. Invocar `claude "/refactor-arch"`
4. Validar as 3 fases
5. Salvar relatório em `reports/audit-project-2.md`
6. Commitar código refatorado

### Etapa 4 — Executar no Projeto 3 (`task-manager-api/`)

1. Copiar `.claude/skills/refactor-arch/` de `code-smells-project/` para `task-manager-api/`
2. Navegar até `task-manager-api/`
3. Invocar `claude "/refactor-arch"`
4. Validar as 3 fases (atenção: projeto já tem organização parcial)
5. Salvar relatório em `reports/audit-project-3.md`
6. Commitar código refatorado

### Etapa 5 — Documentação

1. Criar `SUBMISSION.md` na raiz com as seções exigidas:
   - **A) Análise Manual** — Problemas identificados por projeto (baseado neste plano)
   - **B) Construção da Skill** — Decisões de design, anti-patterns, agnosticismo
   - **C) Resultados** — Resumo dos relatórios, antes/depois, checklists, screenshots
   - **D) Como Executar** — Pré-requisitos e comandos
2. Criar pasta `reports/` com os 3 relatórios

### Etapa 6 — Iteração (se necessário)

Se alguma execução falhar ou não atingir os critérios mínimos:
1. Ajustar os arquivos de referência da skill
2. Re-executar no projeto problemático
3. Atualizar relatórios e documentação

---

## 4. Critérios de Aceite (Checklist)

Para **cada** um dos 3 projetos:

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente

---

## 5. Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| Skill muito acoplada a Python/Flask | Média | Manter exemplos genéricos nos arquivos de referência; testar em Node.js cedo |
| Refatoração quebra endpoints | Alta | Fase 3 deve incluir testes manuais com curl/httpie; validar cada endpoint |
| Skill não detecta problemas suficientes | Média | Catálogo amplo de anti-patterns com sinais de detecção específicos |
| Projeto 3 já organizado → poucas mudanças | Baixa | Skill deve identificar problemas de código (segurança, qualidade) além de estruturais |
| SQLite em memória (Projeto 2) perde dados no restart | Baixa | Verificar que seeds são mantidos no boot da app refatorada |

---

## 6. Estrutura Final Esperada do Repositório

```
mba-ia-refactor-projects-skill/
├── README.md                              # Original (mantido)
├── SUBMISSION.md                          # Documentação do entregável
│
├── code-smells-project/
│   ├── .claude/skills/refactor-arch/      # SKILL ORIGINAL
│   │   ├── SKILL.md
│   │   ├── 01-project-analysis.md
│   │   ├── 02-anti-patterns-catalog.md
│   │   ├── 03-audit-report-template.md
│   │   ├── 04-mvc-architecture.md
│   │   └── 05-refactoring-playbook.md
│   └── (código refatorado em MVC)
│
├── ecommerce-api-legacy/
│   ├── .claude/skills/refactor-arch/      # CÓPIA DA SKILL
│   └── (código refatorado em MVC)
│
├── task-manager-api/
│   ├── .claude/skills/refactor-arch/      # CÓPIA DA SKILL
│   └── (código refatorado em MVC)
│
└── reports/
    ├── audit-project-1.md
    ├── audit-project-2.md
    └── audit-project-3.md
```
