from aiohttp import web
import aiohttp_jinja2
import jinja2
import os

app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("web"))

connected_peers = set()  # Сет для хранения активных WebSocket-соединений

async def index(request):
    return aiohttp_jinja2.render_template("index.html", request, {})

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)  # Исправлено: было prepare
    connected_peers.add(ws)

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            data = msg.data
            # Если пришло сообщение о завершении звонка
            if data == '{"type":"hangup"}':
                # Пересылаем всем другим участникам
                for peer in connected_peers:
                    if peer is not ws:
                        await peer.send_str(data)
            else:
                # Обычная пересылка сигнальных сообщений
                for peer in connected_peers:
                    if peer is not ws:
                        await peer.send_str(data)
        elif msg.type == web.WSMsgType.ERROR:
            print(f"WebSocket error: {ws.exception()}")

    connected_peers.remove(ws)
    return ws

app.router.add_get("/", index)
app.router.add_get("/ws", websocket_handler)
app.router.add_static("/static", "web")

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=5000)