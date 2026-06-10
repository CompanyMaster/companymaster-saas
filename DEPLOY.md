# Deploy do SaaS MVP — Guia Completo (Free Tier)

## ✅ Plataforma Recomendada: **Railway**

**Railway** é a MELHOR opção para este MVP porque:
1. ✅ **Sem cartão de crédito** — Free Trial com $5 créditos + Free plan depois
2. ✅ **Persistência de dados** — 0.5 GB de volume storage (SQLite sobrevive a restarts!)
3. ✅ **Python puro** — Aceita script Python sem `requirements.txt`
4. ✅ **Deploy via CLI** — `railway up` ou git push
5. ✅ **Domínio público** — URL pública com HTTPS automático

---

## 📊 Comparativo das Plataformas

| Critério | Railway | Render | Vercel | Fly.io |
|----------|---------|--------|--------|--------|
| **Sem cartão** | ✅ SIM | ✅ SIM | ✅ SIM | ❌ Requer cartão |
| **SQLite persiste** | ✅ Volume storage | ❌ Ephemeral (perde dados) | ❌ Serverless | ✅ (com volumes pagos) |
| **Python puro** | ✅ Nixpacks detecta | ✅ Native runtime | ⚠️ Serverless (BaseHTTPHandler) | ✅ Docker |
| **Free tier real** | ✅ $0/mês + trial $5 | ✅ 750h/mês (spin down 15min) | ✅ Hobby | ❌ Só trial |
| **Deploy CLI** | ✅ `railway up` | ✅ Git push | ✅ Vercel CLI | ✅ `flyctl` |
| **Limite RAM free** | 0.5 GB | 0.5 GB | 1 GB (functions) | N/A |

---

## 🚀 Passos Exatos de Deploy no Railway

### Pré-requisitos (no computador do Caio)

- [ ] Conta no GitHub (gratuita) — https://github.com
- [ ] Git instalado — `sudo apt install git`
- [ ] Railway CLI instalado

### 1. Criar conta no Railway (NO Credit Card!)

```
1. Acesse: https://railway.com
2. Clique em "Login" (canto superior direito)
3. Escolha "Login with GitHub" (ou Google)
4. Autorize o Railway a acessar sua conta
5. Pronto! Você recebe $5 em créditos automaticamente (30 dias)
```

**Link direto**: https://railway.com/login

⚠️ **IMPORTANTE**: Railway NÃO pede cartão de crédito na inscrição. Se pedir, está na página errada.

### 2. Preparar o código para deploy

Antes do deploy, precisamos ajustar o `server.py` para usar caminhos relativos e a porta do Railway:

```python
# Alterar em server.py (linhas 26-28):
# DE:
BASE_DIR = Path("/opt/data/projetos/saas")
DATA_DIR = BASE_DIR / "data"

# PARA:
import os
BASE_DIR = Path(__file__).resolve().parent  # diretório do script
DATA_DIR = BASE_DIR / "data"

# E a porta (linha 29):
# DE:
PORT = 8080

# PARA:
PORT = int(os.environ.get("PORT", 8080))
```

⚠️ Railway injeta a variável `PORT` automaticamente. O servidor DEVE escutar nessa porta.

### 3. Criar arquivo `railway.toml` na raiz do projeto

Crie `/opt/data/projetos/saas/railway.toml`:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python server.py"
```

Isso diz ao Railway:
- Use Nixpacks para detectar a linguagem (Python)
- Execute `python server.py` como comando de start

### 4. Instalar Railway CLI

```bash
# Linux/macOS:
curl -fsSL https://railway.com/install.sh | sh

# Ou via npm:
npm install -g @railway/cli

# Verificar instalação:
railway --version
```

### 5. Fazer login no CLI

```bash
railway login
```

Isso abre o navegador para autorizar. Se estiver em servidor headless:
```bash
railway login --browserless
```

### 6. Criar projeto e fazer deploy

```bash
cd /opt/data/projetos/saas

# Inicializar o projeto no Railway
railway init

# Fazer deploy!
railway up
```

O `railway up` vai:
1. Compactar e enviar o código
2. Detectar que é Python (via Nixpacks)
3. Instalar Python (se necessário)
4. Executar `python server.py`
5. Gerar uma URL pública (ex: `https://saas-mvp.up.railway.app`)

### 7. Verificar se está rodando

```bash
# Abrir o dashboard
railway open

# Ver logs
railway logs

# Verificar saúde
curl https://SEU_APP.up.railway.app/health
```

### 8. (Opcional) Deploy via Git Push

Conecte o repositório GitHub ao Railway para deploy automático:

1. No dashboard: Project > Settings > Source > GitHub
2. Conecte o repo
3. Todo `git push` = deploy automático

---

## 🔄 Alternativa: Deploy no Render

Se Railway não funcionar por algum motivo, Render é o plano B:

### Render Free Tier
- ✅ Sem cartão de crédito (Hobby plan)
- ✅ 750 horas/mês grátis
- ❌ **SQLite perde dados no spin-down** (a cada 15 min sem tráfego)
- ❌ Spin-up demora ~1 minuto

### Passos Render:

1. Criar conta: https://dashboard.render.com/register
2. New > Web Service
3. Conectar repositório GitHub
4. Configurar:
   - **Runtime**: Python 3
   - **Build Command**: (deixar vazio — sem requirements.txt)
   - **Start Command**: `python server.py`
   - **Instance Type**: Free
5. Adicionar variável de ambiente: `PORT` = `8080`
6. Deploy!

---

## ⚠️ Notas Importantes

### Sobre o SQLite no Railway

O Railway oferece **0.5 GB de volume storage** no plano free. O banco SQLite será salvo em disco persistente e sobreviverá a restarts e redeploys.

**MAS ATENÇÃO**: O caminho do banco precisa estar dentro do diretório do projeto (ou `/data` no volume). Ajuste o código:

```python
# Use caminho relativo ao script ou variável de ambiente
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
```

### Sobre a porta

Railway define a variável `PORT` automaticamente. Modifique `server.py`:

```python
PORT = int(os.environ.get("PORT", 8080))
```

### Sobre a landing page

A landing page (`landing-page.html`) pode ser servida pelo próprio `http.server` (adicionando uma rota GET) ou deployada separadamente como static site no Render.

---

## 📋 Checklist para o Caio

- [ ] Criar conta no GitHub (se não tiver): https://github.com/signup
- [ ] Criar conta no Railway: https://railway.com/login
- [ ] Ajustar `server.py` (caminhos relativos + PORT variável)
- [ ] Criar `railway.toml` na raiz do projeto
- [ ] Instalar Railway CLI: `curl -fsSL https://railway.com/install.sh | sh`
- [ ] Login: `railway login`
- [ ] Deploy: `cd /opt/data/projetos/saas && railway up`
- [ ] Testar: `curl https://SEU_APP.up.railway.app/health`

---

## 📞 Contas/Serviços que o Caio precisa criar

| Serviço | Link | Cartão? | Custo |
|---------|------|---------|-------|
| GitHub | https://github.com/signup | Não | Grátis |
| Railway | https://railway.com/login | Não | Grátis (trial $5) |

**NENHUM cartão de crédito necessário.**

---

## 🔗 Referências

- Railway Pricing: https://railway.com/pricing
- Railway Quick Start: https://docs.railway.com/quick-start
- Railway CLI: https://docs.railway.com/cli
- Render Free Tier: https://docs.render.com/free
- Código do SaaS: `/opt/data/projetos/saas/server.py`
