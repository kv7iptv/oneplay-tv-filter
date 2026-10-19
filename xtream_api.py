
import os
import re
import time
import threading
from urllib.parse import quote

import requests
from flask import Flask, request, jsonify, Response, abort

app = Flask(__name__)

PLAYLIST_URL = os.environ.get(
    "PLAYLIST_URL",
    "https://raw.githubusercontent.com/kv7iptv/oneplay-tv-filter/refs/heads/main/docs/oneplay.m3u",
)

XTREAM_USER = os.environ.get("XTREAM_USER", "oneplay")
XTREAM_PASSWORD = os.environ.get("XTREAM_PASSWORD", "")
CACHE_SECONDS = int(os.environ.get("CACHE_SECONDS", "60"))

_cache = {"time": 0, "channels": []}
_lock = threading.Lock()


def load_channels():
    now = time.time()

    with _lock:
        if now - _cache["time"] < CACHE_SECONDS:
            return _cache["channels"]

        response = requests.get(
            PLAYLIST_URL,
            timeout=30,
            headers={"User-Agent": "OnePlay-Xtream/1.0"},
        )
        response.raise_for_status()
        content = response.text.lstrip("\ufeff")

        if "#EXTM3U" not in content:
            raise ValueError("A origem não retornou uma playlist M3U válida.")

        channels = []
        current = None

        for line in content.splitlines():
            line = line.strip()

            if line.startswith("#EXTINF:"):
                name = line.rsplit(",", 1)[-1].strip()
                group_match = re.search(
                    r'group-title="([^"]*)"',
                    line,
                    re.IGNORECASE,
                )
                logo_match = re.search(
                    r'tvg-logo="([^"]*)"',
                    line,
                    re.IGNORECASE,
                )
                id_match = re.search(
                    r'tvg-id="([^"]*)"',
                    line,
                    re.IGNORECASE,
                )

                current = {
                    "name": name,
                    "group": group_match.group(1).strip()
                    if group_match else "Outros",
                    "logo": logo_match.group(1).strip()
                    if logo_match else "",
                    "tvg_id": id_match.group(1).strip()
                    if id_match else "",
                    "url": "",
                }

            elif current and line and not line.startswith("#"):
                current["url"] = line
                if current["name"] and current["url"]:
                    channels.append(current)
                current = None

        if not channels:
            raise ValueError("Nenhum canal foi encontrado na playlist.")

        _cache["channels"] = channels
        _cache["time"] = now
        return channels


def authorized():
    username = request.args.get("username", "")
    password = request.args.get("password", "")

    return bool(
        XTREAM_PASSWORD
        and username == XTREAM_USER
        and password == XTREAM_PASSWORD
    )


def require_auth():
    if not authorized():
        abort(401)


def channel_id(index):
    return str(index + 1)


def channel_by_id(value):
    if not value.isdigit():
        return None

    index = int(value) - 1
    channels = load_channels()

    if 0 <= index < len(channels):
        return channels[index]

    return None


@app.get("/")
def home():
    return jsonify({
        "service": "OnePlay Xtream API",
        "status": "online",
        "playlist": "GitHub",
    })


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/player_api.php")
def player_api():
    require_auth()

    action = request.args.get("action", "")

    try:
        channels = load_channels()
    except Exception:
        app.logger.exception("Erro ao carregar playlist")
        return jsonify({"error": "Não foi possível carregar a playlist."}), 502

    if not action:
        return jsonify({
            "user_info": {
                "username": XTREAM_USER,
                "password": XTREAM_PASSWORD,
                "message": "Autenticado",
                "auth": 1,
                "status": "Active",
                "exp_date": None,
                "is_trial": "0",
                "active_cons": "0",
                "created_at": None,
                "max_connections": "1",
                "allowed_output_formats": ["ts", "m3u8"],
            },
            "server_info": {
                "url": request.host,
                "port": str(request.environ.get("SERVER_PORT", "80")),
                "https_port": "443",
                "server_protocol": request.scheme,
                "timezone": "America/Maceio",
                "timestamp_now": int(time.time()),
                "time_now": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        })

    if action == "get_live_categories":
        groups = sorted({c["group"] for c in channels}, key=str.casefold)
        return jsonify([
            {"category_id": str(i + 1), "category_name": group,
             "parent_id": 0}
            for i, group in enumerate(groups)
        ])

    if action == "get_live_streams":
        groups = sorted({c["group"] for c in channels}, key=str.casefold)
        group_ids = {group: str(i + 1) for i, group in enumerate(groups)}

        return jsonify([
            {
                "num": i + 1,
                "name": c["name"],
                "stream_type": "live",
                "stream_id": channel_id(i),
                "stream_icon": c["logo"],
                "epg_channel_id": c["tvg_id"],
                "category_id": group_ids[c["group"]],
                "category_ids": [int(group_ids[c["group"]])],
                "custom_sid": "",
                "tv_archive": 0,
                "direct_source": c["url"],
                "tv_archive_duration": 0,
            }
            for i, c in enumerate(channels)
        ])

    if action == "get_short_epg":
        return jsonify({"epg_listings": []})

    if action == "get_simple_data_table":
        return jsonify({"epg_listings": []})

    return jsonify({"error": "Ação não suportada", "action": action}), 400


@app.get("/get.php")
def get_m3u():
    require_auth()

    output = request.args.get("output", "ts").lower()
    if output not in ("ts", "m3u8"):
        output = "ts"

    try:
        channels = load_channels()
    except Exception:
        app.logger.exception("Erro ao carregar playlist")
        return "Não foi possível carregar a playlist.", 502

    lines = ["#EXTM3U"]

    for i, channel in enumerate(channels):
        name = channel["name"].replace("\r", " ").replace("\n", " ")
        group = channel["group"].replace('"', "'")
        logo = channel["logo"].replace('"', "'")

        lines.append(
            f'#EXTINF:-1 tvg-id="{channel["tvg_id"]}" '
            f'tvg-logo="{logo}" group-title="{group}",{name}'
        )
        lines.append(
            f'{request.url_root.rstrip("/")}/live/'
            f'{quote(XTREAM_USER)}/{quote(XTREAM_PASSWORD)}/{i + 1}.{output}'
        )

    return Response(
        "\n".join(lines) + "\n",
        mimetype="audio/x-mpegurl",
    )


@app.route("/live/<username>/<password>/<stream_file>", methods=["GET", "HEAD"])
def live_stream(username, password, stream_file):
    if username != XTREAM_USER or password != XTREAM_PASSWORD:
        abort(401)

    match = re.fullmatch(r"(\d+)\.(ts|m3u8)", stream_file, re.IGNORECASE)
    if not match:
        abort(404)

    channel = channel_by_id(match.group(1))
    if not channel:
        abort(404)

    # Redireciona a TV diretamente para a URL original do canal.
    return Response(
        status=302,
        headers={"Location": channel["url"]},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7000"))
    app.run(host="0.0.0.0", port=port)
  
