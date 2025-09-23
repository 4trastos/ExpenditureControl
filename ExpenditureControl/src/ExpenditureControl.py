import pdfplumber
import pandas as pd
import re
import os
import glob
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import sqlite3
import shutil
import sys
import matplotlib
matplotlib.use("Agg")  # Forzar backend no interactivo para evitar conflictos con Tkinter
import matplotlib.pyplot as plt

def get_app_data_path():
    """Obtiene la ruta para los datos de la aplicación."""
    if sys.platform == "win32":
        path = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'ExpenditureControl')
    elif sys.platform == "darwin":
        path = os.path.join(os.path.expanduser('~/Library/Application Support'), 'ExpenditureControl')
    else:
        path = os.path.join(os.path.expanduser('~/.local/share'), 'ExpenditureControl')
    
    os.makedirs(path, exist_ok=True)
    return path

class DatabaseManager:
    def __init__(self, db_name="expenditure_data.db"):
        app_data_path = get_app_data_path()
        self.db_path = os.path.join(app_data_path, db_name)

    def create_tables(self):
        """Crea las tablas si no existen."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            items_table = """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                invoice_number TEXT,
                invoice_date TEXT,
                item_number TEXT,
                position INTEGER,
                quantity REAL,
                unit_price REAL,
                product_code TEXT,
                discount REAL,
                iva REAL,
                net_value REAL,
                description TEXT
            );
            """
            
            invoices_table = """
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY,
                invoice_number TEXT UNIQUE,
                invoice_date TEXT,
                ports REAL,
                net_value REAL,
                iva REAL,
                iva_amount REAL,
                total_amount REAL
            );
            """
            
            cursor.execute(items_table)
            cursor.execute(invoices_table)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error creando tablas de la base de datos: {e}")
            messagebox.showerror("Error de Base de Datos", f"No se pudo crear las tablas: {e}")

    def insert_data(self, df_items, df_totals):
        """Inserta datos en la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            items_to_insert = df_items.to_dict('records')
            for item in items_to_insert:
                # Corregido: convertir Timestamp a cadena de texto, manejando NaT
                invoice_date_ts = item.get('Fecha Factura')
                if pd.isna(invoice_date_ts):
                    invoice_date_str = None
                else:
                    invoice_date_str = invoice_date_ts.strftime('%Y-%m-%d')
                
                cursor.execute("""
                    INSERT OR REPLACE INTO items (
                        invoice_number, invoice_date, item_number, position, quantity, 
                        unit_price, product_code, discount, iva, net_value, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get('Nº Factura'), invoice_date_str, item.get('Nº Artículo'),
                    item.get('Posición'), item.get('Cantidad'), item.get('Precio Unitario (EUR)'),
                    item.get('Código Producto'), item.get('Descuento %'), item.get('IVA %'),
                    item.get('Valor Neto (EUR)'), item.get('Descripción')
                ))

            totals_to_insert = df_totals.to_dict('records')
            for total in totals_to_insert:
                # Corregido: convertir Timestamp a cadena de texto, manejando NaT
                invoice_date_ts = total.get('Fecha Factura')
                if pd.isna(invoice_date_ts):
                    invoice_date_str = None
                else:
                    invoice_date_str = invoice_date_ts.strftime('%Y-%m-%d')
                
                cursor.execute("""
                    INSERT OR IGNORE INTO invoices (
                        invoice_number, invoice_date, ports, net_value, iva, iva_amount, total_amount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    total.get('Nº Factura'), invoice_date_str, total.get('Portes (EUR)'),
                    total.get('Valor Neto (EUR)'), total.get('IVA %'), total.get('Importe IVA (EUR)'),
                    total.get('Importe Total (EUR)')
                ))
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error insertando datos en la base de datos: {e}")
            raise
    
    def get_all_data(self):
        """Obtiene todos los datos de la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            df_items = pd.read_sql_query("SELECT * FROM items", conn)
            df_invoices = pd.read_sql_query("SELECT * FROM invoices", conn)
            conn.close()
            
            if 'invoice_date' in df_items.columns:
                df_items['invoice_date'] = pd.to_datetime(df_items['invoice_date'])
            if 'invoice_date' in df_invoices.columns:
                df_invoices['invoice_date'] = pd.to_datetime(df_invoices['invoice_date'])

            if not df_items.empty:
                df_items.rename(columns={
                    'invoice_number': 'Nº Factura', 'invoice_date': 'Fecha Factura', 'item_number': 'Nº Artículo',
                    'position': 'Posición', 'quantity': 'Cantidad', 'unit_price': 'Precio Unitario (EUR)',
                    'product_code': 'Código Producto', 'discount': 'Descuento %', 'iva': 'IVA %',
                    'net_value': 'Valor Neto (EUR)', 'description': 'Descripción'
                }, inplace=True)
            
            if not df_invoices.empty:
                df_invoices.rename(columns={
                    'invoice_number': 'Nº Factura', 'invoice_date': 'Fecha Factura', 'ports': 'Portes (EUR)',
                    'net_value': 'Valor Neto (EUR)', 'iva': 'IVA %', 'iva_amount': 'Importe IVA (EUR)',
                    'total_amount': 'Importe Total (EUR)'
                }, inplace=True)

            return df_items, df_invoices
        except Exception as e:
            print(f"Error obteniendo datos de la base de datos: {e}")
            return pd.DataFrame(), pd.DataFrame()

class PDFInvoiceProcessor:
    def __init__(self):
        self.items_data = []
        self.totals_data = []
        self.invoice_dates = []
        self.invoice_numbers = []
        
    def extract_data_from_text(self, text, filename):
        items_data = []
        totals_data = []
        invoice_date = None
        invoice_number = None
        
        lines = text.split('\n')
        
        for line in lines:
            if 'Nº factura' in line:
                invoice_match = re.search(r'Nº factura\s+(\S+)', line)
                if invoice_match:
                    invoice_number = invoice_match.group(1).strip()
                    break
        
        for line in lines:
            if 'Fecha' in line:
                date_match = re.search(r'Fecha\s+(\d{2}\.\d{2}\.\d{4})', line)
                if date_match:
                    try:
                        invoice_date = datetime.strptime(date_match.group(1), '%d.%m.%Y')
                        break
                    except ValueError:
                        invoice_date = None
        
        # NUEVO PATRÓN DE EXTRACCIÓN
        item_pattern = re.compile(r'^\s*(\d{13,})\s+(\S+)\s+(\d+)\s+([\d,.-]+)\s+(\S+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)$')
        # NUEVO PATRÓN PARA LA DESCRIPCIÓN EN LA LÍNEA SIGUIENTE
        description_pattern = re.compile(r'^(?!Nº pedido Oficina)(?!Albarán)(?!Dirección de envío)(?!WURTH)\s+(.*)$')
        total_pattern = re.compile(r'^\s*([\d,]+)\s+([\d,]+)\s+([\d,]+%)\s+([\d,]+)\s+([\d,]+)$')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            item_match = item_pattern.search(line)
            if item_match:
                item_data = list(item_match.groups())
                description_found = False
                # Busca la descripción en las siguientes 2 líneas
                for j in range(1, 3):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        description_match = description_pattern.search(next_line)
                        if description_match:
                            description = description_match.group(1).strip()
                            if description and '€' not in description:
                                item_data.append(description)
                                description_found = True
                                break
                
                if not description_found:
                    item_data.append("Descripción no encontrada")
                
                items_data.append(item_data)
                continue
                
            total_match = total_pattern.search(line)
            if total_match:
                totals_data.append(list(total_match.groups()))
        
        for item in items_data:
            item.extend([invoice_number, invoice_date])
        
        for total in totals_data:
            total.extend([invoice_number, invoice_date])

        return items_data, totals_data, invoice_date, invoice_number

    def process_pdf_directory(self, directory_path):
        pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
        pdf_files.extend(glob.glob(os.path.join(directory_path, "*.PDF")))
        
        all_items = []
        all_totals = []
        
        for pdf_file in pdf_files:
            try:
                print(f"Procesando: {os.path.basename(pdf_file)}")
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        items, totals, date, number = self.extract_data_from_text(text, os.path.basename(pdf_file))
                        
                        all_items.extend(items)
                        all_totals.extend(totals)
                        
                        if date:
                            self.invoice_dates.append(date)
                        if number:
                            self.invoice_numbers.append(number)
                            
            except Exception as e:
                print(f"Error procesando {pdf_file}: {str(e)}")
        
        return all_items, all_totals

    def create_dataframes(self, items_data, totals_data):
        df_items = pd.DataFrame()
        if items_data:
            df_items = pd.DataFrame(items_data)
            
            item_columns = [
                "Nº Artículo", "Posición", "Cantidad", "Precio Unitario (EUR)", 
                "Código Producto", "Descuento %", "IVA %", "Valor Neto (EUR)",
                "Descripción", "Nº Factura", "Fecha Factura"
            ]
            
            if df_items.shape[1] == len(item_columns):
                df_items.columns = item_columns
            
            numeric_item_columns = ["Cantidad", "Precio Unitario (EUR)", "Descuento %", "IVA %", "Valor Neto (EUR)"]
            for col in numeric_item_columns:
                if col in df_items.columns:
                    df_items[col] = df_items[col].str.replace(',', '.').astype(float)
            
            if "Fecha Factura" in df_items.columns:
                df_items["Fecha Factura"] = pd.to_datetime(df_items["Fecha Factura"])
        
        df_totals = pd.DataFrame()
        if totals_data:
            df_totals = pd.DataFrame(totals_data)
            
            total_columns = [
                "Portes (EUR)", "Valor Neto (EUR)", "IVA %", 
                "Importe IVA (EUR)", "Importe Total (EUR)", "Nº Factura", "Fecha Factura"
            ]
            
            if df_totals.shape[1] == len(total_columns):
                df_totals.columns = total_columns
            
            numeric_total_columns = ["Portes (EUR)", "Valor Neto (EUR)", "Importe IVA (EUR)", "Importe Total (EUR)"]
            for col in numeric_total_columns:
                if col in df_totals.columns:
                    df_totals[col] = df_totals[col].str.replace(',', '.').astype(float)
            
            if "IVA %" in df_totals.columns:
                df_totals["IVA %"] = df_totals["IVA %"].str.replace('%', '').str.replace(',', '.').astype(float)
            
            if "Fecha Factura" in df_totals.columns:
                df_totals["Fecha Factura"] = pd.to_datetime(df_totals["Fecha Factura"])
        
        return df_items, df_totals
    
    def generate_statistics(self, df_items, df_totals):
        stats = {}
        if not df_items.empty:
            stats['total_invoices'] = len(df_items['Nº Factura'].unique())
            stats['total_items'] = len(df_items)
            stats['total_spent'] = df_items['Valor Neto (EUR)'].sum()
            stats['avg_item_price'] = df_items['Precio Unitario (EUR)'].mean()
            stats['most_expensive_item'] = df_items.loc[df_items['Precio Unitario (EUR)'].idxmax()]
            
            # FILTRADO DE VALORES NaN
            df_items_filtered = df_items.dropna(subset=['Fecha Factura', 'Valor Neto (EUR)'])
            
            df_items_filtered['Mes'] = df_items_filtered['Fecha Factura'].dt.to_period('M')
            monthly_spending = df_items_filtered.groupby('Mes')['Valor Neto (EUR)'].sum()
            stats['monthly_spending'] = monthly_spending
            
            top_products = df_items_filtered['Descripción'].value_counts().head(10)
            stats['top_products'] = top_products
            
            spending_per_product = df_items_filtered.groupby('Descripción')['Valor Neto (EUR)'].sum().sort_values(ascending=False).head(10)
            stats['spending_per_product'] = spending_per_product
            
            # NUEVOS CAMPOS
            # Total de impuestos
            if not df_totals.empty:
                stats['total_taxes'] = df_totals['Importe IVA (EUR)'].sum()
            
            # Gasto por producto
            stats['spending_per_product'] = df_items_filtered.groupby('Descripción')['Valor Neto (EUR)'].sum().sort_values(ascending=False)
            
            # Total de cada producto comprado
            stats['total_quantity_per_product'] = df_items_filtered.groupby('Descripción')['Cantidad'].sum().sort_values(ascending=False)

        if not df_totals.empty:
            stats['avg_invoice_total'] = df_totals['Importe Total (EUR)'].mean()
        
        return stats
    
    def predict_future_spending(self, df_items):
        if df_items.empty or 'Fecha Factura' not in df_items.columns:
            return None, None
        
        # FILTRADO DE VALORES NaN
        df_items_filtered = df_items.dropna(subset=['Fecha Factura', 'Valor Neto (EUR)'])
        if df_items_filtered.empty:
            return None, None
            
        df_items_filtered['Fecha Numerica'] = (df_items_filtered['Fecha Factura'] - df_items_filtered['Fecha Factura'].min()).dt.days
        monthly_data = df_items_filtered.groupby(df_items_filtered['Fecha Factura'].dt.to_period('M'))['Valor Neto (EUR)'].sum().reset_index()
        monthly_data['Mes'] = range(len(monthly_data))
        
        if len(monthly_data) < 3:
            return None, None
        
        X = monthly_data['Mes'].values.reshape(-1, 1)
        y = monthly_data['Valor Neto (EUR)'].values
        
        poly = PolynomialFeatures(degree=2)
        X_poly = poly.fit_transform(X)
        
        model = LinearRegression()
        model.fit(X_poly, y)
        
        future_months_idx = np.array(range(len(monthly_data), len(monthly_data) + 6)).reshape(-1, 1)
        future_months_poly = poly.transform(future_months_idx)
        predictions = model.predict(future_months_poly)
        
        last_date = df_items_filtered['Fecha Factura'].max()
        future_dates = pd.date_range(start=last_date, periods=7, freq='M')[1:]
        
        return predictions, future_dates

    def generate_visualizations(self, df_items, df_totals, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # FILTRADO DE VALORES NaN
        df_items_filtered = df_items.dropna(subset=['Fecha Factura', 'Valor Neto (EUR)'])

        if not df_items_filtered.empty and 'Fecha Factura' in df_items_filtered.columns:
            plt.figure(figsize=(12, 8))
            df_items_filtered['Mes'] = df_items_filtered['Fecha Factura'].dt.to_period('M')
            monthly_spending = df_items_filtered.groupby('Mes')['Valor Neto (EUR)'].sum()
            
            monthly_spending.plot(kind='bar', color='skyblue')
            plt.title('Gastos Mensuales en Materiales')
            plt.xlabel('Mes')
            plt.ylabel('Euros (EUR)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'gastos_mensuales.png'))
            plt.close()
        
        if not df_items_filtered.empty and 'Descripción' in df_items_filtered.columns and 'Valor Neto (EUR)' in df_items_filtered.columns:
            plt.figure(figsize=(12, 8))
            spending_per_product = df_items_filtered.groupby('Descripción')['Valor Neto (EUR)'].sum().sort_values(ascending=False).head(10)
            
            spending_per_product.plot(kind='barh', color='lightcoral')
            plt.title('Top 10 Productos por Gasto')
            plt.xlabel('Gasto Total (EUR)')
            plt.ylabel('Producto')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'gasto_por_producto.png'))
            plt.close()

        if not df_items_filtered.empty and 'Descripción' in df_items_filtered.columns and 'Cantidad' in df_items_filtered.columns:
            plt.figure(figsize=(12, 8))
            quantity_per_product = df_items_filtered.groupby('Descripción')['Cantidad'].sum().sort_values(ascending=False).head(10)
            
            quantity_per_product.plot(kind='barh', color='lightgreen')
            plt.title('Top 10 Productos por Cantidad Comprada')
            plt.xlabel('Cantidad Total')
            plt.ylabel('Producto')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'cantidad_por_producto.png'))
            plt.close()
            
        predictions, future_dates = self.predict_future_spending(df_items)
        if predictions is not None:
            plt.figure(figsize=(12, 8))
            df_items_filtered['Mes'] = df_items_filtered['Fecha Factura'].dt.to_period('M')
            monthly_spending = df_items_filtered.groupby('Mes')['Valor Neto (EUR)'].sum()
            
            all_months = monthly_spending.index.astype(str).tolist()
            all_months.extend([d.strftime('%Y-%m') for d in future_dates])

            all_values = monthly_spending.values.tolist()
            all_values.extend(predictions)
            
            plt.plot(monthly_spending.index.astype(str), monthly_spending.values, label='Gastos históricos', marker='o', color='b')
            plt.plot(all_months[-len(predictions):], predictions, label='Predicción (6 meses)', marker='x', linestyle='--', color='r')
            
            plt.title('Gastos Mensuales y Predicción de Futuros Gastos')
            plt.xlabel('Mes')
            plt.ylabel('Euros (EUR)')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'prediccion_gastos.png'))
            plt.close()

class PDFProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesador de Facturas PDF")
        self.root.geometry("1000x700")
        
        self.processor = PDFInvoiceProcessor()
        self.db = DatabaseManager()
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        title_label = ttk.Label(main_frame, text="Procesador de Facturas PDF", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(dir_frame, text="Directorio de PDFs:").grid(row=0, column=0, sticky=tk.W)
        self.dir_var = tk.StringVar()
        ttk.Entry(dir_frame, textvariable=self.dir_var, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(dir_frame, text="Examinar", command=self.browse_directory).grid(row=0, column=2)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Procesar PDFs", command=self.start_processing_thread).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Generar Estadísticas", command=self.start_stats_thread).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Exportar CSV", command=self.export_csv).grid(row=0, column=2, padx=5)
        
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="5")
        results_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.results_text = tk.Text(results_frame, height=20, width=80, state=tk.DISABLED)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        self.db.create_tables()
        self.refresh_data()
    
    def refresh_data(self):
        thread = threading.Thread(target=self._refresh_data_thread)
        thread.daemon = True
        thread.start()
        
    def _refresh_data_thread(self):
        self.df_items, self.df_invoices = self.db.get_all_data()
        if not self.df_items.empty:
            message = "Datos cargados desde la base de datos. ¡Listo para generar estadísticas!"
        else:
            message = "Base de datos vacía. Por favor, procesa algunos PDFs."
        self.root.after(0, self.update_results_display, message)

    def update_results_display(self, message):
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, message)
        self.results_text.configure(state=tk.DISABLED)
    
    def browse_directory(self):
        directory = filedialog.askdirectory(title="Seleccionar directorio con PDFs")
        if directory:
            self.dir_var.set(directory)

    def start_processing_thread(self):
        directory = self.dir_var.get()
        if not directory:
            messagebox.showerror("Error", "Por favor, selecciona un directorio.")
            return

        self.update_results_display("Iniciando procesamiento de PDFs... Por favor, espera.")
        self.progress.start()
        thread = threading.Thread(target=self.process_pdfs_in_thread, args=(directory,))
        thread.daemon = True
        thread.start()

    def process_pdfs_in_thread(self, directory):
        try:
            items, totals = self.processor.process_pdf_directory(directory)
            df_items, df_totals = self.processor.create_dataframes(items, totals)

            if not df_items.empty and not df_totals.empty:
                self.db.insert_data(df_items, df_totals)
                self.root.after(0, self.update_results_display, "Procesamiento completado. Datos guardados en la base de datos.")
                self.root.after(0, self.refresh_data)
            else:
                self.root.after(0, self.update_results_display, "No se encontraron datos válidos en los PDFs procesados.")
        
        except Exception as e:
            self.root.after(0, self.update_results_display, f"Error durante el procesamiento: {str(e)}")
        finally:
            self.root.after(0, self.progress.stop)
    
    def start_stats_thread(self):
        # ANTES DE LANZAR EL HILO, ASEGURAMOS QUE LOS DATOS EXISTEN Y LUEGO LANZAMOS EL HILO
        self.update_results_display("Verificando datos y generando estadísticas... Por favor, espera.")
        self.progress.start()
        thread = threading.Thread(target=self._check_and_generate_stats_thread)
        thread.daemon = True
        thread.start()

    def _check_and_generate_stats_thread(self):
        # Carga los datos en el hilo secundario para evitar bloqueos
        self.df_items, self.df_invoices = self.db.get_all_data()

        # Si no hay datos, muestra un error en la GUI usando after()
        if self.df_items.empty:
            self.root.after(0, lambda: messagebox.showerror("Error", "Primero procesa algunos PDFs para tener datos."))
            self.root.after(0, self.progress.stop)
            return

        # Genera estadísticas y gráficos en el hilo secundario
        try:
            # Crea una ruta segura para guardar los gráficos.
            if sys.platform == "win32":
                safe_path = os.path.join(os.environ.get('USERPROFILE'), 'Documents', 'ExpenditureControl_Stats')
            else:
                safe_path = os.path.join(os.path.expanduser('~'), 'Documents', 'ExpenditureControl_Stats')
            
            output_dir = safe_path
            os.makedirs(output_dir, exist_ok=True)
            
            stats = self.processor.generate_statistics(self.df_items, self.df_invoices)
            
            self.processor.generate_visualizations(self.df_items, self.df_invoices, output_dir)
            
            stats_text = "=== ESTADÍSTICAS ===\n\n"
            stats_text += f"Total facturas procesadas: {stats.get('total_invoices', 0)}\n"
            stats_text += f"Total artículos: {stats.get('total_items', 0)}\n"
            stats_text += f"Total gastado: {stats.get('total_spent', 0):.2f} EUR\n"
            stats_text += f"Gasto promedio por factura: {stats.get('avg_invoice_total', 0):.2f} EUR\n"
            stats_text += f"Total de IVA pagado: {stats.get('total_taxes', 0):.2f} EUR\n\n"
            
            stats_text += "Gastos mensuales:\n"
            if 'monthly_spending' in stats:
                for month, amount in stats['monthly_spending'].items():
                    stats_text += f"  {month}: {amount:.2f} EUR\n"
            
            stats_text += "\n--- Cantidad de productos comprados ---\n"
            if 'total_quantity_per_product' in stats and not stats['total_quantity_per_product'].empty:
                for product, count in stats['total_quantity_per_product'].items():
                    stats_text += f"  - {product}: {int(count)} unidades\n"
            
            stats_text += "\n--- Productos con mayor gasto ---\n"
            if 'spending_per_product' in stats and not stats['spending_per_product'].empty:
                for product, amount in stats['spending_per_product'].items():
                    stats_text += f"  - {product}: {amount:.2f} EUR\n"
            
            stats_text += "\n--- Artículo más caro por unidad ---\n"
            if 'most_expensive_item' in stats and not stats['most_expensive_item'].empty:
                item = stats['most_expensive_item']
                stats_text += f"  - Descripción: {item['Descripción']}\n"
                stats_text += f"  - Precio: {item['Precio Unitario (EUR)']:.2f} EUR\n"
                stats_text += f"  - Nº Factura: {item['Nº Factura']}\n"
            
            stats_text += f"\nGráficos guardados en: {os.path.abspath(output_dir)}\n"
            
            # Actualiza la GUI con el resultado del hilo secundario
            self.root.after(0, self.update_results_display, stats_text)
            
        except Exception as e:
            self.root.after(0, self.update_results_display, f"Error generando estadísticas: {str(e)}")
        finally:
            self.root.after(0, self.progress.stop)
    
    def export_csv(self):
        self.refresh_data()
        self.root.after(100, self._check_data_and_export_csv)

    def _check_data_and_export_csv(self):
        if self.df_items.empty:
            messagebox.showerror("Error", "No hay datos en la base de datos para exportar.")
            return
        
        output_dir = filedialog.askdirectory(title="Seleccionar directorio para guardar CSV")
        if not output_dir:
            return
        
        try:
            items_path = os.path.join(output_dir, "articulos.csv")
            invoices_path = os.path.join(output_dir, "totales.csv")
            
            self.df_items.to_csv(items_path, index=False, encoding='utf-8-sig')
            self.df_invoices.to_csv(invoices_path, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("Éxito", f"CSV exportados correctamente:\n{items_path}\n{invoices_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron exportar los CSV: {str(e)}")

def main():
    root = tk.Tk()
    app = PDFProcessorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()