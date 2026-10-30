# AGENTS.md — Diretrizes para Agentes do Projeto encurtador-url

## Visão Geral
Sistema de encurtador de URLs em **FastAPI** + **Python 3.11+**, armazenamento em **JSON local** (`urls.json`). Zero dependências externas além de `fastapi`, `uvicorn`, `pydantic`, `python-multipart`.

---

## Os 5 Papéis do Time
- **Você** = Dono (Aprovador final)
- **Hermes** = Gerente (Orquestrador e criador de tarefas)
- **Linear** = Mural (Status e gerenciamento visual)
- **Orca** = Braço Dev (Escreve o código da aplicação)
- **Ponytail 5** = Braço QA (Garante segurança, caça bugs, roda testes de estresse, valida PRs)

---

## Estrutura de Arquivos
```
encurtador-url/
├── main.py           # App FastAPI + rotas
├── models.py         # Pydantic models (URLCreate, URLResponse, URLInDB)
├── storage.py        # Funções save_url(), get_url() com file lock
├── requirements.txt  # Dependências
├── urls.json         # Banco de dados local (formato: {"abc123": "https://..."})
├── tests/            # Testes pytest
│   ├── test_models.py
│   ├── test_storage.py
│   └── test_routes.py
└── AGENTS.md         # Este arquivo
```

---

## Regras de Ouro (Obrigatórias)

1. **NUNCA exponha segredos** (chaves API, tokens, senhas) no código ou commits.
2. **Validação na borda**: toda entrada externa passa por Pydantic (`HttpUrl` para URLs).
3. **Escrita atômica no JSON**: use `tempfile.NamedTemporaryFile` + `os.replace()` para evitar corrupção.
4. **File lock simples**: `fcntl` (Linux/Mac) ou `msvcrt` (Windows) em `storage.py` para concorrência.
5. **Código curto de 6 chars**: `secrets.token_urlsafe(6)[:6]` — retry até 3x se colisão.
6. **HTTP semântico**: 201 Created (POST), 307 Redirect (GET), 404 Not Found, 422 Validation Error.
7. **Logs mínimos**: `print(f"[INFO] ...")` para debug; nada de libs de log pesadas.
8. **Testes antes de PR**: `pytest -v` deve passar 100%.
9. **Branch por task**: `feature/<nome-task>` → PR para `main` → **NÃO faça merge direto**.
10. **Relatório final**: todo PR inclui `## Resumo` com o que foi feito, arquivos alterados, como testar.

---

## Regras do Ponytail 5 (QA Autônomo) — NOVO

> O Ponytail 5 roda **após** o Orca abrir o PR. Ele clona a branch, executa validações e comenta no PR.

### O que o Ponytail 5 DEVE fazer em cada PR:
1. **Static Analysis**: `ruff check .` + `bandit -r .` (segurança) + `mypy --strict` (tipos).
2. **Testes**: `pytest -v --cov=. --cov-fail-under=80` — cobertura mínima 80%.
3. **Fuzz/Edge Cases**: envie inputs maliciosos nas rotas (SQLi, XSS, path traversal, URLs gigantes, chars Unicode, null bytes).
4. **Performance**: meça tempo de resposta do POST/GET com 1000 iterações — p95 < 50ms.
5. **Memory Leak**: rode `tracemalloc` no storage por 10k ops — sem crescimento linear.
6. **Secret Scan**: `trufflehog` ou `gitleaks` no diff do PR.
7. **Relatório no PR**: comente com:
   - 🟢 **APROVADO** — todos checks passam, selo de qualidade
   - 🔴 **REPROVADO** — lista bugs, falhas, cobertura baixa → task volta pro Orca

### O que o Ponytail 5 NÃO faz:
- ❌ Não escreve código de produção (só testes auxiliares se faltar cobertura)
- ❌ Não faz merge — só aprova/bloqueia
- ❌ Não decide arquitetura — só valida implementação

---

## Convenções de Código

- **Type hints** em tudo (funções, variáveis, retorno).
- **Docstrings** estilo Google em funções públicas.
- **Imports organizados**: stdlib → third-party → local.
- **Constantes em UPPER_SNAKE_CASE** no topo do módulo.
- **Variáveis/funcs em snake_case**, Classes em PascalCase.
- **Sem `async` desnecessário** — só use em I/O real (arquivo, rede).
- **`uvicorn main:app --reload`** para dev; produção usa `--workers 4`.

---

## Fluxo de Trabalho do Agente (Atualizado com Ponytail 5)

```
1. Leia AGENTS.md e entenda a task (5 blocos: TAREFA, CONTEXTO, FRONTEIRAS, REGRAS, ENTREGA)
2. Implemente o mínimo que satisfaz a TAREFA
3. Rode testes locais (pytest -v)
4. Commit + push branch
5. `gh pr create --base main --title "<task>" --body "<relatório>"`
6. PARE — Ponytail 5 assume: roda QA completo no PR
7. Se 🟢 → Hermes mergeia → task fecha no Linear
8. Se 🔴 → Orca corrige → novo push → volta ao passo 6
```

---

## Checklist de PR (auto-verificação antes de abrir)

- [ ] `pytest -v` passa sem erros
- [ ] `ruff check .` (ou `flake8`) sem warnings
- [ ] `bandit -r .` sem findings HIGH/MEDIUM
- [ ] `mypy --strict` passa (opcional mas recomendado)
- [ ] Cobertura `pytest --cov=.` ≥ 80%
- [ ] Nenhum segredo no diff (`git diff --name-only` + `gitleaks`)
- [ ] README/AGENTS.md atualizado se mudou interface
- [ ] Relatório final no corpo do PR

---

## Exemplos de Padrões Esperados

### models.py
```python
from pydantic import BaseModel, HttpUrl

class URLCreate(BaseModel):
    url: HttpUrl

class URLResponse(BaseModel):
    codigo: str
    url_curta: str

class URLInDB(BaseModel):
    codigo: str
    url_original: str
```

### storage.py (esqueleto)
```python
import json, os, secrets, tempfile
from pathlib import Path
try:
    import fcntl
except ImportError:
    import msvcrt as fcntl  # Windows fallback

DB_PATH = Path("urls.json")

def _lock(f):
    fcntl.flock(f, fcntl.LOCK_EX)

def _unlock(f):
    fcntl.flock(f, fcntl.LOCK_UN)

def save_url(code: str, url: str) -> None:
    with open(DB_PATH, "r+") as f:
        _lock(f)
        data = json.load(f)
        data[code] = url
        f.seek(0)
        json.dump(data, f)
        f.truncate()
        _unlock(f)

def get_url(code: str) -> str | None:
    with open(DB_PATH, "r") as f:
        _lock(f)
        data = json.load(f)
        _unlock(f)
    return data.get(code)
```

### main.py (esqueleto rotas)
```python
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from models import URLCreate, URLResponse
import storage, secrets

app = FastAPI()

@app.post("/encurtar", response_model=URLResponse, status_code=201)
def encurtar(payload: URLCreate):
    for _ in range(3):
        code = secrets.token_urlsafe(6)[:6]
        if not storage.get_url(code):
            storage.save_url(code, str(payload.url))
            return URLResponse(codigo=code, url_curta=f"http://localhost:8000/{code}")
    raise HTTPException(500, "Falha ao gerar código único")

@app.get("/{code}")
def redirecionar(code: str):
    url = storage.get_url(code)
    if not url:
        raise HTTPException(404, "Código não encontrado")
    return RedirectResponse(url, status_code=307)
```

---

## Comandos Úteis

```bash
# Instalar deps
pip install -r requirements.txt

# Rodar dev
uvicorn main:app --reload

# Testes
pytest -v

# Testes + cobertura (Ponytail 5 usa isso)
pytest -v --cov=. --cov-fail-under=80

# Segurança estática
bandit -r .

# Lint
ruff check .

# Type check
mypy --strict .

# Formatar
ruff format .

# Secret scan
gitleaks detect --source .
```

---

## O que NÃO fazer

- ❌ Não use banco de dados (SQLite, Redis, etc) — JSON local é requisito.
- ❌ Não adicione autenticação, rate limiting, dashboard, analytics.
- ❌ Não use `async def` nas rotas se não há I/O assíncrono real.
- ❌ Não commite `urls.json` com dados de teste — mantenha vazio `{}`.
- ❌ Não faça `merge` direto na `main` — sempre PR + revisão + Ponytail 5.
- ❌ Não ignore falhas do Ponytail 5 — corrija antes de pedir merge.

---

## Contato / Escalação

Se a task estiver ambígua, **pare e pergunte** no PR ou no Linear. Não assuma.
Dúvidas de arquitetura → dono humano (você).
Bugs de infra (Orca, GitHub, Linear) → dono humano.
Falhas do Ponytail 5 → veja relatório no PR, corrija e faça push.