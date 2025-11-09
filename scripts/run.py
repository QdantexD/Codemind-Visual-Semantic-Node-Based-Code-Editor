import sys
import argparse


def check():
    print("Verificando entorno...")
    print("Python:", sys.version)
    import fastapi
    import uvicorn
    import pydantic
    import requests
    import dearpygui.dearpygui as dpg
    print("Paquetes OK: fastapi, uvicorn, pydantic, requests, dearpygui")
    import os
    for path in ["backend", "ui", "main.py"]:
        exists = os.path.exists(path)
        print(f"{path}: {'OK' if exists else 'FALTA'}")


def test():
    print("Ejecutando prueba mínima de import...")
    try:
        from backend.server import app  # noqa: F401
        print("Import OK: backend.server.app")
        print("Nota: la prueba de WebSocket es interactiva y se valida desde la UI.")
    except Exception as e:
        print("Error al importar backend.server:", e)
        raise


def main():
    parser = argparse.ArgumentParser(description="Scripts utilitarios para Codermind Visual")
    parser.add_argument("command", choices=["check", "test"], help="Comando a ejecutar")
    args = parser.parse_args()

    if args.command == "check":
        check()
    elif args.command == "test":
        test()


if __name__ == "__main__":
    main()