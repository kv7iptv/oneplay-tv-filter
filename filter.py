
import os
import re
import urllib.request
from pathlib import Path

SOURCE_URL = os.environ["PLAYLIST_URL"]
OUTPUT_FILE = Path("docs/oneplay.m3u")
MAX_CHANNELS = 850

# Grupos permitidos, na ordem preferida.
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
    text = text.upper().strip()
    text = re.sub(r"\s+", " ", text)
    return text

def fetch_playlist():
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(request, timeout=90) as response:
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
    header = entry[0]
    match = re.search(
        r'group-title="([^"]*)"',
        header,
        re.IGNORECASE
    )
    return match.group(1).strip() if match else ""

def get_name(entry):
    return entry[0].rsplit(",", 1)[-1].strip()

def group_priority(group):
    group_n = normalize(group)

    # A data de JOGOS DO DIA pode mudar diariamente.
    if re.fullmatch(r"JOGOS DO DIA\s*\([^)]*\)", group_n):
        group_n = "JOGOS DO DIA"

    for index, allowed in enumerate(GROUPS):
        if group_n == normalize(allowed):
            return index

    return None


def natural_key(name):
    parts = re.split(r"(\d+)", name.casefold())
    return tuple(
        (1, int(part)) if part.isdigit() else (0, part)
        for part in parts
        if part
    )

def main():
    content = fetch_playlist()
    entries = parse_playlist(content)

    selected = []
    unknown_groups = set()

    for entry in entries:
        group = get_group(entry)
        priority = group_priority(group)

        if priority is None:
            unknown_groups.add(group or "(sem categoria)")
            continue

        selected.append((priority, natural_key(get_name(entry)), entry))

    selected.sort(key=lambda item: (item[0], item[1]))
    selected = selected[:MAX_CHANNELS]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="\n") as output:
        output.write("#EXTM3U\n")
        for _, _, entry in selected:
            output.write("\n".join(entry) + "\n")

    print(f"Entradas originais: {len(entries)}")
    print(f"Entradas selecionadas: {len(selected)}")
    print(f"Grupos não reconhecidos: {len(unknown_groups)}")
    print(f"Arquivo criado: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
  
