import os
import sys
import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
from pathlib import Path
from PIL import Image
import pystray
import threading
import webbrowser
import json


class WebRTCServer:
    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        self.tray_icon = None
        self.loop = asyncio.new_event_loop()
        self.connections = set()  # Для хранения активных WebSocket соединений
        self.lock = asyncio.Lock()  # Блокировка для безопасного доступа к connections
        asyncio.set_event_loop(self.loop)

    def setup_routes(self):
        Path("web/static").mkdir(exist_ok=True)
        aiohttp_jinja2.setup(self.app, loader=jinja2.FileSystemLoader("web"))

        self.app.router.add_get("/", self.index)
        self.app.router.add_get("/ws", self.websocket_handler)
        self.app.router.add_static("/static", "web/static")

    async def index(self, request):
        """Обработчик главной страницы"""
        return aiohttp_jinja2.render_template("index.html", request, {})

    async def websocket_handler(self, request):
        """Обработчик WebSocket соединений с логикой WebRTC"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async with self.lock:
            self.connections.add(ws)

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        # Создаем копию соединений для безопасной итерации
                        async with self.lock:
                            connections = list(self.connections)

                        for connection in connections:
                            if connection is not ws and not connection.closed:
                                await connection.send_str(msg.data)
                    except json.JSONDecodeError:
                        print("Invalid JSON received")
                elif msg.type == web.WSMsgType.ERROR:
                    print(f"WebSocket error: {ws.exception()}")
        finally:
            async with self.lock:
                if ws in self.connections:
                    self.connections.remove(ws)

        return ws

    def create_tray_icon(self):
        """Создает иконку в системном трее"""
        try:
            image = Image.open('icon.png')
        except:
            image = Image.new('RGB', (64, 64), 'blue')

        menu = pystray.Menu(
            pystray.MenuItem('Открыть чат', self.open_browser),
            pystray.MenuItem('Выход', self.shutdown)
        )

        self.tray_icon = pystray.Icon(
            "WebRTC Server",
            image,
            "WebRTC Video Chat",
            menu
        )

    def open_browser(self):
        """Открывает веб-интерфейс в браузере"""
        webbrowser.open('http://localhost:5000')

    def shutdown(self):
        """Корректно завершает приложение"""
        print("Завершение работы сервера...")
        self.loop.call_soon_threadsafe(self.loop.stop)
        if self.tray_icon:
            self.tray_icon.stop()

    def run_tray(self):
        """Запускает иконку в трее в отдельном потоке"""
        self.create_tray_icon()
        self.tray_icon.run()

    async def start_server(self):
        """Запускает сервер"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)
        await site.start()
        print("Сервер запущен на http://localhost:5000")

    def run(self):
        """Основной метод запуска"""
        # Запускаем сервер в асинхронном цикле
        server_task = self.loop.create_task(self.start_server())

        # Запускаем иконку в трее в отдельном потоке
        threading.Thread(target=self.run_tray, daemon=True).start()

        # Открываем браузер через 2 секунды
        threading.Timer(2, self.open_browser).start()

        try:
             self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            # Создаем копию соединений для безопасного закрытия
            async def close_connections():
                async with self.lock:
                    connections = list(self.connections)
                for ws in connections:
                    if not ws.closed:
                        await ws.close()

            self.loop.run_until_complete(close_connections())
            self.loop.run_until_complete(self.app.shutdown())
            self.loop.close()
            sys.exit(0)

if __name__ == "__main__":
    server = WebRTCServer()
    server.run()