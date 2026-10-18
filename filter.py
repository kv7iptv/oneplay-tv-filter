
import os
import re
import unicodedata
import urllib.request
from pathlib import Path

SOURCE_URL = os.environ["PLAYLIST_URL"]
OUTPUT_FILE = Path("docs/oneplay.m3u")

# Todas as categorias permitidas.
# As cinco regiões da Globo são reunidas em GLOBO.
# JOGOS DO DIA permanece excluída.
# Não existe limite artificial de canais.
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
    """Normaliza acentos, espaços, maiúsculas e caracteres compatíveis."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    text = text.upper().strip()
    return re.sub(r"\s+", " ", text)


def fetch_playlist():
    """Baixa a playlist de origem."""
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
    """Obtém o group-title de uma entrada."""
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
    """Reconhece e normaliza somente as categorias permitidas."""
    name = normalize(group)

    # Junta as cinco categorias regionais da Globo.
    if re.fullmatch(
        r"GLOBO\s+(CENTRO-OESTE|NORDESTE|NORTE|SUDESTE|SUL)",
        name
    ):
        return "GLOBO"

    # Os destinos também ficam sem acentos, pois name já foi normalizado.
    aliases = {
        "LUTAS UFC": "LUTAS / UFC",
        "LUTAS/UFC": "LUTAS / UFC",
        "24H INFANTIS / DESENHOS": "24H INFANTIS/DESENHOS",
        "24H SERIES/PROGRAMAS": "24H SERIES/PROGRAMAS",
        "DOCUMENTARIOS": "DOCUMENTARIOS",
        "NOTICIAS": "NOTICIAS",
    }

    name = aliases.get(name, name)

    for allowed_group in GROUPS:
        if name == normalize(allowed_group):
            return allowed_group

    # JOGOS DO DIA e todas as demais categorias ficam de fora.
    return None


def quality_rank(name):
    """
    Ordena variantes nesta prioridade:
    FHD, FHD², H265, HD, HD², SD, SD².
    A normalização transforma o sobrescrito ² em 2.
    """
    normalized = normalize(name)

    patterns = [
        (r"\bFHD2$", 1),
        (r"\bFHD$", 0),
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
    """Remove a qualidade do final para agrupar variantes do mesmo canal."""
    normalized = normalize(name)

    return re.sub(
        r"\s+(FHD2|FHD|H265|HD2|HD|SD2|SD)$",
        "",
        normalized
    ).strip()


def natural_key(text):
    """Ordena números naturalmente: 2 antes de 10."""
    parts = re.split(r"([0-9]+)", text.casefold())

    return tuple(
        (1, int(part)) if re.fullmatch(r"[0-9]+", part)
        else (0, part)
        for part in parts
        if part
    )


def channel_sort_key(entry):
    """
    Agrupa primeiro pelo nome-base, depois pela qualidade.
    Ex.: ESPN FHD antes de ESPN 2 FHD.
    """
    name = get_name(entry)
    base_name = name_without_quality(name)

    return (
        natural_key(base_name),
        quality_rank(name),
        name.casefold(),
    )


def set_group_title(entry, group):
    """Atualiza o group-title sem alterar os outros metadados."""
    updated = list(entry)

    pattern = r'(\bgroup-title\s*=\s*")[^"]*(")'

    if re.search(pattern, updated[0], re.IGNORECASE):
        updated[0] = re.sub(
            pattern,
            lambda match: match.group(1) + group + match.group(2),
            updated[0],
            count=1,
            flags=re.IGNORECASE
        )
    else:
        # Se não houver group-title, adiciona o atributo ao EXTINF.
        updated[0] = re.sub(
            r"^(#EXTINF:[^,]*)(,)",
            lambda match: (
                match.group(1)
                + f' group-title="{group}"'
                + match.group(2)
            ),
            updated[0],
            count=1
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
                unknown_groups.add(
                    original_group or "(sem categoria)"
                )
            continue

        normalized_entry = set_group_title(entry, group)
        selected_by_group[group].append(normalized_entry)

    # Ordena todas as entradas dentro de cada categoria.
    for group in GROUPS:
        selected_by_group[group].sort(key=channel_sort_key)

    # Não aplica limite de canais.
    total_selected = sum(
        len(channels) for channels in selected_by_group.values()
    )

    if total_selected == 0:
        raise ValueError(
            "Nenhum canal foi selecionado. "
            "Verifique os nomes das categorias no relatório."
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w", encoding="utf-8", newline="\n"
    ) as output:
        output.write("#EXTM3U\n")

        for group in GROUPS:
            for entry in selected_by_group[group]:
                output.write("\n".join(entry) + "\n")

    print(f"Entradas selecionadas: {total_selected}")
    print("Limite de canais: nenhum")
    print("Canais selecionados por categoria:")

    for group in GROUPS:
        count = len(selected_by_group[group])
        print(f"  {group}: {count}")

    print(f"Entradas JOGOS DO DIA ignoradas: {ignored_games}")
    print(f"Outras categorias não reconhecidas: {len(unknown_groups)}")

    for group in sorted(unknown_groups):
        print(f"  Ignorada: {group}")

    print(f"Arquivo criado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
    
