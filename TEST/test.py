import pdfplumber
import pandas as pd
import re

# Primero veamos qué hay realmente en el PDF
with pdfplumber.open("pdf/test_01.PDF") as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n=== PÁGINA {i+1} ===")
        
        # Extraer texto completo
        text = page.extract_text()
        print("TEXTO COMPLETO:")
        print(text)
        print("\n" + "="*50)
        
        # Extraer tablas
        tables = page.extract_tables()
        print(f"Número de tablas encontradas: {len(tables)}")
        
        for j, table in enumerate(tables):
            print(f"\n--- TABLA {j+1} ---")
            for k, row in enumerate(table):
                print(f"Fila {k}: {row}")