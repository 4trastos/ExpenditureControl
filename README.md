# ExpenditureControl
Control de pedidos

Aplicación en Python para el control de gastos e ingresos mediante la extracción de datos de facturas PDF, almacenamiento en base de datos y generación de estadísticas y visualizaciones.

---

## 📋 Tabla de contenido

- [Descripción](#descripción)  
- [Características](#características)  
- [Instalación](#instalación)  
- [Uso](#uso)  
- [Construcción del ejecutable](#construcción-del-ejecutable)  
- [Estructura del proyecto](#estructura-del-proyecto)  
- [Contribuciones](#contribuciones)  
- [Licencia](#licencia)  

---

## Descripción

**ExpenditureControl** te ayuda a:

- Procesar facturas en PDF para extraer datos.  
- Guardar gastos e ingresos en una base SQLite.  
- Calcular estadísticas (totales, medias, artículo más costoso, gasto mensual, etc.).  
- Generar gráficos y predicciones de tendencias de gastos.  
- Exportar la información a CSV y PNG.  
- Usar una interfaz gráfica (Tkinter) sencilla y ligera.

---

## Características

- 📂 **Procesamiento de PDFs** con `pdfplumber` (o librería similar).  
- 💾 **Base de datos SQLite** para persistencia.  
- 📊 **Estadísticas financieras**: gastos totales, promedio, comparativas, etc.  
- 📈 **Visualizaciones** con `matplotlib` (tendencias, categorías, ratios).  
- 💻 **Interfaz gráfica** en Tkinter.  
- 🔮 **Predicciones** de gastos futuros con regresión lineal (`scikit-learn`).  
- 📤 **Exportación** a CSV e imágenes.  

---

## Instalación

1. Clona el repositorio:

 ```bash
   git clone https://github.com/4trastos/ExpenditureControl.git
   cd ExpenditureControl
````

2. Crea un entorno virtual (opcional pero recomendado):

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # En Windows: venv\Scripts\activate
   ```

3. Instala dependencias:

   ```bash
   pip install -r requirements.txt
   ```

   Si no tienes `requirements.txt`, instala manualmente:

   ```bash
   pip install pdfplumber pandas numpy matplotlib scikit-learn
   ```

---

## Uso

1. Ejecuta la aplicación:

   ```bash
   python ExpenditureControl.py
   ```

2. Desde la interfaz podrás:

   * Añadir gastos o ingresos.
   * Procesar PDFs de facturas.
   * Generar estadísticas y gráficos.
   * Exportar datos.

3. Los gráficos se guardan como imágenes PNG en el directorio de trabajo.

---

## Construcción del ejecutable

Con [PyInstaller](https://pyinstaller.org/):

```bash
pyinstaller --onefile --windowed --name=ExpenditureControl \
-hidden-import=matplotlib.backends.backend_tkagg \
 ExpenditureControl.py
```

Agrega `--hidden-import` extra si PyInstaller te avisa de módulos faltantes (`matplotlib`, `numpy`, etc.).

---

## Estructura del proyecto

```
ExpenditureControl/
│
├── ExpenditureControl.py         # Código principal
├── build.py                      # Script para crear ejecutables
├── install_dependencies.py       # Instalar dependencias en Windows
├── install_dependencies_ubuntu.py# Instalar dependencias en Ubuntu
├── organize_project.py           # Script de organización
├── IMG/                          # Imágenes del proyecto
├── TEST/                         # Archivos de prueba
├── MAC/                          # Configuración específica de macOS
├── README.md
└── requirements.txt (opcional)
```

## Licencia

Distribuido bajo la licencia MIT.
Consulta el archivo `LICENSE` para más información.

````
