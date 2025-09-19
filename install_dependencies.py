#!/usr/bin/env python3
# install_dependencies.py - Instalar dependencias correctamente

import os
import sys
import subprocess
import platform

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    return version

def install_dependencies():
    """Instalar dependencias según la versión de Python"""
    python_version = sys.version_info
    
    # Dependencias base
    base_packages = [
        "pdfplumber==0.10.3",
        "Pillow==10.1.0",
        "openpyxl==3.1.2"
    ]
    
    # Dependencias según versión
    if python_version.minor <= 10:
        # Python 3.10 o anterior
        version_specific = [
            "pandas==2.0.3",
            "numpy==1.24.3",
            "scikit-learn==1.3.0",
            "matplotlib==3.7.2",
            "seaborn==0.12.2"
        ]
    else:
        # Python 3.11+
        version_specific = [
            "pandas==2.1.4",
            "numpy==1.26.0",
            "scikit-learn==1.3.2",
            "matplotlib==3.8.2",
            "seaborn==0.13.0"
        ]
    
    all_packages = base_packages + version_specific
    
    print("📦 Instalando dependencias...")
    for package in all_packages:
        print(f"Instalando {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} instalado correctamente")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando {package}: {e}")
            # Intentar instalación sin versión específica
            try:
                package_name = package.split('==')[0]
                print(f"Intentando instalar {package_name} sin versión específica...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                print(f"✅ {package_name} instalado correctamente")
            except:
                print(f"❌ No se pudo instalar {package_name}")

def check_tkinter():
    """Verificar si tkinter está disponible"""
    try:
        import tkinter
        print("✅ tkinter está disponible")
        return True
    except ImportError:
        print("❌ tkinter no está disponible")
        
        # Instrucciones para instalar tkinter
        system = platform.system()
        if system == "Linux":
            print("Para instalar tkinter en Linux:")
            print("Ubuntu/Debian: sudo apt-get install python3-tk")
            print("Fedora: sudo dnf install python3-tkinter")
            print("Arch: sudo pacman -S tk")
        elif system == "Darwin":  # macOS
            print("Tkinter debería venir incluido con Python en macOS")
            print("Si no está, reinstala Python desde python.org")
        elif system == "Windows":
            print("Tkinter debería venir incluido con Python en Windows")
            print("Al instalar Python, asegúrate de marcar 'Install tkinter'")
        
        return False

def main():
    print("🛠️  Instalador de dependencias para ExpenditureControl")
    print("=" * 50)
    
    # Verificar versión de Python
    python_version = check_python_version()
    
    # Verificar tkinter
    tkinter_available = check_tkinter()
    
    if not tkinter_available:
        print("\n⚠️  Advertencia: tkinter es necesario para la interfaz gráfica")
        response = input("¿Continuar con la instalación? (s/n): ")
        if response.lower() != 's':
            print("Instalación cancelada")
            return
    
    # Instalar dependencias
    install_dependencies()
    
    print("\n✅ Instalación completada!")
    print("\n📋 Para verificar la instalación, ejecuta:")
    print("python -c \"import pdfplumber, pandas, numpy, sklearn, matplotlib, seaborn, PIL; print('Todas las dependencias están instaladas correctamente')\"")

if __name__ == "__main__":
    main()