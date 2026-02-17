# 📤 Guia Rápido: Atualizar Código no GitHub

## Fluxo de Trabalho Diário

### Passo a Passo

```bash
# 1️⃣ Ver o que mudou
git status

# 2️⃣ Adicionar alterações
git add .

# 3️⃣ Criar commit com descrição
git commit -m "Descrição clara do que você fez"

# 4️⃣ Enviar para GitHub
git push origin main
```

### ⚡ Atalho (tudo de uma vez)

```bash
git add . && git commit -m "Sua mensagem aqui" && git push origin main
```

## 📝 Boas Práticas para Mensagens de Commit

### ✅ Boas Mensagens

```bash
git commit -m "Add user authentication endpoint"
git commit -m "Fix campaign scheduler timezone bug"
git commit -m "Update Dockerfile healthcheck"
git commit -m "Add rate limiting to API"
```

### ❌ Mensagens Ruins

```bash
git commit -m "fix"
git commit -m "update"
git commit -m "changes"
git commit -m "asdf"
```

## 🎯 Cenários Comuns

### Cenário 1: Adicionei uma nova funcionalidade

```bash
git add .
git commit -m "Add WhatsApp integration with Brevo"
git push origin main
```

### Cenário 2: Corrigi um bug

```bash
git add .
git commit -m "Fix timezone calculation in campaign scheduler"
git push origin main
```

### Cenário 3: Atualizei documentação

```bash
git add .
git commit -m "Update README with deployment instructions"
git push origin main
```

### Cenário 4: Alterei configuração

```bash
git add .
git commit -m "Update Docker configuration for production"
git push origin main
```

## 🔄 Com Easypanel Configurado

Quando você tiver o Easypanel configurado com Auto-Deploy:

```bash
# Você faz alterações no código
# Depois:

git add .
git commit -m "Add new feature"
git push origin main

# ⏱️ Aguarde 2-5 minutos
# ✅ Easypanel detecta, faz build e deploy automaticamente!
```

## 🛠️ Comandos Úteis

### Ver histórico de commits

```bash
git log --oneline -10
```

### Ver diferenças antes de commitar

```bash
git diff
```

### Ver status detalhado

```bash
git status
```

### Desfazer último commit (mantém alterações)

```bash
git reset --soft HEAD~1
```

### Ver arquivos alterados

```bash
git diff --name-only
```

## 🚨 Troubleshooting

### Erro: "nothing to commit"

Significa que não há alterações. Tudo está atualizado!

### Erro: "Your branch is behind"

Alguém fez alterações no GitHub. Baixe primeiro:

```bash
git pull origin main
```

### Erro: "merge conflict"

Há conflitos. Resolva manualmente e depois:

```bash
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

## 📋 Checklist Antes de Push

- [ ] Código funciona localmente?
- [ ] Sem erros de sintaxe?
- [ ] Mensagem de commit é clara?
- [ ] Não está commitando arquivos sensíveis (.env)?
- [ ] Testou as alterações?

## 🎓 Dicas Profissionais

1. **Commit frequentemente**: Pequenos commits são melhores que um grande
2. **Mensagens claras**: Facilita encontrar alterações depois
3. **Teste antes de push**: Evita quebrar o código em produção
4. **Use branches**: Para features grandes, crie uma branch separada

### Exemplo com Branch

```bash
# Criar nova branch para feature
git checkout -b feature/nova-funcionalidade

# Fazer alterações...
git add .
git commit -m "Add nova funcionalidade"

# Enviar branch
git push origin feature/nova-funcionalidade

# Depois, fazer merge no main via GitHub Pull Request
```

## ✅ Resumo

**Workflow básico diário:**

```bash
# Trabalhar no código...
# Quando terminar:

git add .
git commit -m "Descrição clara"
git push origin main

# Se tiver Easypanel: aguardar deploy automático!
```

**É isso! Simples e eficiente.** 🚀
