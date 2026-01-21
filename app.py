
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
    <style>
        body { font-family: sans-serif; margin: 0; padding: 10px; background: #f4f4f9; }
        .card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); max-width: 400px; margin: auto; }
        input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 1.1rem; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #E30613; color: white; border: none; border-radius: 5px; font-size: 1.1rem; font-weight: bold; }
        .result-item { background: #fff; padding: 12px; border-radius: 8px; margin-top: 10px; border-left: 6px solid #E30613; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .date-val { font-weight: bold; color: #333; }
        .error { color: red; font-weight: bold; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="margin:0 0 10px 0; color:#002d5a">Čtečka Tisku</h2>
        <form method="POST">
            <input type="number" name="ean" placeholder="Pípni EAN" autofocus required>
            <input type="text" name="vydani" placeholder="Číslo (např. 02)" required>
            <button type="submit">VYHLEDAT</button>
        </form>

        {% if title %}
            <hr>
            <div style="font-weight:bold; font-size: 1.2rem; margin-bottom:10px;">{{ title }}</div>
            {% if results %}
                {% for r in results %}
                <div class="result-item">
                    <div>Vydání: <strong>{{ r.vydani }}</strong></div>
                    <div style="margin-top:5px">PŘIŠLO: <span class="date-val">{{ r.navoz }}</span></div>
                    <div>VRACÍ SE: <span class="date-val" style="color:red">{{ r.remitenda }}</span></div>
                </div>
                {% endfor %}
            {% else %}
                <div class="error">Pro číslo "{{ query_vydani }}" nic nenalezeno.</div>
                <p style="font-size:0.8rem">Zkus zadat jen jednu číslici nebo zkontroluj EAN.</p>
            {% endif %}
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
        ean = request.form.get('ean').strip()
        query_vydani = request.form.get('vydani').strip()
        try:
            # Hledání v katalogu MPK
            url = f"https://www.mediaprintkapa.cz/katalog-tisku/?search={ean}"
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else "Titul nenalezen"
            
            table = soup.find('table', {'class': 'katalog-tisku'})
            if table:
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        vydani_web = cols[1].text.strip()
                        # Hledáme, zda se naše číslo vydání nachází v textu z webu
                        if query_vydani in vydani_web:
                            results.append({
                                "vydani": vydani_web,
                                "navoz": cols[2].text.strip(),
                                "remitenda": cols[5].text.strip()
                            })
        except Exception as e:
            title = f"Chyba: {str(e)}"
    return render_template_string(HTML_TEMPLATE, results=results, title=title, query_vydani=query_vydani)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
