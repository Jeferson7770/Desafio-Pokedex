import os
import csv
import json
import time
import webbrowser
import requests

# Configurações de Arquivos
BASE_CSV = "pokemon_base.csv"
COMPLETO_CSV = "pokemon_completo.csv"
CACHE_FILE = "poke_cache.json"
RESP_FILE = "respostas.txt"
HTML_FILE = "dashboard.html"

# Imagem padrão caso ocorra alguma falha geral de rede
DEFAULT_SPRITE = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png"
)

TYPE_COLORS = {
    "normal": "bg-gray-400 text-white",
    "fire": "bg-red-500 text-white",
    "water": "bg-blue-500 text-white",
    "electric": "bg-yellow-400 text-gray-900",
    "grass": "bg-green-500 text-white",
    "ice": "bg-blue-300 text-gray-900",
    "fighting": "bg-red-700 text-white",
    "poison": "bg-purple-500 text-white",
    "ground": "bg-yellow-600 text-white",
    "flying": "bg-indigo-400 text-white",
    "psychic": "bg-pink-500 text-white",
    "bug": "bg-green-600 text-white",
    "rock": "bg-yellow-700 text-white",
    "ghost": "bg-purple-700 text-white",
    "dragon": "bg-indigo-700 text-white",
    "steel": "bg-gray-500 text-white",
    "fairy": "bg-pink-300 text-gray-900",
    "dark": "bg-gray-800 text-white",
}


def garantir_csv_base():
    print(f"[*] Sincronizando {BASE_CSV} com a lista oficial de 30 Pokémon...")
    pokemon_oficiais = [
        ("6", "charizard"),
        ("9", "blastoise"),
        ("25", "pikachu"),
        ("26", "raichu"),
        ("31", "nidoqueen"),
        ("34", "nidoking"),
        ("59", "arcanine"),
        ("65", "alakazam"),
        ("68", "machamp"),
        ("76", "golem"),
        ("94", "gengar"),
        ("103", "exeggutor"),
        ("130", "gyarados"),
        ("131", "lapras"),
        ("143", "snorlax"),
        ("149", "dragonite"),
        ("150", "mewtwo"),
        ("157", "typhlosion"),
        ("160", "feraligatr"),
        ("196", "espeon"),
        ("212", "scizor"),
        ("248", "tyranitar"),
        ("257", "blaziken"),
        ("282", "gardevoir"),
        ("306", "aggron"),
        ("373", "salamence"),
        ("376", "metagross"),
        ("445", "garchomp"),
        ("448", "lucario"),
        ("658", "greninja"),
        # ENTIDADE INVÁLIDA 
        ("9999", "pokemon_fantasma_invalido"),
    ]
    with open(BASE_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "nome"])
        writer.writerows(pokemon_oficiais)


def carregar_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)


def obter_matchups_tipo(tipo, cache_matchups):
    if tipo in cache_matchups:
        return cache_matchups[tipo]
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/type/{tipo}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            double_to = [
                t["name"] for t in data["damage_relations"]["double_damage_to"]
            ]
            double_from = [
                t["name"] for t in data["damage_relations"]["double_damage_from"]
            ]
            cache_matchups[tipo] = {"vantagens": double_to, "fraquezas": double_from}
            return cache_matchups[tipo]
    except Exception as e:
        print(f"[!] Erro ao buscar matchups para o tipo {tipo}: {e}")
    return {"vantagens": [], "fraquezas": []}


def main():
    garantir_csv_base()
    cache = carregar_cache()
    pokemon_completo = []
    cache_matchups = {}

    with open(BASE_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        lista_pokemon = list(reader)

    print(f"[*] Processando {len(lista_pokemon)} Pokémons...")

    for idx, row in enumerate(lista_pokemon, start=1):
        id_original = row["id"]
        nome_original = row["nome"]
        nome_clean = nome_original.strip().lower()

        # Se já estiver no cache, carrega localmente e economiza requisições
        if nome_clean in cache:
            pokemon_completo.append(cache[nome_clean])
            continue

        # Consulta na PokeAPI oficial
        print(f"    [{idx}/{len(lista_pokemon)}] Buscando '{nome_original}' na API...")
        try:
            url = f"https://pokeapi.co/api/v2/pokemon/{nome_clean}"
            response = requests.get(url, timeout=5)

            # --- TRATAMENTO DE ERRO 
            if response.status_code == 404:
                print(
                    f"    [⚠] Erro Tratado: '{nome_original}' (ID {id_original}) não existe na API. Pulando sem quebrar o script!"
                )
                continue

            response.raise_for_status()
            data = response.json()

            # Extração de dados
            tipos = [t["type"]["name"] for t in data["types"]]
            stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}

            hp = stats.get("hp", 0)
            attack = stats.get("attack", 0)
            defense = stats.get("defense", 0)
            sp_atk = stats.get("special-attack", 0)
            sp_def = stats.get("special-defense", 0)
            speed = stats.get("speed", 0)
            soma_stats = hp + attack + defense + sp_atk + sp_def + speed

            sprite = DEFAULT_SPRITE
            if data.get("sprites"):
                other = data["sprites"].get("other", {})
                if "official-artwork" in other:
                    sprite = other["official-artwork"].get("front_default") or sprite
                if sprite == DEFAULT_SPRITE:
                    sprite = data["sprites"].get("front_default") or DEFAULT_SPRITE

            registro = {
                "id": id_original,
                "nome": nome_clean,
                "tipos": tipos,
                "hp": hp,
                "attack": attack,
                "defense": defense,
                "special_attack": sp_atk,
                "special_defense": sp_def,
                "speed": speed,
                "soma_stats": soma_stats,
                "altura": data.get("height", 0),
                "peso": data.get("weight", 0),
                "habilidade": (
                    data["abilities"][0]["ability"]["name"]
                    if data.get("abilities")
                    else "Nenhuma"
                ),
                "sprite": sprite,
            }

            pokemon_completo.append(registro)
            cache[nome_clean] = registro
            time.sleep(0.1)

        except Exception as e:
            print(f"    [!] Erro de conexão com '{nome_original}': {e}")
            continue

    salvar_cache(cache)

    # Gerar o CSV Enriquecido Final 
    headers = [
        "id",
        "nome",
        "tipos",
        "hp",
        "attack",
        "defense",
        "special_attack",
        "special_defense",
        "speed",
        "soma_stats",
        "altura",
        "peso",
        "habilidade",
    ]
    with open(COMPLETO_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for p in pokemon_completo:
            writer.writerow(
                [
                    p["id"],
                    p["nome"],
                    ",".join(p["tipos"]),
                    p["hp"],
                    p["attack"],
                    p["defense"],
                    p["special_attack"],
                    p["special_defense"],
                    p["speed"],
                    p["soma_stats"],
                    p["altura"],
                    p["peso"],
                    p["habilidade"],
                ]
            )

    print(f"[+] Salvo com sucesso: {COMPLETO_CSV}")

    # Maior soma total
    max_soma = max(p["soma_stats"] for p in pokemon_completo)
    maiores_somas_pokes = [
        p["nome"].capitalize() for p in pokemon_completo if p["soma_stats"] == max_soma
    ]
    resp_1 = f"{', '.join(maiores_somas_pokes)} ({max_soma} BST)"

    # Maior média de ataque por tipo
    tipo_ataques = {}
    for p in pokemon_completo:
        for t in p["tipos"]:
            tipo_ataques.setdefault(t, []).append(p["attack"])
    tipo_medias = {tipo: sum(atks) / len(atks) for tipo, atks in tipo_ataques.items()}
    melhor_tipo = max(tipo_medias, key=tipo_medias.get)
    resp_2 = (
        f"Tipo {melhor_tipo.upper()} (média de ataque: {tipo_medias[melhor_tipo]:.2f})"
    )

    # Quantidade do tipo Water
    water_pokes = sum(1 for p in pokemon_completo if "water" in p["tipos"])
    resp_3 = f"{water_pokes} Pokémon"

    # 5 mais rápidos
    mais_rapidos = sorted(pokemon_completo, key=lambda p: p["speed"], reverse=True)[:5]
    resp_4 = ", ".join(
        [f"{p['nome'].capitalize()} ({p['speed']})" for p in mais_rapidos]
    )

    # Time dos Sonhos (Top 6 estatísticas gerais)
    ranking_stats = sorted(
        pokemon_completo, key=lambda p: p["soma_stats"], reverse=True
    )
    dream_team = ranking_stats[:6]
    resp_5 = ", ".join(
        [f"{p['nome'].capitalize()} ({p['soma_stats']})" for p in dream_team]
    )

    # Vantagens e Fraquezas agregadas do Time dos Sonhos
    dream_team_ids = {p["id"] for p in dream_team}
    dream_vantagens = set()
    dream_fraquezas = set()
    for p in dream_team:
        for t in p["tipos"]:
            matchups = obter_matchups_tipo(t, cache_matchups)
            dream_vantagens.update(matchups["vantagens"])
            dream_fraquezas.update(matchups["fraquezas"])

    conflitos = dream_vantagens.intersection(dream_fraquezas)
    dream_vantagens_limpas = sorted(list(dream_vantagens - conflitos))
    dream_fraquezas_limpas = sorted(list(dream_fraquezas - conflitos))

    resp_bonus_vantagem = ", ".join([v.upper() for v in dream_vantagens_limpas])
    resp_bonus_fraqueza = ", ".join([f.upper() for f in dream_fraquezas_limpas])

    # Escrever arquivo respostas.txt
    conteudo_txt = (
        "==================================================\n"
        "         RESPOSTAS PARA O TIME DE PRODUTO          \n"
        "==================================================\n\n"
        f"1. Pokémon com maior soma de stats (BST):\n   -> {resp_1}\n\n"
        f"2. Tipo com maior média de Attack da lista:\n   -> {resp_2}\n\n"
        f"3. Quantidade de Pokémon do tipo Water:\n   -> {resp_3}\n\n"
        f"4. Os 5 Pokémon mais rápidos:\n   -> {resp_4}\n\n"
        f"5. Time dos Sonhos (6 melhores somas de stats):\n   -> {resp_5}\n\n"
        "==================================================\n"
        "          RESPOSTAS DO DESAFIO BÔNUS              \n"
        "==================================================\n\n"
        f"O Time dos Sonhos possui vantagens ofensivas (Dano 2x) contra:\n   -> {resp_bonus_vantagem}\n\n"
        f"O Time dos Sonhos possui fraquezas defensivas (Dano 2x) contra:\n   -> {resp_bonus_fraqueza}\n"
    )

    with open(RESP_FILE, "w", encoding="utf-8") as f:
        f.write(conteudo_txt)
    print(f"[+] Salvo com sucesso: {RESP_FILE}")

    # Ordenar numericamente para a exibição no Front-End
    todos_pokes_ordenados = sorted(pokemon_completo, key=lambda p: int(p["id"]))

    # Processar dados do Dashboard interativo
    pokes_para_web = []
    for p in todos_pokes_ordenados:
        vantagens = set()
        fraquezas = set()
        for t in p["tipos"]:
            matchups = obter_matchups_tipo(t, cache_matchups)
            vantagens.update(matchups["vantagens"])
            fraquezas.update(matchups["fraquezas"])

        p_info = {
            "id": p["id"],
            "nome": p["nome"].capitalize(),
            "sprite": p.get("sprite", DEFAULT_SPRITE),
            "tipos": p["tipos"],
            "stats": {
                "HP": p["hp"],
                "Ataque": p["attack"],
                "Defesa": p["defense"],
                "Ataque Esp.": p["special_attack"],
                "Defesa Esp.": p["special_defense"],
                "Velocidade": p["speed"],
            },
            "total": p["soma_stats"],
            "habilidade": p["habilidade"].replace("-", " ").capitalize(),
            "altura": p["altura"] / 10.0,
            "peso": p["peso"] / 10.0,
            "vantagens": sorted(list(vantagens)),
            "fraquezas": sorted(list(fraquezas)),
            "dream_team": p["id"] in dream_team_ids,
        }
        pokes_para_web.append(p_info)

    # HTML TEMPLATE DO DASHBOARD INTERATIVO
    html_template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pokédex Analítica - Startup Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;600;700;800&display=swap');
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #0f172a;
        }
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #1e293b;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: #4f46e5;
            border-radius: 10px;
        }
    </style>
</head>
<body class="text-slate-100 min-h-screen flex flex-col">

    <header class="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
        <div class="max-w-7xl mx-auto flex justify-between items-center">
            <div>
                <span class="text-xs font-bold tracking-widest text-indigo-400 uppercase">ESTÁGIO DE DADOS - STARTUP BI</span>
                <h1 class="text-2xl font-extrabold text-white tracking-tight">Dashboard Analítico: Balanceamento</h1>
            </div>
            <span class="bg-indigo-500/10 text-indigo-400 text-xs font-semibold px-3 py-1.5 rounded-full border border-indigo-500/20">
                PokeAPI V2 Conectada
            </span>
        </div>
    </header>

    <main class="flex-grow max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        <section class="lg:col-span-4 flex flex-col gap-3 h-[calc(100vh-140px)] overflow-y-auto pr-2">
            <h2 class="text-sm font-semibold tracking-wider text-slate-400 uppercase mb-2">Criaturas Enriquecidas (__TOTAL_POKES__)</h2>
            <div id="poke-list" class="space-y-3"></div>
        </section>

        <section class="lg:col-span-8 bg-slate-900/40 border border-slate-800 rounded-2xl p-6 lg:p-8 flex flex-col justify-between">
            <div id="active-panel" class="grid grid-cols-1 md:grid-cols-12 gap-8"></div>
        </section>

    </main>

    <script>
        const pokemonData = __POKEMON_DATA_JS__;
        const typeColors = __COLORS_JS__;
        let activeIdx = 0;

        function getBadgeClass(type) {
            return typeColors[type.toLowerCase()] || "bg-slate-600 text-white";
        }

        function renderList() {
            const listContainer = document.getElementById("poke-list");
            listContainer.innerHTML = pokemonData.map((poke, index) => {
                const isActive = index === activeIdx;
                const typesBadges = poke.tipos.map(t => 
                    `<span class="px-2 py-0.5 text-[10px] font-bold rounded-md uppercase tracking-wider ${getBadgeClass(t)}">${t}</span>`
                ).join(" ");

                const dreamBadge = poke.dream_team 
                    ? `<span class="bg-amber-500/10 text-amber-400 text-[9px] font-bold px-1.5 py-0.5 rounded border border-amber-500/25">★ DREAM TEAM</span>` 
                    : '';

                return `
                    <button onclick="setActive(${index})" class="w-full text-left transition-all duration-200 border rounded-xl p-4 flex items-center gap-4 group 
                        ${isActive ? 'bg-indigo-600/10 border-indigo-500 shadow-lg shadow-indigo-500/5' : 'bg-slate-900/60 border-slate-800/80 hover:bg-slate-800/40 hover:border-slate-700'}">
                        <img src="${poke.sprite}" alt="${poke.nome}" class="w-14 h-14 object-contain group-hover:scale-110 transition-transform">
                        <div class="flex-grow">
                            <div class="flex justify-between items-baseline mb-0.5">
                                <span class="text-xs font-mono text-slate-500">#${poke.id}</span>
                                <div class="flex items-center gap-1.5">
                                    ${dreamBadge}
                                    <span class="text-xs font-bold text-indigo-400">BST ${poke.total}</span>
                                </div>
                            </div>
                            <h3 class="font-bold text-lg text-white group-hover:text-indigo-300 transition-colors">${poke.nome}</h3>
                            <div class="flex gap-1.5 mt-1.5">${typesBadges}</div>
                        </div>
                    </button>
                `;
            }).join("");
        }

        function renderActive() {
            const poke = pokemonData[activeIdx];
            const panel = document.getElementById("active-panel");

            const typesBadges = poke.tipos.map(t => 
                `<span class="px-3 py-1 text-xs font-extrabold rounded-lg uppercase tracking-wider shadow-md ${getBadgeClass(t)}">${t}</span>`
            ).join(" ");

            const statsBars = Object.entries(poke.stats).map(([name, val]) => {
                const pct = Math.min((val / 160) * 100, 100);
                return `
                    <div class="space-y-1">
                        <div class="flex justify-between text-sm">
                            <span class="text-slate-400 font-medium">${name}</span>
                            <span class="font-bold text-white font-mono">${val}</span>
                        </div>
                        <div class="h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div class="h-full bg-indigo-500 rounded-full transition-all duration-500" style="width: ${pct}%"></div>
                        </div>
                    </div>
                `;
            }).join("");

            const vantagensBadges = poke.vantagens.length > 0 
                ? poke.vantagens.map(t => `<span class="px-2 py-1 text-xs font-bold rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 uppercase tracking-wider">${t}</span>`).join(" ")
                : `<span class="text-sm text-slate-500 italic">Nenhuma</span>`;

            const fraquezasBadges = poke.fraquezas.length > 0 
                ? poke.fraquezas.map(t => `<span class="px-2 py-1 text-xs font-bold rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-400 uppercase tracking-wider">${t}</span>`).join(" ")
                : `<span class="text-sm text-slate-500 italic">Nenhuma</span>`;

            panel.innerHTML = `
                <div class="md:col-span-5 flex flex-col items-center text-center">
                    <div class="relative bg-slate-950/60 rounded-3xl p-6 border border-slate-800 w-full flex justify-center items-center h-56">
                        <span class="absolute top-4 left-4 text-xs font-mono text-slate-500">ID #${poke.id}</span>
                        <img src="${poke.sprite}" alt="${poke.nome}" class="w-48 h-48 md:w-52 md:h-52 object-contain drop-shadow-[0_10px_20px_rgba(99,102,241,0.2)]">
                    </div>
                    
                    <h2 class="text-3xl font-black text-white mt-6 tracking-tight">${poke.nome}</h2>
                    <div class="flex gap-2 mt-3">${typesBadges}</div>

                    <div class="grid grid-cols-3 gap-2 w-full mt-6 bg-slate-900/60 border border-slate-800/60 rounded-xl p-3 text-center">
                        <div>
                            <span class="block text-[10px] text-slate-400 font-bold uppercase">Altura</span>
                            <span class="text-sm font-extrabold text-white">${poke.altura} m</span>
                        </div>
                        <div>
                            <span class="block text-[10px] text-slate-400 font-bold uppercase">Peso</span>
                            <span class="text-sm font-extrabold text-white">${poke.peso} kg</span>
                        </div>
                        <div>
                            <span class="block text-[10px] text-slate-400 font-bold uppercase">Habilidade</span>
                            <span class="text-[11px] font-extrabold text-indigo-300 truncate block max-w-full" title="${poke.habilidade}">${poke.habilidade}</span>
                        </div>
                    </div>
                </div>

                <div class="md:col-span-7 flex flex-col justify-between space-y-6">
                    <div class="space-y-4">
                        <div class="flex justify-between items-baseline border-b border-slate-800 pb-2">
                            <h3 class="text-md font-bold text-white uppercase tracking-wider">Atributos de Combate</h3>
                            <span class="text-sm font-black text-indigo-400 font-mono">Total Base: ${poke.total}</span>
                        </div>
                        <div class="grid grid-cols-1 gap-3">
                            ${statsBars}
                        </div>
                    </div>

                    <div class="space-y-4 border-t border-slate-800 pt-4">
                        <h3 class="text-md font-bold text-white uppercase tracking-wider">Combates Ofensivos e Defensivos</h3>
                        
                        <div class="space-y-3">
                            <div>
                                <span class="text-xs font-bold text-emerald-400 uppercase tracking-wide block mb-1.5">Vantagem de Tipo (Ataque 2x)</span>
                                <div class="flex flex-wrap gap-1.5">${vantagensBadges}</div>
                            </div>
                            <div>
                                <span class="text-xs font-bold text-rose-400 uppercase tracking-wide block mb-1.5">Fraqueza de Tipo (Defesa 2x)</span>
                                <div class="flex flex-wrap gap-1.5">${fraquezasBadges}</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        function setActive(idx) {
            activeIdx = idx;
            renderList();
            renderActive();
        }

        renderList();
        renderActive();
    </script>
</body>
</html>
"""

    # Injeta os dados limpos no HTML
    html_template = html_template.replace(
        "__POKEMON_DATA_JS__", json.dumps(pokes_para_web, indent=4)
    )
    html_template = html_template.replace("__COLORS_JS__", json.dumps(TYPE_COLORS))
    html_template = html_template.replace("__TOTAL_POKES__", str(len(pokes_para_web)))

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"[+] Painel dinâmico gerado com sucesso: '{HTML_FILE}'")

    caminho_absoluto = os.path.realpath(HTML_FILE)
    print(f"[*] Abrindo o front-end interativo no seu navegador...")
    webbrowser.open(f"file://{caminho_absoluto}")


if __name__ == "__main__":
    main()
