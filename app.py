import os
from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zebra Ctecka</title>
    <style>
        body { font-family: sans-serif; margin: 0; padding: 10px; background: #f4f4f9; }
        .container { max-width: 400px; margin: auto; }
        .card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        input { width: 100%; padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 1.2rem; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #002d5a; color: white; border: none; border-radius: 5px; font-size: 1.1rem; font-weight: bold; cursor: pointer; }
        .result-item { background: #eef2f7; padding: 10px; border-radius: 5px; margin-top: 10px; border-left: 5px solid #002d5a; }
        .date-box { display: flex; justify-content: space-between; margin-top: 5px; }
        .date-label { font-size: 0.8rem; color: #666; }
        .date-val { font-weight: bold; font-size: 1rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2 style="margin-top:0">Pípni titul</h2>
            <form method="POST">
                <input type="number" name="ean" placeholder="EAN (pípni)" autofocus required>
                <input type="text" name="vydani" placeholder="Vydání (např. 02)" required>
                <button type="submit">HLEDAT</button>
            </form>
        </div>

        {% if title %}
        <div style="margin-top: 20px;">
            <strong style="font-size: 1.2rem;">{{ title }}</strong>
            {% if results %}
                {% for r in results %}
                <div class="result-item">
                    <div>Vydání: <strong>{{ r.vydani }}</strong></div>
                    <div class="date-box">
                        <div><div class="date-label">NÁVOZ</div><div class="date-val">{{ r.navoz }}</div></div>
                        <div><div class="date-label">REMITENDA</div><div class="date-val" style="color: #d9534f;">{{ r.remitenda }}</div></div>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <p>Pro vydání {{ query_vydani }} nebyl nalezen žádný termín.</p>
            {% endif %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    title = ""
    query_vydani = ""
    
    if request.method == 'POST':
        ean = request.form.get('ean')
        query_vydani = request.form.get('vydani')
        
        try:
            # Hledání v katalogu Mediaprint Kapa
            url = f"https://www.mediaprintkapa.cz/katalog-tisku/?search={ean}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Najdeme název
            h1 = soup.find('h1')
            title = h1.text.strip() if h1 else "Titul nenalezen"
            
            # Projdeme tabulku a hledáme všechny shody s číslem vydání
            table = soup.find('table', {'class': 'katalog-tisku'})
            if table:
                rows = table.find_all('tr')[1:] # Přeskočíme hlavičku
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        vydani_text = cols[1].text.strip()
                        # Kontrola, zda se v textu vydání vyskytuje naše číslo (např. "02/2026")
                        if query_vydani in vydani_text:
                            results.append({
                                "vydani": vydani_text,
                                "navoz": cols[2].text.strip(),
                                "remitenda": cols[5].text.strip()
                            })
        except Exception as e:
            title = f"Chyba: {str(e)}"

    return render_template_string(HTML_TEMPLATE, results=results, title=title, query_vydani=query_vydani)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
