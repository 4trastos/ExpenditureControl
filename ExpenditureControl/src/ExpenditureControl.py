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
        
        # Extraer número de factura
        for line in lines:
            if 'Nº factura' in line:
                invoice_match = re.search(r'Nº factura\s+(\S+)', line)
                if invoice_match:
                    invoice_number = invoice_match.group(1)
        
        # Extraer fecha de factura
        for line in lines:
            if 'Fecha' in line:
                date_match = re.search(r'Fecha\s+(\d{2}\.\d{2}\.\d{4})', line)
                if date_match:
                    invoice_date = datetime.strptime(date_match.group(1), '%d.%m.%Y')
                    break
        
        # Buscar la línea específica del artículo
        for line in lines:
            line = line.strip()
            
            # Buscar la línea que contiene el número de artículo largo
            if re.search(r'^\d{13,}', line):  # Busca números de 13+ dígitos al inicio
                numbers = re.findall(r'[\d,]+', line)
                description = re.sub(r'^\d{13,}.*?\d{1,2}\s+\d{1,3}\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+[\d,]+', '', line)
                description = description.strip()
                
                if len(numbers) >= 8:  # Debe tener al menos 8 valores numéricos
                    # Añadir descripción al final
                    numbers.append(description)
                    items_data.append(numbers)
            
            # Buscar totales - línea con valores separados por espacios
            if re.match(r'^\d+,\d+\s+\d+,\d+\s+\d+,\d+%*\s+\d+,\d+\s+\d+,\d+', line):
                numbers = re.findall(r'[\d,]+%*', line)
                if len(numbers) >= 5:  # Debe tener al menos 5 valores
                    totals_data.append(numbers)
        
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
                        
                        # Añadir información de la factura a cada artículo
                        for item in items:
                            item.extend([number, date])
                        
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
        # Procesar artículos
        if items_data:
            df_items = pd.DataFrame(items_data)
            
            # Asignar nombres de columnas
            column_names = [
                "Nº Artículo", "Posición", "Cantidad", "Precio Unitario (EUR)", 
                "Código Producto", "Descuento %", "IVA %", "Valor Neto (EUR)",
                "Descripción", "Nº Factura", "Fecha Factura"
            ]
            
            if df_items.shape[1] <= len(column_names):
                df_items.columns = column_names[:df_items.shape[1]]
            
            # Convertir columnas numéricas
            numeric_columns = ["Cantidad", "Precio Unitario (EUR)", "Descuento %", "IVA %", "Valor Neto (EUR)"]
            for col in numeric_columns:
                if col in df_items.columns:
                    df_items[col] = df_items[col].str.replace(',', '.').astype(float)
            
            # Convertir fecha
            if "Fecha Factura" in df_items.columns:
                df_items["Fecha Factura"] = pd.to_datetime(df_items["Fecha Factura"])
        
        # Procesar totales
        if totals_data:
            df_totals = pd.DataFrame(totals_data)
            
            # Asignar nombres de columnas
            total_columns = [
                "Portes (EUR)", "Valor Neto (EUR)", "IVA %", 
                "Importe IVA (EUR)", "Importe Total (EUR)"
            ]
            
            if df_totals.shape[1] <= len(total_columns):
                df_totals.columns = total_columns[:df_totals.shape[1]]
            
            # Convertir columnas numéricas
            numeric_total_columns = ["Portes (EUR)", "Valor Neto (EUR)", "Importe IVA (EUR)", "Importe Total (EUR)"]
            for col in numeric_total_columns:
                if col in df_totals.columns:
                    df_totals[col] = df_totals[col].str.replace(',', '.').astype(float)
            
            # Convertir IVA % (eliminar el símbolo %)
            if "IVA %" in df_totals.columns:
                df_totals["IVA %"] = df_totals["IVA %"].str.replace('%', '').str.replace(',', '.').astype(float)
        
        return df_items, df_totals
    
    def generate_statistics(self, df_items, df_totals):
        stats = {}
        
        if not df_items.empty:
            # Estadísticas básicas
            stats['total_invoices'] = len(df_items['Nº Factura'].unique())
            stats['total_items'] = len(df_items)
            stats['total_spent'] = df_items['Valor Neto (EUR)'].sum()
            stats['avg_item_price'] = df_items['Precio Unitario (EUR)'].mean()
            stats['most_expensive_item'] = df_items.loc[df_items['Precio Unitario (EUR)'].idxmax()]
            
            # Gastos por mes
            df_items['Mes'] = df_items['Fecha Factura'].dt.to_period('M')
            monthly_spending = df_items.groupby('Mes')['Valor Neto (EUR)'].sum()
            stats['monthly_spending'] = monthly_spending
            
            # Productos más comprados
            top_products = df_items['Descripción'].value_counts().head(10)
            stats['top_products'] = top_products
            
        if not df_totals.empty:
            stats['avg_invoice_total'] = df_totals['Importe Total (EUR)'].mean()
            stats['total_taxes'] = df_totals['Importe IVA (EUR)'].sum()
        
        return stats
    
    def predict_future_spending(self, df_items):
        if df_items.empty or 'Fecha Factura' not in df_items.columns:
            return None
        
        # Preparar datos para predicción
        df_items['Fecha Numerica'] = (df_items['Fecha Factura'] - df_items['Fecha Factura'].min()).dt.days
        monthly_data = df_items.groupby(df_items['Fecha Factura'].dt.to_period('M'))['Valor Neto (EUR)'].sum().reset_index()
        monthly_data['Mes'] = range(len(monthly_data))
        
        if len(monthly_data) < 3:
            return None  # No hay suficientes datos para predicción
        
        # Modelo de regresión polinomial
        X = monthly_data['Mes'].values.reshape(-1, 1)
        y = monthly_data['Valor Neto (EUR)'].values
        
        poly = PolynomialFeatures(degree=2)
        X_poly = poly.fit_transform(X)
        
        model = LinearRegression()
        model.fit(X_poly, y)
        
        # Predecir próximos 6 meses
        future_months = np.array(range(len(monthly_data), len(monthly_data) + 6)).reshape(-1, 1)
        future_months_poly = poly.transform(future_months)
        predictions = model.predict(future_months_poly)
        
        return predictions
    
    def generate_visualizations(self, df_items, df_totals, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Gráfico de gastos mensuales
        if not df_items.empty and 'Fecha Factura' in df_items.columns:
            plt.figure(figsize=(10, 6))
            df_items['Mes'] = df_items['Fecha Factura'].dt.to_period('M')
            monthly_spending = df_items.groupby('Mes')['Valor Neto (EUR)'].sum()
            
            monthly_spending.plot(kind='bar', color='skyblue')
            plt.title('Gastos Mensuales en Materiales')
            plt.xlabel('Mes')
            plt.ylabel('Euros (EUR)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'gastos_mensuales.png'))
            plt.close()
        
        # Gráfico de productos más comprados
        if not df_items.empty and 'Descripción' in df_items.columns:
            plt.figure(figsize=(12, 8))
            top_products = df_items['Descripción'].value_counts().head(10)
            
            top_products.plot(kind='barh', color='lightgreen')
            plt.title('Productos Más Comprados')
            plt.xlabel('Frecuencia')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'productos_mas_comprados.png'))
            plt.close()
        
        # Gráfico de distribución de precios
        if not df_items.empty and 'Precio Unitario (EUR)' in df_items.columns:
            plt.figure(figsize=(10, 6))
            sns.histplot(df_items['Precio Unitario (EUR)'], bins=20, kde=True, color='orange')
            plt.title('Distribución de Precios de Productos')
            plt.xlabel('Precio Unitario (EUR)')
            plt.ylabel('Frecuencia')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'distribucion_precios.png'))
            plt.close()

class PDFProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesador de Facturas PDF")
        self.root.geometry("800x600")
        
        self.processor = PDFInvoiceProcessor()
        
        self.create_widgets()
    
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="Procesador de Facturas PDF", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Selección de directorio
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(dir_frame, text="Directorio de PDFs:").grid(row=0, column=0, sticky=tk.W)
        self.dir_var = tk.StringVar()
        ttk.Entry(dir_frame, textvariable=self.dir_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(dir_frame, text="Examinar", command=self.browse_directory).grid(row=0, column=2)
        
        # Botones de acción
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Procesar PDFs", command=self.process_pdfs).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Generar Estadísticas", command=self.generate_stats).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Exportar CSV", command=self.export_csv).grid(row=0, column=2, padx=5)
        
        # Área de resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="5")
        results_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.results_text = tk.Text(results_frame, height=15, width=70)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # DataFrames para almacenar resultados
        self.df_items = pd.DataFrame()
        self.df_totals = pd.DataFrame()
        self.stats = {}
    
    def browse_directory(self):
        directory = filedialog.askdirectory(title="Seleccionar directorio con PDFs")
        if directory:
            self.dir_var.set(directory)
    
    def process_pdfs(self):
        directory = self.dir_var.get()
        if not directory:
            messagebox.showerror("Error", "Por favor, selecciona un directorio")
            return
        
        def process():
            self.progress.start()
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Procesando PDFs...\n")
            
            try:
                items, totals = self.processor.process_pdf_directory(directory)
                self.df_items, self.df_totals = self.processor.create_dataframes(items, totals)
                
                self.results_text.insert(tk.END, f"Procesamiento completado.\n")
                self.results_text.insert(tk.END, f"Artículos encontrados: {len(self.df_items)}\n")
                self.results_text.insert(tk.END, f"Facturas procesadas: {len(self.df_totals)}\n")
                
            except Exception as e:
                self.results_text.insert(tk.END, f"Error: {str(e)}\n")
            finally:
                self.progress.stop()
        
        # Ejecutar en un hilo separado para no bloquear la UI
        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()
    
    def generate_stats(self):
        if self.df_items.empty:
            messagebox.showerror("Error", "Primero procesa algunos PDFs")
            return
        
        self.stats = self.processor.generate_statistics(self.df_items, self.df_totals)
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== ESTADÍSTICAS ===\n\n")
        self.results_text.insert(tk.END, f"Total facturas procesadas: {self.stats.get('total_invoices', 0)}\n")
        self.results_text.insert(tk.END, f"Total artículos: {self.stats.get('total_items', 0)}\n")
        self.results_text.insert(tk.END, f"Total gastado: {self.stats.get('total_spent', 0):.2f} EUR\n")
        self.results_text.insert(tk.END, f"Gasto promedio por factura: {self.stats.get('avg_invoice_total', 0):.2f} EUR\n\n")
        
        self.results_text.insert(tk.END, "Gastos mensuales:\n")
        if 'monthly_spending' in self.stats:
            for month, amount in self.stats['monthly_spending'].items():
                self.results_text.insert(tk.END, f"  {month}: {amount:.2f} EUR\n")
        
        # Generar visualizaciones
        output_dir = os.path.join(os.path.dirname(self.dir_var.get()), "estadisticas")
        self.processor.generate_visualizations(self.df_items, self.df_totals, output_dir)
        self.results_text.insert(tk.END, f"\nGrágicos guardados en: {output_dir}\n")
    
    def export_csv(self):
        if self.df_items.empty:
            messagebox.showerror("Error", "No hay datos para exportar")
            return
        
        output_dir = filedialog.askdirectory(title="Seleccionar directorio para guardar CSV")
        if not output_dir:
            return
        
        try:
            items_path = os.path.join(output_dir, "articulos.csv")
            totals_path = os.path.join(output_dir, "totales.csv")
            
            self.df_items.to_csv(items_path, index=False, encoding='utf-8-sig')
            self.df_totals.to_csv(totals_path, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("Éxito", f"CSV exportados correctamente:\n{items_path}\n{totals_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron exportar los CSV: {str(e)}")

def main():
    # Para ejecutar la aplicación con interfaz gráfica
    root = tk.Tk()
    app = PDFProcessorApp(root)
    root.mainloop()

if __name__ == "__main__":
    # Si se ejecuta sin interfaz gráfica, procesar PDFs en el directorio actual
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--cli":
        processor = PDFInvoiceProcessor()
        items, totals = processor.process_pdf_directory(".")
        df_items, df_totals = processor.create_dataframes(items, totals)
        
        if not df_items.empty:
            df_items.to_csv("articulos.csv", index=False, encoding='utf-8-sig')
            print("✅ articulos.csv generado")
        
        if not df_totals.empty:
            df_totals.to_csv("totales.csv", index=False, encoding='utf-8-sig')
            print("✅ totales.csv generado")
        
        stats = processor.generate_statistics(df_items, df_totals)
        print(f"\n=== ESTADÍSTICAS ===")
        print(f"Facturas procesadas: {stats.get('total_invoices', 0)}")
        print(f"Artículos: {stats.get('total_items', 0)}")
        print(f"Total gastado: {stats.get('total_spent', 0):.2f} EUR")
        
        # Generar visualizaciones
        processor.generate_visualizations(df_items, df_totals, "estadisticas")
        print("Gráficos generados en la carpeta 'estadisticas'")
    else:
        # Ejecutar interfaz gráfica
        main()