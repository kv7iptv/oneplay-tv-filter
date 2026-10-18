
import os
import re
import unicodedata
import urllib.request
from pathlib import Path

SOURCE_URL = os.environ["PLAYLIST_URL"]
OUTPUT_FILE = Path("docs/oneplay.m3u")
MAX_CHANNELS = 850

# Ordem de prioridade das categorias na lista final.
GROUPS = [
    "ABERTOS",
    "GLOBO CENTRO-OESTE",
    "GLOBO NORDESTE",
    "GLOBO NORTE",
    "GLOBO SUDESTE",
    "GLOBO SUL",
    "BAND",
    "RECORD TV",
    "SBT",
    "ESPORTES",
    "ESPN",
    "SPORTV",
    "PREMIERE",
    "SPORTYNET PPV",
    "JOGOS DO DIA",
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
    """Normaliza acentos, espaços e maiúsculas para comparar categorias."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    text = text.upper().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def fetch_playlist():
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=90) as response:
        content = response.read()

    return content.decode("utf-8-sig", errors="replace")


def parse_playlist(content):
    """Mantém cada entrada EXTINF e suas linhas associadas."""
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
    header = entry[0]

    match = re.search(
        r'group-title\s*=\s*"([^"]*)"',
        header,
        re.IGNORECASE
    )

    if not match:
        return ""

    return match.group(1).strip()


def get_name(entry):
    header = entry[0]
    return header.rsplit(",", 1)[-1].strip()


def group_priority(group):
    group_name = normalize(group)

    # A categoria de jogos pode conter uma data variável.
    if re.fullmatch(r"JOGOS DO DIA\s*\([^)]*\)", group_name):
        group_name = "JOGOS DO DIA"

    # Pequenas variações de escrita conhecidas.
    aliases = {
        "NOTICIAS": "NOTICIAS",
        "NOTÍCIAS": "NOTICIAS",
        "LUTAS UFC": "LUTAS / UFC",
        "LUTAS/UFC": "LUTAS / UFC",
        "24H SERIES/PROGRAMAS": "24H SÉRIES/PROGRAMAS",
        "24H INFANTIS / DESENHOS": "24H INFANTIS/DESENHOS",
    }

    group_name = aliases.get(group_name, group_name)

    for index, allowed_group in enumerate(GROUPS):
        if group_name == normalize(allowed_group):
            return index

    return None


def natural_key(name):
    """Ordena números naturalmente: Canal 2 vem antes de Canal 10."""
    parts = re.split(r"(\d+)", name.casefold())

    return tuple(
        (1, int(part)) if part.isdigit() else (0, part)
        for part in parts
        if part
    )


def main():
    print("Baixando lista de origem...")
    content = fetch_playlist()

    if "#EXTINF:" not in content:
        raise ValueError(
            "A resposta recebida não parece ser uma lista M3U válida."
        )

    entries = parse_playlist(content)

    selected_by_group = {group: [] for group in GROUPS}
    unknown_groups = set()

    for entry in entries:
        group = get_group(entry)
        priority = group_priority(group)

        if priority is None:
            unknown_groups.add(group or "(sem categoria)")
            continue

        canonical_group = GROUPS[priority]
        selected_by_group[canonical_group].append(entry)

    # Ordena os canais dentro de cada categoria.
    for group in GROUPS:
        selected_by_group[group].sort(
            key=lambda entry: natural_key(get_name(entry))
        )

    # Mantém a prioridade definida e respeita o limite de segurança.
    selected = []

    for group in GROUPS:
        for entry in selected_by_group[group]:
            if len(selected) >= MAX_CHANNELS:
                break
            selected.append(entry)

        if len(selected) >= MAX_CHANNELS:
            break

    if not selected:
        raise ValueError(
            "Nenhum canal foi selecionado. "
            "Os nomes das categorias podem ser diferentes "
            "dos configurados em GROUPS."
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w", encoding="utf-8", newline="\n"
    ) as output:
        output.write("#EXTM3U\n")

        for entry in selected:
            output.write("\n".join(entry) + "\n")

    print(f"Entradas originais: {len(entries)}")
    print(f"Entradas selecionadas: {len(selected)}")
    print(f"Limite configurado: {MAX_CHANNELS}")
    print("Canais por categoria:")

    for group in GROUPS:
        count = len(selected_by_group[group])
        if count:
            print(f"  {group}: {count}")

    print(f"Grupos não reconhecidos: {len(unknown_groups)}")

    for group in sorted(unknown_groups):
        print(f"  Categoria não reconhecida: {group}")

    print(f"Arquivo criado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
    
