# 🚀 Guia Completo: Configurar Git e GitHub

## Passo 1: Configurar Git (FAÇA ISSO PRIMEIRO)

Execute estes comandos no PowerShell (substitua com SEU email):

```powershell
# Configurar nome de usuário (já feito)
git config --global user.name "ManuelNeto280690"

# Configurar email (SUBSTITUA com seu email do GitHub)
git config --global user.email "manuel.neto280690@gmail.com"

# Verificar configuração
git config --list
```

## Passo 2: Criar Repositório no GitHub

1. Acesse: **https://github.com/new**
2. Preencha:
   - **Repository name**: `api-assitantbot`
   - **Description**: Multi-Tenant SaaS Backend
   - **Visibility**: 🔒 Private
   - **NÃO marque nenhuma opção** (README, .gitignore, license)
3. Clique em **"Create repository"**

## Passo 3: Autenticar com GitHub

### Opção A: GitHub CLI (Mais Fácil)

```powershell
# Instalar GitHub CLI
winget install --id GitHub.cli

# Fazer login
gh auth login
# Escolha: GitHub.com → HTTPS → Yes → Login with browser
```

### Opção B: Personal Access Token

1. Vá para: **https://github.com/settings/tokens**
2. Clique em **"Generate new token"** → **"Classic"**
3. Configurar:
   - **Note**: `api-assitantbot-deploy`
   - **Expiration**: 90 days (ou No expiration)
   - **Scopes**: Marque `repo` (todas as opções)
4. Clique em **"Generate token"**
5. **COPIE O TOKEN** (você não verá novamente!)
6. Salve em local seguro

### Opção C: SSH (Avançado)

```powershell
# Gerar chave SSH
ssh-keygen -t ed25519 -C "seu-email@exemplo.com"
# Pressione Enter 3 vezes (aceitar padrões)

# Copiar chave pública
cat ~/.ssh/id_ed25519.pub | clip

# Adicionar no GitHub:
# https://github.com/settings/keys
# Clique "New SSH key", cole a chave, salve
```

## Passo 4: Fazer Push do Código

Depois de criar o repositório e autenticar:

```powershell
# Fazer push
git push -u origin main
```

**Se usar Token**: Quando pedir senha, cole o Personal Access Token (não a senha normal)

## Passo 5: Verificar

1. Acesse: `https://github.com/ManuelNeto280690/api-assitantbot`
2. Você deve ver todo o código lá!

## 🔧 Troubleshooting

### Erro: "remote: Repository not found"
- ✅ Certifique-se que criou o repositório no GitHub
- ✅ Verifique se o nome está correto: `api-assitantbot`

### Erro: "Permission denied"
- ✅ Use Personal Access Token como senha
- ✅ Ou configure SSH
- ✅ Ou use GitHub CLI

### Erro: "Authentication failed"
- ✅ Token expirado? Gere um novo
- ✅ Token sem permissão `repo`? Gere novo com permissão

## 📋 Checklist Completo

- [ ] Git configurado com nome e email
- [ ] Repositório criado no GitHub
- [ ] Autenticação configurada (Token/SSH/CLI)
- [ ] Push realizado com sucesso
- [ ] Código visível no GitHub

## 🎯 Próximo Passo: Easypanel

Depois que o código estiver no GitHub, vamos configurar o Easypanel para deploy automático!

Veja o arquivo **DEPLOY.md** para instruções completas.
