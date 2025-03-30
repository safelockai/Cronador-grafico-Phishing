#!/bin/bash

echo "Atualizando pacotes..."
pkg update -y && pkg upgrade -y

echo "Instalando pacotes básicos..."
pkg install python git -y

echo "Instalando pip e ferramentas necessárias..."
pip install --upgrade pip
pip install flask beautifulsoup4 requests

echo "Instalação concluída!"
echo "Para rodar a ferramenta, use o comando: python phishing_tool.py"
