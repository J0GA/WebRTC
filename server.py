import sys
import subprocess
from pathlib import Path
from aiohttp import web
import aiohttp_jinja2
import jinja2

def install_dependencies():
    try:
        import aiohttp
        import aiohttp_jinja2
        import jinja2
    except ImportError:
        print("Устанавливаем необходимые зависимости...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Зависимости успешно установлены!")

# Проверяем и устанавливаем зависимости перед запуском
install_dependencies()

app = web.Application()

Path("web/static").mkdir(parents=True, exist_ok=True)
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("web"))
connected_peers = set()

app = web.Application()

# Создаем необходимые папки
Path("web/static").mkdir(parents=True, exist_ok=True)

aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("web"))

connected_peers = set()

async def index(request):
    return aiohttp_jinja2.render_template("index.html", request, {})

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    connected_peers.add(ws)

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = msg.data
                if data == '{"type":"hangup"}':
                    for peer in connected_peers:
                        if peer is not ws:
                            await peer.send_str(data)
                else:
                    for peer in connected_peers:
                        if peer is not ws:
                            await peer.send_str(data)
            elif msg.type == web.WSMsgType.ERROR:
                print(f"WebSocket error: {ws.exception()}")
    finally:
        connected_peers.remove(ws)
    return ws

app.router.add_get("/", index)
app.router.add_get("/ws", websocket_handler)
app.router.add_static("/static", "web/static")

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=5000)