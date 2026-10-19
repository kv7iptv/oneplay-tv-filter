import os
import re
import unicodedata
import urllib.request
from pathlib import Path

SOURCE_URL = os.environ["PLAYLIST_URL"]
OUTPUT_FILE = Path("docs/oneplay.m3u")

MAX_GLOBO_POR_REGIAO = 15
MAX_GLOBO_TOTAL = 75
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
        "MANAUS", "ITACOATIARA", "PARINTINS", "PARA",
        "BELEM", "ALTAMIRA", "CASTANHAL", "MARABA",
        "PARAGOMINAS", "PARAUAPEBAS", "REDENCAO", "TAPAJOS",
        "RONDONIA", "PORTO VELHO", "CACOAL", "VILHENA",
        "JI-PARANA", "RORAIMA", "BOA VISTA", "GUAJARA MIRIM",
        "TOCANTINS",
    ],
    "NORDESTE": [
        "ALAGOAS", "MACEIO", "GAZETA ALAGOAS", "BAHIA",
        "SALVADOR", "JUAZEIRO BAHIA", "CEARA", "FORTALEZA",
        "VERDES MARES", "MARANHAO", "MIRANTE", "SAO LUIS",
        "COCAIS", "PARAIBA", "CABO BRANCO", "PERNAMBUCO",
        "RECIFE", "RIO GRANDE DO NORTE", "NATAL", "SERGIPE",
        "TERESINA", "PIAUI", "SANTA CRUZ", "SERRA MAR",
        "INTERTV COSTA BRANCA", "INTERTV CABUGI",
        "OESTE BARREIRAS", "ASA BRANCA", "JUAZEIRO DO NORTE",
        "TV SAO FRANCISCO", "TV SUDOESTE",
    ],
    "CENTRO-OESTE": [
        "BRASILIA", "DISTRITO FEDERAL", "ANHANGUERA",
        "GOIANIA", "ANAPOLIS", "CATALAO", "ITUMBIARA",
        "JATAI", "LUZIANIA", "PORANGATU",
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
        "INTEG", "INTEGRACAO", "MOGI DAS CRUZES",
        "INTER ALTO LITORAL", "INTER DOS VALES",
        "INTERTV CEL FABRICIANO", "INTERTV GOV VALADARES",
        "VANG S J CAMPOS", "DIARIO MOGI",
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

REGION_OVERRIDES = {
    "GLOBO RPC PARANAVAI": "SUL",
    "GLOBO DIARIO MOGI DAS CRUZES": "SUDESTE",
    "GLOBO DIARIO MOGIDAS CRUZES": "SUDESTE",
    "GLOBO VANG. S.J. CAMPOS": "SUDESTE",
    "GLOBO INTERTV CEL FABRICIANO": "SUDESTE",
    "GLOBO INTERTV GOV VALADARES": "SUDESTE",
    "GLOBO JUAZEIRO DO NORTE": "NORDESTE",
    "GLOBO TV ITACOTIARA": "NORTE",
    "GLOBO TV JI-PARANA": "NORTE",
    "GLOBO TV LIBERAL PARAGOMINAS": "NORTE",
    "GLOBO TV OESTE": "NORDESTE",
    "GLOBO TV SAO FRANCISCO": "NORDESTE",
    "GLOBO TV SUDOESTE": "NORDESTE",
    "GLOBO ASA BRANCA": "NORDESTE",
    "GLOBO ALAGOAS": "NORDESTE",
    "GLOBO GAZETA ALAGOAS": "NORDESTE",
    "GLOBO AMAZONICA ITACOATIARA": "NORTE",
    "GLOBO AMAZONICA MACAPA": "NORTE",
    "GLOBO AMAZONICA MANAUS": "NORTE",
    "GLOBO AMAZONICA PARINTINS": "NORTE",
    "GLOBO AMAZONICA PORTO VELHO": "NORTE",
    "GLOBO AMAZONICA RIO BRANCO": "NORTE",
    "GLOBO AMAZONICA RONDONIA": "NORTE",
    "GLOBO ANHANGUERA TOCANTINS": "NORTE",
    "GLOBO CABO BRANCO": "NORDESTE",
    "GLOBO INTERTV COSTA BRANCA": "NORDESTE",
    "GLOBO JUAZEIRO BAHIA": "NORDESTE",
    "GLOBO MIRANTE COCAIS": "NORDESTE",
    "GLOBO MIRANTE SAO LUIS": "NORDESTE",
    "GLOBO BRASILIA": "CENTRO-OESTE",
    "GLOBO CENTRO AMERICA": "CENTRO-OESTE",
    "GLOBO MORENA": "CENTRO-OESTE",
    "GLOBO TV MORENA CORUMBA": "CENTRO-OESTE",
    "GLOBO TV MORENA PONTAPORA": "CENTRO-OESTE",
    "GLOBO RPC": "SUL",
    "GLOBO NSC": "SUL",
    "GLOBO RBS": "SUL",
}

# Canais principais usados primeiro quando for necessário
# completar as 75 vagas com emissoras de outras regiões.
GLOBO_PRIORIDADE_COMPLEMENTO = [
    "GLOBO SP",
    "GLOBO SAO PAULO",
    "GLOBO CAPITAL",
    "GLOBO RIO DE JANEIRO",
    "GLOBO RJ",
    "GLOBO MINAS",
    "GLOBO NORDESTE",
    "GLOBO BRASILIA",
    "GLOBO BAHIA",
    "GLOBO PERNAMBUCO",
    "GLOBO CEARA",
    "GLOBO ALAGOAS",
    "GLOBO PARANA",
    "GLOBO RBS PORTO ALEGRE",
    "GLOBO AMAZONICA MANAUS",
]

KIDS_PRIORITY = [
    "BLUEY",
    "BOB ESPONJA",
    "PATRULHA CANINA",
    "PAW PATROL",
    "PEPPA PIG",
    "MUNDO BITA",
    "3 PALAVRINHAS",
    "COCOMELON",
    "TURMA COCOMELON",
    "PATRULHEIROS EM ACAO",
    "PEIXONAUTA",
    "DANIEL TIGRE",
    "GALINHA PINTADINHA",
    "MUNDO DE GREG",
    "O SHOW DA LUNA",
    "SHOW DA LUNA",
    "MIRACULOUS",
    "PJ MASKS",
    "SANTIAGO DOS MARES",
    "GIGANTOSSAURO",
    "BATWHEELS",
    "BEN 10",
    "POKEMON HORIZONTES",
    "POKEMON",
    "DRAGON BALL",
    "NARUTO SHIPPUDEN",
    "NARUTO",
    "ONE PIECE",
    "YU-GI-OH",
    "AVATAR A LENDA DE AANG",
    "HORA DE AVENTURA",
    "IRMAO DO JOREL",
    "TOM E JERRY",
    "PICA-PAU",
    "OS SMURFS",
    "TICO E TECO",
    "TIMAO E PUMBA",
    "DUCKTALES",
    "BABY LOONEY TUNES",
    "O SHOW DOS LOONEY TUNES",
    "KND A TURMA DO BAIRRO",
    "CORAGEM O CAO COVARDE",
    "AS AVENTURAS DE JACKIE CHAN",
    "JUSTICA JOVEM",
    "LIGA DA JUSTICA SEM LIMITES",
    "HOMEM-ARANHA",
    "X-MEN 97",
    "X-MEN",
    "OS CAVALEIROS DO ZODIACO",
    "SUPER ONZE",
    "YU YU HAKUSHO",
    "SAILOR MOON",
    "DIGIMON",
    "BEYBLADE",
    "MEDABOTS",
    "MECANIMAIS",
    "GLOOBINHO",
    "GLOOB",
    "DISCOVERY KIDS",
    "CARTOON NETWORK",
    "CARTOONITO",
    "TOONCAST",
    "TV RA TIM BUM",
    "DREAMWORKS",
    "MUNDO MARAVILHOSAMENTE ESTRANHO DE GUMBALL",
    "O SHOW DO PATRICK ESTRELA",
    "OS JETSONS",
    "ESQUADRILHA PARAFUSO",
    "GARGULAS",
    "HE-MAN",
    "THUNDERCATS",
    "SWAT KATS",
    "LILO E STITCH",
    "HOTEL TRANSYLVANIA",
    "JELLYSTONE",
    "MAYA E OS 3 GUERREIROS",
    "YABBA-DABBA DINOSSAUROS",
    "ZIG E SHARKO",
    "TRES ESPIAS DEMAIS",
    "A TURMA DO PATETA",
    "A VACA E O FRANGO",
    "A XERIFE CALLIE NO OESTE",
    "ALADDIN",
    "CAVALO DE FOGO",
    "CAPITAO PLANETA",
    "DU DUDU E EDU",
    "EDENS ZERO",
    "FAIRY TAIL",
    "HAIKYU",
    "HUNTER X HUNTER",
    "INUYASHA",
    "JUJUTSU KAISEN",
    "MY HERO ACADEMIA",
    "MOB PSYCHO 100",
    "ONE PUNCH MAN",
    "SAKAMOTO DAYS",
    "SOLO LEVELING",
    "SPY X FAMILY",
    "DR. STONE",
    "FULLMETAL ALCHEMIST BROTHERHOOD",
    "FRIEREN",
    "VINLAND SAGA",
    "KAIJU NO. 8",
    "BLACK CLOVER",
    "BLEACH",
    "BLUE LOCK",
    "DEMON SLAYER",
    "JOJOS BIZARRE ADVENTURE",
    "CHAINSAW MAN",
    "CYBERPUNK",
    "DEATH NOTE",
    "NEON GENESIS EVANGELION",
    "STEINSGATE",
    "SWORD ART ONLINE",
    "RECORD OF RAGNAROK",
    "NANATSU NO TAIZAI",
    "REZERO",
    "THE RISING OF THE SHIELD HERO",
    "OVERLORD",
    "MASHLE",
    "FUMETSU NO ANATA E",
    "DAN DA DAN",
    "TO BE HERO X",
    "WHAT IF",
    "INVENCIVEL",
    "CAPITAO FALL",
    "SCOTT PILGRIM",
    "4 CONTRA O APOCALIPSE",
    "100 LOBO",
    "100 COISAS PARA FAZER ANTES DE VIRAR ZUMBI",
]


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
        (r"\bFHD2(?:\s*[²³])?$", 1),
        (r"\bFHD(?:\s*[²³])?$", 0),
        (r"\bUHD(?:\s*[²³])?$", 0),
        (r"\b4K(?:\s*[²³])?$", 0),
        (r"\bH265(?:\s*[²³])?$", 2),
        (r"\bHD2(?:\s*[²³])?$", 4),
        (r"\bHD(?:\s*[²³])?$", 3),
        (r"\bSD2(?:\s*[²³])?$", 6),
        (r"\bSD(?:\s*[²³])?$", 5),
    ]

    for pattern, rank in patterns:
        if re.search(pattern, normalized):
            return rank

    return 7


def name_without_quality(name):
    return re.sub(
        rf"\s+({QUALITY_SUFFIXES})(?:\s*[²³])?$",
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

    for exact_name, region in REGION_OVERRIDES.items():
        if normalize(exact_name) in normalized:
            return region

    # Paraná não deve ser confundido com Pará.
    if any(term in normalized for term in [
        "PARANAVAI", "PARANA", "RPC", "CURITIBA",
        "CASCAVEL", "LONDRINA", "MARINGA",
        "FOZ DO IGUACU", "GUARAPUAVA",
    ]):
        return "SUL"

    if any(term in normalized for term in [
        "PARAGOMINAS", "TV LIBERAL", "PARAUAPEBAS",
        "AMAZONICA", "AMAPA", "MACAPA", "MANAUS",
        "ITACOATIARA", "PARINTINS", "PORTO VELHO",
        "RIO BRANCO", "RONDONIA", "RORAIMA", "BOA VISTA",
        "TAPAJOS", "BELEM", "TOCANTINS",
    ]):
        return "NORTE"

    matches = []

    for region, keywords in REGION_KEYWORDS.items():
        for keyword in keywords:
            normalized_keyword = normalize(keyword)

            if normalized_keyword == "PARA":
                continue

            if normalized_keyword in normalized:
                matches.append(region)
                break

    return matches[0] if len(matches) == 1 else None


def select_globo(entries):
    # Consolida variantes de qualidade da mesma emissora.
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

    selected_by_region = {}
    selected_keys = set()

    print("\nGlobo selecionada por região:")

    # Primeira etapa: até 15 emissoras identificadas por região.
    for region in REGION_KEYWORDS:
        ordered = sorted(
            by_region[region].values(),
            key=channel_sort_key,
        )

        chosen = ordered[:MAX_GLOBO_POR_REGIAO]
        selected_by_region[region] = chosen

        for entry in chosen:
            selected_keys.add(name_without_quality(get_name(entry)))

        print(f"  {region}: {len(chosen)}")

    selected_count = sum(
        len(channels) for channels in selected_by_region.values()
    )
    missing = MAX_GLOBO_TOTAL - selected_count

    # Segunda etapa: completa as vagas com outras emissoras Globo
    # disponíveis, sem repetir a mesma emissora.
    if missing > 0:
        print(
            f"\nFaltam {missing} emissoras para completar "
            f"{MAX_GLOBO_TOTAL}. Procurando opções de complemento..."
        )

        candidates = {}

        for region_channels in by_region.values():
            for entry in region_channels.values():
                base = name_without_quality(get_name(entry))
                if base not in selected_keys:
                    candidates[base] = entry

        for base, entry in unresolved.items():
            if base not in selected_keys:
                candidates.setdefault(base, entry)

        priority = [
            normalize(name)
            for name in GLOBO_PRIORIDADE_COMPLEMENTO
        ]

        def complement_key(entry):
            base = name_without_quality(get_name(entry))

            for index, preferred in enumerate(priority):
                if preferred in base:
                    return (0, index, channel_sort_key(entry))

            return (1, 0, channel_sort_key(entry))

        ordered_candidates = sorted(
            candidates.values(),
            key=complement_key,
        )

        added = []

        for entry in ordered_candidates:
            if missing <= 0:
                break

            base = name_without_quality(get_name(entry))

            if base in selected_keys:
                continue

            added.append(entry)
            selected_keys.add(base)
            missing -= 1

        if added:
            print("\nEmissoras adicionadas para completar as 75:")

            for entry in added:
                name = get_name(entry)
                region = region_for_channel(name) or "REGIÃO NÃO IDENTIFICADA"
                print(f"  - {name} (origem: {region})")

            # As emissoras de complemento ficam no grupo GLOBO,
            # mantendo os nomes originais e sem duplicar entradas.
            selected_by_region["COMPLEMENTO"] = added

    selected = []

    for region in REGION_KEYWORDS:
        selected.extend(selected_by_region.get(region, []))

    selected.extend(selected_by_region.get("COMPLEMENTO", []))

    print("\nResumo final da seleção Globo:")

    for region in REGION_KEYWORDS:
        print(
            f"  {region}: "
            f"{len(selected_by_region.get(region, []))} "
            "(selecionadas pela região)"
        )

    print(
        "  Complemento de outras regiões: "
        f"{len(selected_by_region.get('COMPLEMENTO', []))}"
    )
    print(f"  Total Globo selecionada: {len(selected)}")

    if unresolved:
        print("\nEmissoras Globo sem região identificada:")
        for name in sorted(unresolved, key=natural_key):
            print(f"  - {name}")

    if len(selected) != MAX_GLOBO_TOTAL:
        print(
            "\nAVISO: a lista de origem não forneceu emissoras distintas "
            f"suficientes para completar {MAX_GLOBO_TOTAL}. "
            f"Total disponível selecionado: {len(selected)}."
        )

    return selected


def kids_priority_key(entry):
    base = name_without_quality(get_name(entry))

    for index, keyword in enumerate(KIDS_PRIORITY):
        normalized_keyword = normalize(keyword)

        if normalized_keyword in base:
            return (0, index, natural_key(base))

    return (1, 0, natural_key(base))


def select_kids(entries):
    unique = {}

    for entry in entries:
        name = get_name(entry)
        base = name_without_quality(name)
        previous = unique.get(base)

        if (
            previous is None
            or quality_rank(name) < quality_rank(get_name(previous))
        ):
            unique[base] = entry

    available_names = set(unique)
    priority_found = []

    for keyword in KIDS_PRIORITY:
        normalized_keyword = normalize(keyword)

        for name in sorted(available_names, key=natural_key):
            if normalized_keyword in name and name not in priority_found:
                priority_found.append(name)

    print("\nDiagnóstico dos canais 24H infantis:")
    print(f"  Títulos únicos disponíveis: {len(unique)}")
    print(f"  Títulos que correspondem às prioridades: {len(priority_found)}")
    print("  Títulos prioritários encontrados:")

    for name in priority_found:
        print(f"    - {name}")

    ordered = sorted(unique.values(), key=kids_priority_key)
    selected = ordered[:MAX_INFANTIS]

    print(f"  Limite configurado: {MAX_INFANTIS}")
    print(f"  Títulos selecionados: {len(selected)}")

    if len(selected) < MAX_INFANTIS:
        print(
            "AVISO: há menos títulos únicos disponíveis do que o limite "
            "configurado; todos os títulos únicos foram mantidos."
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
        len(channels) for c
