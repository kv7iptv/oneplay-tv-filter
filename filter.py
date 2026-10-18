
import os
import re
import unicodedata
import urllib.request
from pathlib import Path

SOURCE_URL = os.environ["PLAYLIST_URL"]
OUTPUT_FILE = Path("docs/oneplay.m3u")

MAX_GLOBO_POR_REGIAO = 15
MAX_INFANTIS = 126

GROUPS = [
    "ABERTOS",
    "GLOBO",
    "BAND",
    "RECORD TV",
    "SBT",
    "ESPN",
    "ESPORTES",
    "SPORTV",
    "PREMIERE",
    "SPORTYNET PPV",
    "LUTAS / UFC",
    "HBO MAX PPV",
    "APPLE TV+ PPV",
    "DISNEY+ PPV",
    "PARAMOUNT+ PPV",
    "PRIME VIDEO PPV",
    "FILMES E SÉRIES",
    "HBO",
    "TELECINE",
    "24H FILMES",
    "24H SÉRIES/PROGRAMAS",
    "DOCUMENTÁRIOS",
    "NOTICIAS",
    "VARIEDADES",
    "INFANTIS",
    "24H INFANTIS/DESENHOS",
    "RELIGIOSOS",
    "A FAZENDA 18",
]

QUALITY_SUFFIXES = r"FHD2|FHD|H265|HD2|HD|SD2|SD|UHD|4K"

REGION_KEYWORDS = {
    "NORTE": [
        "ACRE", "RIO BRANCO", "AMAPA", "MACAPA", "AMAZONAS",
        "MANAUS", "ITACOATIARA", "PARINTINS", "PARA", "BELEM",
        "ALTAMIRA", "CASTANHAL", "MARABA", "PARAGOMINAS",
        "PARAUAPEBAS", "REDENCAO", "TAPAJOS", "RONDONIA",
        "PORTO VELHO", "CACOAL", "VILHENA", "JI-PARANA",
        "RORAIMA", "BOA VISTA", "GUAJARA MIRIM",
    ],
    "NORDESTE": [
        "ALAGOAS", "MACEIO", "GAZETA ALAGOAS", "BAHIA",
        "SALVADOR", "JUAZEIRO BAHIA", "CEARA", "FORTALEZA",
        "VERDES MARES", "MARANHAO", "MIRANTE", "SAO LUIS",
        "COCAIS", "PARAIBA", "CABO BRANCO", "PERNAMBUCO",
        "RECIFE", "RIO GRANDE DO NORTE", "NATAL", "SERGIPE",
        "TERESINA", "PIAUI", "SANTA CRUZ", "SERRA MAR",
        "INTERTV COSTA BRANCA", "INTERTV CABUGI",
        "OESTE BARREIRAS",
    ],
    "CENTRO-OESTE": [
        "BRASILIA", "DISTRITO FEDERAL", "ANHANGUERA",
        "GOIANIA", "ANAPOLIS", "CATALAO", "ITUMBIARA",
        "JATAI", "LUZIANIA", "PORANGATU", "TOCANTINS",
        "CENTRO AMERICA", "MATO GROSSO", "MORENA",
        "CAMPO GRANDE", "CORUMBA", "PONTAPORA",
    ],
    "SUDESTE": [
        "SAO PAULO", "GLOBO SP", "CAPITAL", "CAMPINAS",
        "RIBEIRAO PRETO", "SAO CARLOS", "SUL DE MINAS",
        "DIVINOPOLIS", "ARAXA", "JUIZ DE FORA", "UBERLANDIA",
        "UBERABA", "MINAS", "VITORIA", "GAZETA ES",
        "GAZETA VITORIA", "GAZETA SUL", "RIO DE JANEIRO",
        "GLOBO RJ", "RIO SUL", "TV GRANDE RIO", "SANTOS",
        "TRIBUNA", "BAURU", "ITAPETININGA", "SOROCABA",
        "SJRP", "SAO JOSE DO RIO PRETO", "VANGUARDA",
        "TAUBATE", "S J CAMPOS", "FRONTEIRA PAULISTA",
        "INTEG", "INTEGRACAO",
    ],
    "SUL": [
        "PARANA", "RPC", "CASCAVEL", "CURITIBA",
        "FOZ DO IGUACU", "GUARAPUAVA", "LONDRINA",
        "MARINGA", "PARANAVAI", "PONTA GROSSA",
        "SANTA CATARINA", "NSC", "BLUMENAU", "CHAPECO",
        "CRICIUMA", "FLORIANOPOLIS", "JOINVILLE",
        "RIO GRANDE DO SUL", "RBS", "PORTO ALEGRE",
        "CAXIAS DO SUL", "PASSO FUNDO", "PELOTAS",
        "SANTA MARIA", "BAGE", "CRUZ ALTA",
    ],
}

KIDS_PRIORITY = [
    "BLUEY", "BOB ESPONJA", "PATRULHEIROS EM ACAO",
    "PEIXONAUTA", "MUNDO BITA", "3 PALAVRINHAS",
    "TURMA COCOMELON", "DANIEL TIGRE", "SANTIAGO DOS MARES",
    "PJ MASKS", "MIRACULOUS", "GIGANTOSSAURO", "BATWHEELS",
    "BEN 10", "POKEMON", "POKEMON HORIZONTES", "DRAGON BALL",
    "NARUTO", "NARUTO SHIPPUDEN", "ONE PIECE", "YU-GI-OH",
    "AVATAR A LENDA DE AANG", "HORA DE AVENTURA",
    "IRMAO DO JOREL", "TOM E JERRY", "PICA-PAU", "OS SMURFS",
    "TICO E TECO", "TIMAO E PUMBA", "DUCKTALES",
    "BABY LOONEY TUNES", "O SHOW DOS LOONEY TUNES",
    "KND A TURMA DO BAIRRO", "CORAGEM O CAO COVARDE",
    "AS AVENTURAS DE JACKIE CHAN", "JUSTICA JOVEM",
    "LIGA DA JUSTICA SEM LIMITES", "HOMEM-ARANHA", "X-MEN",
    "OS CAVALEIROS DO ZODIACO", "SUPER ONZE", "SUPER-C HOQUE",
    "YU YU HAKUSHO", "SAILOR MOON", "DIGIMON", "BEYBLADE",
    "MEDABOTS", "MECANIMAIS", "GLOOBINHO", "GLOOB",
    "DISCOVERY KIDS", "CARTOON NETWORK", "CARTOONITO",
    "TOONCAST", "TV RA TIM BUM", "DREAMWORKS",
    "MUNDO MARAVILHOSAMENTE ESTRANHO DE GUMBALL",
    "O SHOW DO PATRICK ESTRELA", "OS JETSONS",
    "ESQUADRILHA PARAFUSO", "GARGULAS", "HE-MAN",
    "THUNDERCATS", "SWAT KATS", "LILO E STITCH",
    "HOTEL TRANSYLVANIA", "JELLYSTONE",
    "MAYA E OS 3 GUERREIROS", "YABBA-DABBA DINOSSAUROS",
    "ZIG E SHARKO", "TRES ESPIAS DEMAIS",
    "A TURMA DO PATETA", "A VACA E O FRANGO",
    "A XERIFE CALLIE NO OESTE", "ALADDIN", "CAVALO DE FOGO",
    "CAPITAO PLANETA", "DU DUDU E EDU", "EDENS ZERO",
    "FAIRY TAIL", "HAIKYU", "HUNTER X HUNTER", "INUYASHA",
    "JUJUTSU KAISEN", "MY HERO ACADEMIA", "MOB PSYCHO 100",
    "ONE PUNCH MAN", "SAKAMOTO DAYS", "SOLO LEVELING",
    "SPY X FAMILY", "DR. STONE", "FULLMETAL ALCHEMIST BROTHERHOOD",
    "FRIEREN", "VINLAND SAGA", "KAIJU NO. 8", "BLACK CLOVER",
    "BLEACH", "BLUE LOCK", "DEMON SLAYER",
    "JOJOS BIZARRE ADVENTURE", "CHAINSAW MAN", "CYBERPUNK",
    "DEATH NOTE", "NEON GENESIS EVANGELION", "STEINSGATE",
    "SWORD ART ONLINE", "RECORD OF RAGNAROK", "NANATSU NO TAIZAI",
    "REZERO", "THE RISING OF THE SHIELD HERO", "OVERLORD",
    "MASHLE", "FUMETSU NO ANATA E", "DAN DA DAN", "TO BE HERO X",
    "WHAT IF", "X-MEN 97", "INVENCIVEL", "CAPITAO FALL",
    "SCOTT PILGRIM", "4 CONTRA O APOCALIPSE", "100 LOBO",
    "100 COISAS PARA FAZER ANTES DE VIRAR ZUMBI",
]

LINEAR_KIDS = {
    "BOX KIDS TV",
    "CARTOON NETWORK",
    "CARTOONITO",
    "DISCOVERY KIDS",
    "DREAMWORKS",
    "DUMDUM",
    "GLOOB",
    "GLOOBINHO",
    "KIDS MAIS",
    "TOONCAST",
    "TV RA TIM BUM",
}


def normalize(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    text = text.upper().strip()
    return re.sub(r"\s+", " ", text)


def fetch_playlist():
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read().decode("utf-8-sig", errors="replace")


def parse_playlist(content):
    entries = []
    current = []

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if line.startswith("#EXTINF:"):
            if current:
                entries.append(current)
            current = [line]
        elif current and line:
            current.append(line)

    if current:
        entries.append(current)

    return entries


def get_group(entry):
    match = re.search(
        r'group-title\s*=\s*"([^"]*)"',
        entry[0],
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def get_name(entry):
    return entry[0].rsplit(",", 1)[-1].strip()


def canonical_group(group):
    name = normalize(group)

    for allowed in GROUPS:
        if name == normalize(allowed):
            return allowed

    aliases = {
        "LUTAS UFC": "LUTAS / UFC",
        "LUTAS/UFC": "LUTAS / UFC",
        "24H INFANTIS / DESENHOS": "24H INFANTIS/DESENHOS",
        "24H SERIES/PROGRAMAS": "24H SÉRIES/PROGRAMAS",
        "GLOBO NORTE": "GLOBO",
        "GLOBO NORDESTE": "GLOBO",
        "GLOBO CENTRO-OESTE": "GLOBO",
        "GLOBO SUDESTE": "GLOBO",
        "GLOBO SUL": "GLOBO",
    }

    return aliases.get(name)


def quality_rank(name):
    normalized = normalize(name)

    patterns = [
        (r"\bFHD2$", 1),
        (r"\bFHD$", 0),
        (r"\bUHD$", 0),
        (r"\b4K$", 0),
        (r"\bH265$", 2),
        (r"\bHD2$", 4),
        (r"\bHD$", 3),
        (r"\bSD2$", 6),
        (r"\bSD$", 5),
    ]

    for pattern, rank in patterns:
        if re.search(pattern, normalized):
            return rank

    return 7


def name_without_quality(name):
    return re.sub(
        rf"\s+({QUALITY_SUFFIXES})$",
        "",
        normalize(name),
    ).strip()


def natural_key(text):
    parts = re.split(r"([0-9]+)", text.casefold())

    return tuple(
        (1, int(part)) if re.fullmatch(r"[0-9]+", part)
        else (0, part)
        for part in parts if part
    )


def channel_sort_key(entry):
    name = get_name(entry)

    return (
        natural_key(name_without_quality(name)),
        quality_rank(name),
        name.casefold(),
    )


def set_group_title(entry, group):
    updated = list(entry)
    pattern = r'(\bgroup-title\s*=\s*")[^"]*(")'

    if re.search(pattern, updated[0], re.IGNORECASE):
        updated[0] = re.sub(
            pattern,
            lambda match: match.group(1) + group + match.group(2),
            updated[0],
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        updated[0] = re.sub(
            r"^(#EXTINF:[^,]*)(,)",
            lambda match: (
                match.group(1)
                + f' group-title="{group}"'
                + match.group(2)
            ),
            updated[0],
            count=1,
        )

    return updated


def region_for_channel(name):
    normalized = normalize(name)
    matches = []

    for region, keywords in REGION_KEYWORDS.items():
        if any(normalize(keyword) in normalized for keyword in keywords):
            matches.append(region)

    return matches[0] if len(matches) == 1 else None


def select_globo(entries):
    by_region = {region: {} for region in REGION_KEYWORDS}
    unresolved = {}

    for entry in entries:
        name = get_name(entry)
        base = name_without_quality(name)
        region = region_for_channel(base)

        destination = by_region[region] if region else unresolved
        previous = destination.get(base)

        if (
            previous is None
            or quality_rank(name) < quality_rank(get_name(previous))
        ):
            destination[base] = entry

    selected = []

    print("Globo selecionada por região:")

    for region in REGION_KEYWORDS:
        ordered = sorted(
            by_region[region].values(),
            key=channel_sort_key,
        )
        chosen = ordered[:MAX_GLOBO_POR_REGIAO]
        selected.extend(chosen)
        print(f"  {region}: {len(chosen)}")

    print(f"  Sem região identificável: {len(unresolved)}")
    print(f"  Total Globo selecionada: {len(selected)}")

    if len(selected) < MAX_GLOBO_POR_REGIAO * len(REGION_KEYWORDS):
        print(
            "AVISO: não foi possível atingir a meta regional. "
            "Canais sem região confirmada não serão incluídos automaticamente."
        )

    return selected


def kids_priority_key(entry):
    base = name_without_quality(get_name(entry))

    for index, keyword in enumerate(KIDS_PRIORITY):
        if normalize(keyword) in base:
            return (0, index, natural_key(base))

    return (1, 0, natural_key(base))


def select_kids(entries):
    linear_groups = {}
    vod_entries = {}

    print("Exemplos de nomes recebidos na categoria infantil:")

    for entry in entries[:20]:
        print("  ", repr(get_name(entry)))

    for entry in entries:
        name = get_name(entry)
        base = name_without_quality(name)

        if base in LINEAR_KIDS:
            target = linear_groups
        else:
            target = vod_entries

        previous = target.get(base)

        if (
            previous is None
            or quality_rank(name) < quality_rank(get_name(previous))
        ):
            target[base] = entry

    linear = sorted(linear_groups.values(), key=channel_sort_key)
    vod = sorted(vod_entries.values(), key=kids_priority_key)

    selected = linear[:MAX_INFANTIS]
    remaining = MAX_INFANTIS - len(selected)
    selected.extend(vod[:remaining])

    print(f"Canais infantis lineares únicos: {len(linear)}")
    print(f"Títulos restantes disponíveis: {len(vod)}")
    print(f"Entradas infantis selecionadas: {len(selected)}")

    if len(linear) == 0:
        print(
            "AVISO: nenhum canal linear reconhecido. "
            "Use os exemplos acima para ajustar os nomes-base."
        )

    if len(selected) < MAX_INFANTIS:
        print(
            f"AVISO: existem apenas {len(selected)} entradas "
            "infantis selecionáveis."
        )

    return selected


def main():
    print("Baixando lista de origem...")
    content = fetch_playlist()

    if "#EXTINF:" not in content:
        raise ValueError(
            "A resposta recebida não parece ser uma lista M3U válida."
        )

    entries = parse_playlist(content)
    print(f"Entradas originais: {len(entries)}")

    selected_by_group = {group: [] for group in GROUPS}
    unknown_groups = set()
    ignored_games = 0

    for entry in entries:
        original_group = get_group(entry)
        group = canonical_group(original_group)

        if group is None:
            if normalize(original_group).startswith("JOGOS DO DIA"):
                ignored_games += 1
            else:
                unknown_groups.add(original_group or "(sem categoria)")
            continue

        normalized_entry = set_group_title(entry, group)
        selected_by_group[group].append(normalized_entry)

    selected_by_group["GLOBO"] = select_globo(
        selected_by_group["GLOBO"]
    )

    selected_by_group["24H INFANTIS/DESENHOS"] = select_kids(
        selected_by_group["24H INFANTIS/DESENHOS"]
    )

    for group in GROUPS:
        if group not in ("GLOBO", "24H INFANTIS/DESENHOS"):
            selected_by_group[group].sort(key=channel_sort_key)

    total_selected = sum(
        len(channels) for channels in selected_by_group.values()
    )

    if total_selected == 0:
        raise ValueError(
            "Nenhum canal foi selecionado. Verifique as categorias."
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="\n") as output:
        output.write("#EXTM3U\n")

        for group in GROUPS:
            for entry in selected_by_group[group]:
                output.write("\n".join(entry) + "\n")

    print("\nResumo por categoria:")

    for group in GROUPS:
        print(f"  {group}: {len(selected_by_group[group])}")

    print(f"Entradas selecionadas: {total_selected}")
    print(f"Entradas JOGOS DO DIA ignoradas: {ignored_games}")
    print(f"Outras categorias não reconhecidas: {len(unknown_groups)}")

    for group in sorted(unknown_groups):
        print(f"  Ignorada: {group}")

    print(f"Arquivo criado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
    
