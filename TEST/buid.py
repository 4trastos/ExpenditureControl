#!/usr/bin/env python3
# build.py - Script para crear ejecutables multiplataforma

import os
import sys
import platform
import subprocess

def build_executable():
    system = platform.system()
    script_name = "ExpenditureControl.py"
    app_name = "ExpenditureControl"
    
    # Comando base
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--name={app_name}",
        "--clean",
        "--noconfirm"
    ]
    
    # Añadir imports ocultos necesarios para sklearn y pandas
    hidden_imports = [
        "--hidden-import=sklearn.neighbors._typedefs",
        "--hidden-import=sklearn.utils._weight_vector",
        "--hidden-import=pandas._libs.tslibs.timedeltas",
        "--hidden-import=sklearn.neighbors._quad_tree",
        "--hidden-import=sklearn.tree._utils",
        "--hidden-import=matplotlib.backends.backend_tkagg"
    ]
    
    cmd.extend(hidden_imports)
    
    # Añadir icono según el sistema
    if system == "Windows":
        if os.path.exists("icon.ico"):
            cmd.append("--icon=icon.ico")
        cmd.append("--add-data=*.pdf;.")
    elif system == "Darwin":  # macOS
        if os.path.exists("icon.icns"):
            cmd.append("--icon=icon.icns")
        cmd.append("--add-data=*.pdf:.")
    else:  # Linux
        cmd.append("--add-data=*.pdf:.")
    
    # Añadir el script principal
    cmd.append(script_name)
    
    print(f"Creando ejecutable para {system}...")
    print("Comando:", " ".join(cmd))
    
    # Ejecutar pyinstaller
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Ejecutable creado exitosamente!")
        print(f"El ejecutable está en: dist/{app_name}{'.exe' if system == 'Windows' else ''}")
    except subprocess.CalledProcessError as e:
        print("❌ Error al crear el ejecutable:")
        print(e.stderr)
        return False
    
    return True

def create_icons():
    """Crear iconos si no existen"""
    # Puedes añadir aquí la creación de iconos básicos si no tienes
    print("ℹ️  Recuerda añadir icon.ico para Windows y/o icon.icns para macOS")
    print("   para tener un icono personalizado en tu aplicación")

if __name__ == "__main__":
    if not os.path.exists("ExpenditureControl.py"):
        print("❌ Error: El archivo ExpenditureControl.py no existe")
        sys.exit(1)
    
    print("🛠️  Constructor de ExpenditureControl")
    print("=" * 40)
    
    create_icons()
    
    if build_executable():
        print("\n🎉 ¡Build completado!")
        print("\n📋 Instrucciones de uso:")
        print("1. El ejecutable está en la carpeta 'dist/'")
        print("2. Para Windows: Ejecuta ExpenditureControl.exe")
        print("3. Para macOS: Ejecuta ExpenditureControl")
        print("4. Para Linux: Ejecuta ./ExpenditureControl")
    else:
        sys.exit(1)