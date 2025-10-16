import pandas as pd

df = pd.read_csv("data/per_stock/AAPL.csv")

# Supprime les 2 premières lignes problématiques
df_clean = df.drop([0, 1])

# Reset index pour refaire une indexation correcte
df_clean = df_clean.reset_index(drop=True)
df_clean = df_clean.rename(columns={"Price": "Date"})
print(df_clean.head())
