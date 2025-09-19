#!/usr/bin/env python3
# install_dependencies_ubuntu.py - Instalar dependencias en Ubuntu con PEP 668

import os
import sys
import subprocess
import platform

def create_virtual_environment():
    """Crear entorno virtual"""
    venv_path = "venv"
    
    if not os.path.exists(venv_path):
        print("🐍 Creando entorno virtual...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", venv_path])
            print("✅ Entorno virtual creado")
            return True
        except subprocess.CalledProcessError:
            print("❌ Error creando entorno virtual")
            return False
    else:
        print("✅ Entorno virtual ya existe")
        return True

def activate_virtual_environment():
    """Activar entorno virtual"""
    # No podemos activar el venv desde el script padre directamente
    # En su lugar, devolvemos el path al pip del venv
    if os.name == 'nt':  # Windows
        pip_path = os.path.join("venv", "Scripts", "pip.exe")
        python_path = os.path.join("venv", "Scripts", "python.exe")
    else:  # Unix/Linux
        pip_path = os.path.join("venv", "bin", "pip")
        python_path = os.path.join("venv", "bin", "python")
    
    return pip_path, python_path

def install_in_virtualenv():
    """Instalar dependencias en el entorno virtual"""
    pip_path, python_path = activate_virtual_environment()
    
    if not os.path.exists(pip_path):
        print("❌ pip no encontrado en el entorno virtual")
        return False
    
    packages = [
        "pdfplumber==0.10.3",
        "pandas==2.1.4", 
        "numpy==1.26.0",
        "scikit-learn==1.3.2",
        "matplotlib==3.8.2",
        "seaborn==0.13.0",
        "Pillow==10.1.0",
        "openpyxl==3.1.2"
    ]
    
    print("📦 Instalando dependencias en entorno virtual...")
    
    for package in packages:
        print(f"Instalando {package}...")
        try:
            subprocess.check_call([pip_path, "install", package])
            print(f"✅ {package} instalado correctamente")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando {package}: {e}")
            # Intentar sin versión específica
            try:
                package_name = package.split('==')[0]
                print(f"Intentando instalar {package_name}...")
                subprocess.check_call([pip_path, "install", package_name])
                print(f"✅ {package_name} instalado")
            except:
                print(f"❌ No se pudo instalar {package_name}")
                return False
    
    return True

def check_system_dependencies():
    """Verificar dependencias del sistema"""
    print("🖥️  Verificando dependencias del sistema...")
    
    try:
        # Verificar que python3-venv está instalado
        subprocess.check_call(["dpkg", "-s", "python3-venv"], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        print("✅ python3-venv está instalado")
        return True
    except subprocess.CalledProcessError:
        print("❌ python3-venv no está instalado")
        print("Instalando python3-venv...")
        try:
            subprocess.check_call(["sudo", "apt", "install", "-y", "python3-venv"])
            return True
        except:
            print("❌ No se pudo instalar python3-venv")
            return False

def main():
    print("🛠️  Instalador para Ubuntu (PEP 668 compatible)")
    print("=" * 60)
    
    # Verificar que estamos en Linux
    if platform.system() != "Linux":
        print("⚠️  Este script está optimizado para Ubuntu/Linux")
    
    # Verificar dependencias del sistema
    if not check_system_dependencies():
        print("❌ Dependencias del sistema faltantes")
        sys.exit(1)
    
    # Crear entorno virtual
    if not create_virtual_environment():
        print("❌ No se pudo crear el entorno virtual")
        sys.exit(1)
    
    # Instalar dependencias en el venv
    if install_in_virtualenv():
        print("\n🎉 ¡Instalación completada!")
        print("\n📋 Para usar la aplicación:")
        print("   source venv/bin/activate")
        print("   python src/ExpenditureControl.py")
        print("\n📋 Para construir el ejecutable:")
        print("   source venv/bin/activate") 
        print("   python build.py")
    else:
        print("\n❌ Error en la instalación")
        sys.exit(1)

if __name__ == "__main__":
    main()