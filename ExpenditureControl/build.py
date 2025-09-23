#!/usr/bin/env python3
# build.py - Script para crear ejecutables multiplataforma

import os
import sys
import platform
import subprocess
import shutil
import glob
from pathlib import Path

def build_executable(platform_type=None):
    """Construir ejecutable para una plataforma específica"""
    if platform_type is None:
        platform_type = platform.system()
    
    script_path = "src/ExpenditureControl.py"
    app_name = "ExpenditureControl"
    
    # Configuración por plataforma
    config = {
        "Windows": {
            "icon": "assets/icons/icon.ico",
            "add_data": [],
            "output_dir": "../WINDOWS",
            "extension": ".exe"
        },
        "Darwin": {
            "icon": "assets/icons/icon.icns",
            "add_data": [],
            "output_dir": "../MAC",
            "extension": ".app"
        }
    }
    
    # Añadir archivos PDF específicos en lugar de usar patrones
    pdf_files = glob.glob("assets/samples/*.pdf")
    pdf_files.extend(glob.glob("assets/samples/*.PDF"))
    
    for pdf_file in pdf_files:
        if platform_type == "Windows":
            config[platform_type]["add_data"].append(f"{pdf_file};assets/samples/")
        else:
            config[platform_type]["add_data"].append(f"{pdf_file}:assets/samples/")
    
    if platform_type not in config:
        print(f"❌ Plataforma no soportada: {platform_type}")
        return False
    
    cfg = config[platform_type]
    
    # Comando base de pyinstaller - CAMBIO IMPORTANTE: usar --onedir en lugar de --onefile para macOS
    cmd = [
        "pyinstaller",
        "--windowed",  # Removido --onefile para macOS
        f"--name={app_name}",
        "--clean",
        "--noconfirm",
        f"--workpath=build",
        f"--distpath=dist",
    ]
    
    # Para Windows, podemos mantener --onefile
    if platform_type == "Windows":
        cmd.insert(1, "--onefile")
    
    # Añadir icono si existe
    if os.path.exists(cfg["icon"]):
        cmd.append(f"--icon={cfg['icon']}")
        print(f"✅ Usando icono: {cfg['icon']}")
    else:
        print(f"⚠️  Icono no encontrado: {cfg['icon']}")
    
    # Añadir datos adicionales (archivos PDF)
    for data_item in cfg["add_data"]:
        cmd.append(f"--add-data={data_item}")
    
    # Añadir imports ocultos necesarios
    hidden_imports = [
        "--hidden-import=sklearn.neighbors._typedefs",
        "--hidden-import=sklearn.utils._weight_vector",
        "--hidden-import=pandas._libs.tslibs.timedeltas",
        "--hidden-import=sklearn.neighbors._quad_tree",
        "--hidden-import=sklearn.tree._utils",
        "--hidden-import=matplotlib.backends.backend_tkagg",
        "--hidden-import=tkinter",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=pdfminer.six",
        "--hidden-import=PyPDF2",
        "--hidden-import=matplotlib.backends.backend_agg",
        "--hidden-import=matplotlib.pyplot",
        "--hidden-import=numpy.core._methods",
        "--hidden-import=numpy.lib.format"
    ]
    
    cmd.extend(hidden_imports)
    
    # Añadir el script principal
    cmd.append(script_path)
    
    print(f"🔨 Creando ejecutable para {platform_type}...")
    print("Comando:", " ".join(cmd))
    
    # Ejecutar pyinstaller
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Ejecutable creado exitosamente!")
        
        # Mover ejecutable a la carpeta de plataforma
        if platform_type == "Darwin":
            source_path = f"dist/{app_name}.app"
            dest_path = f"{cfg['output_dir']}/{app_name}.app"
        else:
            source_path = f"dist/{app_name}.exe"
            dest_path = f"{cfg['output_dir']}/{app_name}.exe"
        
        if os.path.exists(source_path):
            # Crear directorio de destino si no existe
            os.makedirs(cfg["output_dir"], exist_ok=True)
            
            # Mover el ejecutable
            if platform_type == "Darwin" and os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            elif os.path.exists(dest_path):
                os.remove(dest_path)
            
            shutil.move(source_path, dest_path)
            print(f"📦 Ejecutable movido a: {dest_path}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Error al crear el ejecutable:")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def build_all_platforms():
    """Construir para todas las plataformas"""
    print("🛠️  Constructor de ExpenditureControl para todas las plataformas")
    print("=" * 50)
    
    # Verificar que el script principal existe
    if not os.path.exists("src/ExpenditureControl.py"):
        print("❌ Error: El archivo ExpenditureControl.py no existe en src/")
        print("📁 Directorio actual:", os.getcwd())
        print("📁 Contenido de src/:", os.listdir("src") if os.path.exists("src") else "No existe")
        return False
    
    # Verificar que hay archivos PDF de muestra
    pdf_files = glob.glob("assets/samples/*.pdf") + glob.glob("assets/samples/*.PDF")
    if not pdf_files:
        print("⚠️  No se encontraron archivos PDF en assets/samples/")
        print("   Se creará el ejecutable sin archivos de muestra")
    else:
        print(f"✅ Encontrados {len(pdf_files)} archivos PDF de muestra")
    
    # Construir para la plataforma actual primero
    current_platform = platform.system()
    print(f"🏗️  Construyendo para plataforma actual: {current_platform}")
    
    if build_executable(current_platform):
        print(f"\n✅ Build para {current_platform} completado!")
        return True
    else:
        return False

def check_icons():
    """Verificar si los iconos existen"""
    icons = {
        "Windows": "assets/icons/icon.ico",
        "Darwin": "assets/icons/icon.icns"
    }
    
    all_exist = True
    for platform_name, icon_path in icons.items():
        if os.path.exists(icon_path):
            print(f"✅ Icono para {platform_name}: {icon_path}")
        else:
            print(f"⚠️  Icono no encontrado para {platform_name}: {icon_path}")
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    try:
        import pdfplumber
        import pandas as pd
        import numpy as np
        import sklearn
        import matplotlib
        import seaborn as sns
        from PIL import Image
        import tkinter as tk
        print("✅ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("   Ejecuta: pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    print("📁 Directorio de trabajo actual:", os.getcwd())
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Verificar iconos
    icons_exist = check_icons()
    if not icons_exist:
        print("\n⚠️  Algunos iconos no se encontraron. El ejecutable se creará sin icono personalizado.")
    
    if build_all_platforms():
        print("\n🎉 ¡Build completado!")
        print("\n📋 Ejecutables creados en:")
        current_platform = platform.system()
        if current_platform == "Darwin":
            print("   - ../MAC/ExpenditureControl.app")
            print("\n💡 Para ejecutar en macOS:")
            print("   open ../MAC/ExpenditureControl.app")
        elif current_platform == "Windows":
            print("   - ../WINDOWS/ExpenditureControl.exe")
        else:
            print("   - Consulta la carpeta dist/ para tu plataforma")
    else:
        sys.exit(1)