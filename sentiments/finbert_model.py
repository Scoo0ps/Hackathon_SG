### Ce fichier est destiné à charger le modèle FinBERT une seule fois.
### Il doit donc être exécuté une seule fois et importé dans sentiment_analysis.py


import tensorflow as tf
from transformers import TFBertForSequenceClassification, BertTokenizer, set_seed

# Fixer la seed pour la reproductibilité (une seule fois)
set_seed(1, True)

# Charger le modèle et le tokenizer FinBERT (une seule fois)
model_path = "ProsusAI/finbert"
tokenizer = BertTokenizer.from_pretrained(model_path)
model = TFBertForSequenceClassification.from_pretrained(model_path)
