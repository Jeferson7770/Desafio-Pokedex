# Desafio Técnico - Pokédex Analítica 🚀

Este repositório contém a solução para o desafio técnico de integração de dados com a PokeAPI.

## 📂 Estrutura do Projeto

* `pokemon_base.csv`: Lista inicial de Pokémons.
* `pokemon_completo.csv`: Arquivo final com dados consolidados e enriquecidos via PokeAPI.
* `respostas.txt`: Respostas para as perguntas de negócio do Time de Produto (incluindo o bônus).
* `dashboard.html`: Painel interativo gerado para visualização dinâmica dos dados.
* `main.py`: Script principal que realiza a extração, tratamento de erros, geração dos arquivos e cache local.

![alt text](image.png)

## ⚙️ Como Executar

1. Instale as dependências: 
   `pip install requests`

2. Execute o script: 
   `python src/enriquecer_pokedex.py`