"""
Biblioteka — System Tray Launcher
Pokreće FastAPI server i prikazuje ikonicu u system tray-u.
Dvostruki klik na ikonicu otvara aplikaciju u browseru.
"""

import os
import sys
import threading
import webbrowser
import socket

HOST = "0.0.0.0"
PORT = 8000


def get_local_ip():
    """Get the local network IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def start_server():
    """Start the uvicorn server."""
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, log_level="info")


def open_browser():
    """Open the application in the default browser."""
    webbrowser.open(f"http://127.0.0.1:{PORT}")


def main():
    # Set working directory to script location
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Load .env
    env_path = os.path.join("config", ".env")
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)

    local_ip = get_local_ip()
    print("=" * 50)
    print("  BIBLIOTEKA — Sistem upravljanja")
    print("=" * 50)
    print(f"  Lokalni pristup:  http://127.0.0.1:{PORT}")
    print(f"  Mrežni pristup:   http://{local_ip}:{PORT}")
    print(f"  API dokumentacija: http://127.0.0.1:{PORT}/docs")
    print("=" * 50)
    print("  Login: admin / admin123")
    print("  (Promenite lozinku posle prvog logovanja!)")
    print("=" * 50)
    print()

    try:
        # Try to use pystray for system tray icon
        import pystray
        from PIL import Image, ImageDraw

        def create_icon_image():
            img = Image.new("RGB", (64, 64), "#1a1a2e")
            draw = ImageDraw.Draw(img)
            draw.rectangle([12, 16, 52, 52], fill="#c45e2c")
            draw.rectangle([16, 12, 48, 20], fill="#c45e2c")
            draw.rectangle([20, 24, 44, 28], fill="#1a1a2e")
            draw.rectangle([20, 32, 44, 36], fill="#1a1a2e")
            draw.rectangle([20, 40, 36, 44], fill="#1a1a2e")
            return img

        def on_open(icon, item):
            open_browser()

        def on_quit(icon, item):
            icon.stop()
            os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Otvori u browseru", on_open, default=True),
            pystray.MenuItem(f"http://{local_ip}:{PORT}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Zatvori server", on_quit),
        )

        icon = pystray.Icon("Biblioteka", create_icon_image(), "Biblioteka", menu)

        # Start server in background thread
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        # Open browser after a short delay
        threading.Timer(2.0, open_browser).start()

        # Run tray icon (blocks)
        icon.run()

    except ImportError:
        # pystray not installed — run without system tray
        print("  (pystray nije instaliran — pokretanje bez system tray ikonice)")
        print("  Pritisnite Ctrl+C za zaustavljanje servera")
        print()

        # Open browser after a short delay
        threading.Timer(2.0, open_browser).start()

        # Start server (blocks)
        start_server()


if __name__ == "__main__":
    main()
