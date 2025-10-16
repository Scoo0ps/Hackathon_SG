# Hackathon_SG

https://github.com/CarolineChipieCAO/ENSIIE-Hackathon


Comment faire un environnement sans sudo :

Mathias :
python3 -m pip install --user virtualenv 

Agathe :
python3 -m pip install --user virtualenv --break-system-packages | python3 -m virtualenv ~/venv





Comment activer son environnement :

source venv/bin/activate



installer depuis le fichier de requirements:
pip install -r requirements.txt



actualiser la liste des librairies:
pip freeze > requirements.txt

