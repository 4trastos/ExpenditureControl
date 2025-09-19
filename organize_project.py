#!/usr/bin/env python3
# organize_project.py - Script para organizar la estructura del proyecto

import os
import shutil
from pathlib import Path

def create_project_structure():
    # Directorios principales
    directories = [
        "ExpenditureControl/src",
        "ExpenditureControl/assets/icons",
        "ExpenditureControl/assets/samples",
        "ExpenditureControl/docs",
        "ExpenditureControl/tests/test_samples",
        "ExpenditureControl/build",
        "ExpenditureControl/dist",
        "MAC",
        "WINDOWS"
    ]
    
    # Crear directorios
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Creando directorio: {directory}")
    
    # Mover archivos existentes
    files_to_move = {
        'ExpenditureControl.py': 'ExpenditureControl/src/',
        'build.py': 'ExpenditureControl/',
        'requirements.txt': 'ExpenditureControl/',
        'install.txt': './'
    }
    
    for file, destination in files_to_move.items():
        if os.path.exists(file):
            shutil.move(file, destination + file)
            print(f"📄 Moviendo {file} -> {destination}")
    
    # Mover PDFs de muestra
    for platform_dir in ['MAC', 'WINDOWS']:
        pdf_source = f"{platform_dir}/pdf/test_01.PDF"
        if os.path.exists(pdf_source):
            shutil.move(pdf_source, "ExpenditureControl/assets/samples/test_01.PDF")
            print(f"📄 Moviendo PDF de muestra desde {platform_dir}")
    
    # Crear archivos básicos si no existen
    if not os.path.exists("ExpenditureControl/README.md"):
        with open("ExpenditureControl/README.md", "w") as f:
            f.write("# ExpenditureControl\n\nControl de gastos y procesamiento de facturas PDF\n")
    
    if not os.path.exists("ExpenditureControl/docs/instructions.md"):
        with open("ExpenditureControl/docs/instructions.md", "w") as f:
            f.write("# Instrucciones de uso\n\n## Instalación\n\n## Uso\n\n")
    
    print("✅ Estructura del proyecto creada exitosamente!")
    print("\n📋 Estructura final:")
    print_tree()

def print_tree():
    """Mostrar estructura de directorios"""
    for root, dirs, files in os.walk("ExpenditureControl"):
        level = root.replace("ExpenditureControl", "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    print("🛠️ Organizando estructura del proyecto...")
    create_project_structure()