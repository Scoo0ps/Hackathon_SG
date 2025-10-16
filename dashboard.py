import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# ============================
# Liste des entreprises
# ============================
companies = [
    "AIR.PA", "BNP.PA", "SAN.PA", "MC.PA", "OR.PA", "DG.PA", "SU.PA", "ENGI.PA",
    "CAP.PA", "KER.PA", "AAPL", "MSFT", "GOOG", "AMZN", "META", "NVDA", "TSLA",
    "PEP", "AVGO", "ADBE"
]

# ============================
# Charger les CSV
# ============================
# Attention : les fichiers doivent être nommés par exemple :
# "AIR.PA_prices.csv" et "AIR.PA_sentiment.csv"
# avec colonnes :
# - prices CSV : "date","fluctuation" (en %)
# - sentiment CSV : "date","score" (entre -1 et 1 ou 0-1)
def load_data(company):
    df_price = pd.read_csv(f"data/{company}_prices.csv", parse_dates=["date"])
    df_sentiment = pd.read_csv(f"data/{company}_sentiment.csv", parse_dates=["date"])
    return df_price, df_sentiment

# ============================
# Créer l'app Dash
# ============================
app = dash.Dash(__name__)
app.title = "Sentiment vs Market Dashboard"

app.layout = html.Div([
    html.H1("📊 Sentiment et Fluctuation des Actions", style={"textAlign": "center"}),

    # Dropdown pour choisir l'entreprise
    html.Div([
        html.Label("Sélectionnez une entreprise :"),
        dcc.Dropdown(
            id="company-dropdown",
            options=[{"label": c, "value": c} for c in companies],
            value="AAPL",  # valeur par défaut
            clearable=False
        )
    ], style={"width": "40%", "margin": "auto"}),

    html.Br(),

    # Graphiques
    dcc.Graph(id="price-graph"),
    dcc.Graph(id="sentiment-graph")
])

# ============================
# Callback pour mettre à jour les graphiques
# ============================
@app.callback(
    [Output("price-graph", "figure"),
     Output("sentiment-graph", "figure")],
    [Input("company-dropdown", "value")]
)
def update_graphs(selected_company):
    df_price, df_sentiment = load_data(selected_company)

    # Graphique des fluctuations
    fig_price = px.line(
        df_price, x="date", y="fluctuation",
        title=f"Fluctuation journalière du prix : {selected_company}",
        labels={"fluctuation":"% fluctuation", "date":"Date"}
    )
    fig_price.update_traces(line=dict(color="#1f77b4", width=3))
    fig_price.update_layout(template="plotly_white")

    # Graphique du sentiment
    fig_sentiment = px.line(
        df_sentiment, x="date", y="score",
        title=f"Score de sentiment quotidien : {selected_company}",
        labels={"score":"Sentiment Score", "date":"Date"}
    )
    fig_sentiment.update_traces(line=dict(color="#ff7f0e", width=3))
    fig_sentiment.update_layout(template="plotly_white")

    return fig_price, fig_sentiment

# ============================
# Lancer l'app
# ============================
if __name__ == "__main__":
    app.run_server(debug=True)
