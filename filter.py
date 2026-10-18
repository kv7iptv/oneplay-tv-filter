
import os
import re
import unicodedata
import urllib.request
from pathlib import Path

SOURCE_URL = os.environ["PLAYLIST_URL"]
OUTPUT_FILE = Path("docs/oneplay.m3u")
MAX_CHANNELS = 850

# Categorias finais, na ordem em que aparecerão na playlist.
# JOGOS DO DIA foi removida.
# As cinco categorias regionais da Globo serão reunidas em GLOBO.
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
    "FILMES E SÉRIES",
    "HBO",
    "HBO MAX PPV",
    "TELECINE",
    "APPLE TV+ PPV",
    "DISNEY+ PPV",
    "PARAMOUNT+ PPV",
    "PRIME VIDEO PPV",
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


def normalize(text):
    """Normaliza acentos, espaços e maiúsculas."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    text = text.upper().strip()
    return re.sub(r"\s+", " ", text)


def fetch_playlist():
    """Baixa a playlist usando a URL guardada no segredo do GitHub."""
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        content = response.read()

    return content.decode("utf-8-sig", errors="replace")


def parse_playlist(content):
    """Mantém juntas as linhas de cada entrada M3U."""
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
    """Obtém o group-title da entrada."""
    match = re.search(
        r'group-title\s*=\s*"([^"]*)"',
        entry[0],
        re.IGNORECASE
    )

    return match.group(1).strip() if match else ""


def get_name(entry):
    """Obtém o nome do canal."""
    return entry[0].rsplit(",", 1)[-1].strip()


def canonical_group(group):
    """Converte a categoria original para uma das categorias permitidas."""
    name = normalize(group)

    # Reúne as categorias regionais da Globo.
    if re.fullmatch(r"GLOBO\s+(CENTRO-OESTE|NORDESTE|NORTE|SUDESTE|SUL)", name):
        return "GLOBO"

    aliases = {
        "LUTAS UFC": "LUTAS / UFC",
        "LUTAS/UFC": "LUTAS / UFC",
        "24H INFANTIS / DESENHOS": "24H INFANTIS/DESENHOS",
        "24H SERIES/PROGRAMAS": "24H SÉRIES/PROGRAMAS",
        "DOCUMENTARIOS": "DOCUMENTÁRIOS",
        "NOTÍCIAS": "NOTICIAS",
    }

    name = aliases.get(name, name)

    for allowed_group in GROUPS:
        if name == normalize(allowed_group):
            return allowed_group

    # JOGOS DO DIA e qualquer categoria não autorizada são ignorados.
    return None


def quality_rank(name):
    """
    Prioriza as variantes na ordem solicitada:
    FHD, FHD², H265, HD, HD², SD, SD².
    """
    normalized = normalize(name)

    patterns = [
        (r"\bFHD\s*²$", 1),
        (r"\bFHD$", 0),
        (r"\bH265$", 2),
        (r"\bHD\s*²$", 4),
        (r"\bHD$", 3),
        (r"\bSD\s*²$", 6),
        (r"\bSD$", 5),
    ]

    for pattern, rank in patterns:
        if re.search(pattern, normalized):
            return rank

    return 7


def name_without_quality(name):
    """Remove a qualidade final para ordenar primeiro o nome-base."""
    return re.sub(
        r"\s+(FHD|H265|HD|SD)\s*²?$",
        "",
        name,
        flags=re.IGNORECASE
    ).strip()


def natural_key(text):
    """Ordena números como números: 2 antes de 10."""
    parts = re.split(r"([0-9]+)", text.casefold())

    return tuple(
        (1, int(part)) if re.fullmatch(r"[0-9]+", part)
        else (0, part)
        for part in parts
        if part
    )


def channel_sort_key(entry):
    """
    Primeiro ordena pelo nome-base; depois pela qualidade.
    Exemplo: ESPN FHD antes de ESPN 2 FHD.
    """
    name = get_name(entry)
    base_name = name_without_quality(name)

    return (
        natural_key(base_name),
        quality_rank(name),
        name.casefold(),
    )


def set_group_title(entry, group):
    """Atualiza apenas o group-title para a categoria final."""
    updated = list(entry)

    updated[0] = re.sub(
        r'(\bgroup-title\s*=\s*")[^"]*(")',
        lambda match: match.group(1) + group + match.group(2),
        updated[0],
        count=1,
        flags=re.IGNORECASE
    )

    return updated


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

        # Agrupa os canais da Globo sob o mesmo group-title.
        normalized_entry = set_group_title(entry, group)
        selected_by_group[group].append(normalized_entry)

    # Ordena os canais de cada categoria.
    for group in GROUPS:
        selected_by_group[group].sort(key=channel_sort_key)

    # Distribui os canais em rodadas entre as categorias.
    # Assim, categorias do final da lista também recebem espaço
    # antes de categorias grandes consumirem todo o limite.
    selected_by_group_limited = {group: [] for group in GROUPS}

    for round_index in range(MAX_CHANNELS):
        for group in GROUPS:
            channels = selected_by_group[group]

            if round_index < len(channels):
                if sum(len(items) for items in selected_by_group_limited.values()) >= MAX_CHANNELS:
                    break

                selected_by_group_limited[group].append(
                    channels[round_index]
                )

        if sum(len(items) for items in selected_by_group_limited.values()) >= MAX_CHANNELS:
            break

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w", encoding="utf-8", newline="\n"
    ) as output:
        output.write("#EXTM3U\n")

        # Mantém as categorias agrupadas na ordem definida acima.
        for group in GROUPS:
            for entry in selected_by_group_limited[group]:
                output.write("\n".join(entry) + "\n")

    total_selected = sum(
        len(items) for items in selected_by_group_limited.values()
    )

    print(f"Entradas selecionadas: {total_selected}")
    print(f"Limite configurado: {MAX_CHANNELS}")
    print("Canais selecionados por categoria:")

    for group in GROUPS:
        count = len(selected_by_group_limited[group])
        available = len(selected_by_group[group])
        print(f"  {group}: {count} de {available}")

    print(f"Entradas JOGOS DO DIA ignoradas: {ignored_games}")
    print(f"Outras categorias não reconhecidas: {len(unknown_groups)}")

    for group in sorted(unknown_groups):
        print(f"  Ignorada: {group}")

    print(f"Arquivo criado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
    
