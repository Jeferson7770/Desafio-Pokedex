# Desafio Técnico - Pokédex Analítica 🚀

Este repositório contém a solução para o desafio técnico de integração de dados com a PokeAPI.

## 📂 Estrutura do Projeto

* `pokemon_base.csv`: Lista inicial de Pokémons.
* `pokemon_completo.csv`: Arquivo final com dados consolidados e enriquecidos via PokeAPI.
* `respostas.txt`: Respostas para as perguntas de negócio do Time de Produto (incluindo o bônus).
* `dashboard.html`: Painel interativo gerado para visualização dinâmica dos dados.
* `main.py`: Script principal que realiza a extração, tratamento de erros, geração dos arquivos e cache local.


<img width="1866" height="874" alt="image" src="https://github.com/user-attachments/assets/96648a75-a2ba-47ae-81c5-b4493876a756" />

## 📊 Respostas

```text
1. Pokémon com maior soma de stats (BST):
   -> Mewtwo (680 BST)

2. Tipo com maior média de Attack da lista:
   -> Tipo DRAGON (média de ataque: 133.00)

3. Quantidade de Pokémon do tipo Water:
   -> 5 Pokémon

4. Os 5 Pokémon mais rápidos:
   -> Mewtwo (130), Greninja (122), Alakazam (120), Raichu (110), Gengar (110)

5. Time dos Sonhos (6 melhores somas de stats):
   -> Mewtwo (680), Dragonite (600), Tyranitar (600), Salamence (600), Metagross (600), Garchomp (600)
```


## ⚙️ Como Executar

1. Instale as dependências: 
   `pip install requests`

2. Execute o script: 
   `python src/enriquecer_pokedex.py`
