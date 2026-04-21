# Desafio de Skills — Refatoração Arquitetural Automatizada

Este repositório contém a entrega do desafio de criação de uma Skill de IA para refatoração arquitetural automatizada. A skill, denominada `refactor-arch`, é capaz de analisar, auditar e refatorar codebases legadas para o padrão MVC, garantindo segurança e qualidade de código de forma agnóstica a tecnologia.

## 1. Análise Manual dos Projetos

Antes da automação, foi realizada uma auditoria manual nos três projetos para identificar os principais gargalos e vulnerabilidades.

### Projeto 1: code-smells-project (Python/Flask)
**Domínio:** API de E-commerce.
- **CRITICAL [SQL Injection]:** Todas as queries em `models.py` utilizam concatenação de strings, permitindo roubo e destruição de dados.
- **CRITICAL [Hardcoded Credentials]:** `SECRET_KEY` exposta diretamente no `app.py`.
- **CRITICAL [Admin Backdoor]:** Endpoint `/admin/query` permite execução de SQL arbitrário sem autenticação.
- **CRITICAL [Plaintext Passwords]:** Senhas armazenadas sem nenhum tipo de hash.
- **HIGH [God File]:** `models.py` concentra toda a lógica de 4 domínios diferentes, violando o SRP.

### Projeto 2: ecommerce-api-legacy (Node.js/Express)
**Domínio:** LMS API com Checkout.
- **CRITICAL [Sensitive Data Exposure]:** Números de cartão de crédito e chaves de API são impressos no console durante o checkout.
- **CRITICAL [Broken Cryptography]:** Função `badCrypto()` em `utils.js` utiliza um algoritmo previsível e reversível para "senhas".
- **HIGH [Callback Hell]:** Lógica de checkout com aninhamento excessivo, tornando o código impossível de testar.
- **HIGH [God Class]:** `AppManager.js` gerencia desde a conexão com o banco até a lógica de negócio e rotas.
- **MEDIUM [N+1 Queries]:** Relatórios financeiros realizam queries individuais dentro de loops de cursos e alunos.

### Projeto 3: task-manager-api (Python/Flask)
**Domínio:** API de Gerenciamento de Tarefas.
- **CRITICAL [Insecure Hashing]:** Utilização de MD5 para hashing de senhas.
- **CRITICAL [Hardcoded SMTP]:** Credenciais de e-mail expostas em `notification_service.py`.
- **HIGH [Sensitive Data Exposure]:** Método `to_dict()` do usuário retorna o hash da senha em todas as respostas da API.
- **HIGH [Architecture Violation]:** Total ausência de camada de Controller; toda a lógica de negócio reside nos arquivos de rotas.
- **HIGH [Fake Auth]:** Sistema de login gera tokens estáticos e não possui middleware de validação real.

---

## 2. Construção da Skill `refactor-arch`

A skill foi projetada para ser um pipeline autônomo de 3 fases, guiado por arquivos de referência em Markdown que provêem o conhecimento especializado necessário.

### Decisões de Design
- **Agnosticismo Tecnológico:** Em vez de regras rígidas por linguagem, a skill utiliza heurísticas de detecção (ex: presença de `package.json` vs `requirements.txt`) e padrões de transformação genéricos baseados em AST e busca semântica.
- **Segurança em Primeiro Lugar:** O catálogo de anti-patterns prioriza vulnerabilidades do OWASP Top 10 (SQLi, Exposição de Dados, Broken Auth).
- **Relatório Estruturado:** A Fase 2 gera um relatório padronizado que classifica os achados por severidade (CRITICAL a LOW), permitindo uma decisão informada do desenvolvedor.
- **Confirmação Obrigatória:** A skill interrompe a execução após a auditoria, exigindo um "sim" explícito do usuário antes de iniciar qualquer modificação destrutiva.

### Arquitetura da Skill
- `SKILL.md`: Orquestrador central das fases.
- `01-project-analysis.md`: Heurísticas de detecção de stack e domínio.
- `02-anti-patterns-catalog.md`: Catálogo com 14 padrões de erro e sinais de detecção.
- `03-audit-report-template.md`: Template para o relatório de auditoria.
- `04-mvc-architecture.md`: Definição das camadas alvo (Models, Controllers, Routes, Config, Middleware).
- `05-refactoring-playbook.md`: Exemplos de transformação "antes/depois" para cada anti-pattern.

---

## 3. Resultados e Validação

A skill foi executada com sucesso nos três projetos, utilizando diferentes agentes de IA para validar a portabilidade do conceito.

### Resumo de Execução

| Projeto | Ferramenta Utilizada | Findings Identificados | Status da Refatoração |
|---------|----------------------|-------------------------|-----------------------|
| code-smells-project | **CLAUDE CODE** | 23 (8 Critical, 7 High) | **SUCESSO** (MVC Completo) |
| ecommerce-api-legacy | **OpenAI Codex** | 20 (5 Critical, 6 High) | **SUCESSO** (MVC + Clean Node) |
| task-manager-api | **Github Copilot** | 29 (4 Critical, 8 High) | **SUCESSO** (MVC + Services) |

### Comparação de Estrutura (Exemplo: code-smells-project)

**Antes (Monolito Flat):**
```text
├── app.py
├── controllers.py
├── database.py
└── models.py
```

**Depois (Padrão MVC):**
```text
├── app.py (Composition Root)
├── config.py (Env Vars)
├── controllers/
│   ├── pedido_controller.py
│   ├── produto_controller.py
│   └── usuario_controller.py
├── middleware/
│   ├── auth.py
│   └── error_handler.py
├── models/
│   ├── database.py (Session management)
│   ├── pedido.py
│   ├── produto.py
│   └── usuario.py
├── routes/
│   ├── pedido_routes.py
│   ├── produto_routes.py
│   └── usuario_routes.py
└── utils/
    └── security.py (Bcrypt hashing)
```

### Checklist de Validação Final
- [x] Linguagem e Framework detectados corretamente em 3/3 projetos.
- [x] Mínimo de 5 findings identificados por projeto.
- [x] Todas as vulnerabilidades CRITICAL (SQLi, Hardcoded Creds) foram corrigidas.
- [x] Separação clara entre Rotas (HTTP) e Controllers (Business Logic).
- [x] Aplicações iniciam sem erros após a refatoração.
- [x] Endpoints originais mantidos e funcionais.

---

## 4. Como Executar

### Pré-requisitos
- Uma das ferramentas instaladas: `claude` (Claude Code), `gemini` (Gemini CLI) ou `codex`.
- Variáveis de ambiente configuradas para o provedor de IA correspondente.

### Comandos
Para executar a refatoração em qualquer um dos projetos:

```bash
# Entre na pasta do projeto
cd code-smells-project

# Invoque a skill
# No Claude Code:
claude "/refactor-arch"

# No Gemini CLI:
gemini "/refactor-arch"
```

### Validação
Após a execução, os relatórios detalhados podem ser encontrados na pasta `reports/` na raiz deste repositório. Para validar o funcionamento das APIs refatoradas, execute:

```bash
# Python/Flask
python app.py

# Node.js
npm install && npm start
```
