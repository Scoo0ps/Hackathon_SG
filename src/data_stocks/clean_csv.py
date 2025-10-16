import pandas as pd
import os

input_folder = "../../data/per_stock"       # Dossier des CSV bruts
output_folder = "../../data/per_stock_clean"  # Nouveau dossier pour les CSV nettoyés

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.endswith(".csv"):
        ticker = filename.replace(".csv", "")
        file_path = os.path.join(input_folder, filename)
        
        # Lecture brut
        df = pd.read_csv(file_path)
        
        # Nettoyage : suppression des 2 premières lignes inutiles
        df_clean = df.drop([0, 1]).reset_index(drop=True)
        
        # Renommer la colonne Price en Date
        df_clean = df_clean.rename(columns={"Price": "Date"})
        
        # Convertir Date en datetime et mettre en index
        df_clean['Date'] = pd.to_datetime(df_clean['Date'])
        df_clean = df_clean.set_index('Date')
        
        # Convertir les colonnes numériques
        cols = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
        for col in cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Sauvegarder le CSV nettoyé
        output_path = os.path.join(output_folder, f"{ticker}.csv")
        df_clean.to_csv(output_path)
        
        print(f"✅ {ticker} nettoyé et sauvegardé dans {output_path}")

print("\nNettoyage et sauvegarde terminés !")
