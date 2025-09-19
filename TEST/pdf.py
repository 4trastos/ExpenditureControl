import pdfplumber
import pandas as pd
import re
import os

def extract_data_from_text(text):
    items_data = []
    totals_data = []
    
    lines = text.split('\n')
    
    # Buscar la línea específica del artículo
    for line in lines:
        line = line.strip()
        
        # Buscar la línea que contiene el número de artículo largo
        if re.search(r'^\d{13,}', line):  # Busca números de 13+ dígitos al inicio
            numbers = re.findall(r'[\d,]+', line)
            if len(numbers) >= 8:  # Debe tener al menos 8 valores numéricos
                items_data.append(numbers)
        
        # Buscar totales - línea con valores separados por espacios
        if re.match(r'^\d+,\d+\s+\d+,\d+\s+\d+,\d+%*\s+\d+,\d+\s+\d+,\d+', line):
            numbers = re.findall(r'[\d,]+%*', line)
            if len(numbers) >= 5:  # Debe tener al menos 5 valores
                totals_data.append(numbers)
    
    return items_data, totals_data

# Procesar el PDF
items_data = []
totals_data = []

with pdfplumber.open("pdf/test_01.PDF") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        page_items, page_totals = extract_data_from_text(text)
        items_data.extend(page_items)
        totals_data.extend(page_totals)

# Crear DataFrame para artículos
if items_data:
    df_items = pd.DataFrame(items_data)
    
    # Asignar nombres de columnas en español
    column_names = [
        "Nº Artículo", "Posición", "Cantidad", "Precio Unitario (EUR)", 
        "Código Producto", "Descuento %", "IVA %", "Valor Neto (EUR)"
    ]
    
    if df_items.shape[1] <= len(column_names):
        df_items.columns = column_names[:df_items.shape[1]]
    
    # Convertir columnas numéricas
    numeric_columns = ["Cantidad", "Precio Unitario (EUR)", "Descuento %", "IVA %", "Valor Neto (EUR)"]
    for col in numeric_columns:
        if col in df_items.columns:
            df_items[col] = df_items[col].str.replace(',', '.').astype(float)
    
    # Guardar CSV
    df_items.to_csv("articulos.csv", index=False, encoding="utf-8-sig")
    print("✅ articulos.csv generado correctamente")
    print(f"Artículos procesados: {len(df_items)}")
    
    # Mostrar resumen
    print("\n📊 RESUMEN DE ARTÍCULOS:")
    print(df_items.to_string(index=False))

# Crear DataFrame para totales
if totals_data:
    df_totals = pd.DataFrame(totals_data)
    
    # Asignar nombres de columnas en español
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
    
    # Guardar CSV
    df_totals.to_csv("totales.csv", index=False, encoding="utf-8-sig")
    print("✅ totales.csv generado correctamente")
    
    # Mostrar resumen
    print("\n💰 RESUMEN DE TOTALES:")
    print(df_totals.to_string(index=False))

# Eliminar archivo residual si existe
if os.path.exists("resultado.csv"):
    os.remove("resultado.csv")
    print("🗑️ Archivo residual 'resultado.csv' eliminado")

print("\n🎉 Procesamiento completado exitosamente!")
print(f"📁 Archivos guardados en: {os.getcwd()}")