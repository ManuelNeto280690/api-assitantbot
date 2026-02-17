#!/bin/bash

# Script para conectar ao GitHub e fazer push inicial

echo "🚀 Configurando GitHub..."
echo ""
echo "Por favor, forneça as seguintes informações:"
echo ""

# Solicitar informações do usuário
read -p "Seu nome de usuário do GitHub: " GITHUB_USER
read -p "Nome do repositório (ex: api-assitantbot): " REPO_NAME

# Configurar remote
echo ""
echo "📡 Conectando ao repositório..."
git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git

# Renomear branch para main
git branch -M main

# Push inicial
echo ""
echo "📤 Enviando código para o GitHub..."
git push -u origin main

echo ""
echo "✅ Código enviado com sucesso!"
echo ""
echo "🔗 Repositório: https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "📋 Próximos passos:"
echo "1. Acesse seu Easypanel"
echo "2. Crie um novo projeto"
echo "3. Conecte ao repositório GitHub: $GITHUB_USER/$REPO_NAME"
echo "4. Configure as variáveis de ambiente (veja DEPLOY.md)"
echo "5. Ative Auto-Deploy"
echo ""
echo "🎉 Pronto! Agora toda alteração será deployada automaticamente!"
