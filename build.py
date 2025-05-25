from PyInstaller.__main__ import run

build_params = [
    '--name=WebRTCVideoChat',
    '--onefile',
    '--windowed',
    '--noconsole',
    '--add-data=web;web',
    '--add-data=icon.png;.',
    '--hidden-import=pystray',
    '--hidden-import=PIL',
    '--clean',
    'server.py'
]

run(build_params)