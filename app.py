
import os
from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; padding: 10px; background: #f0f0f0; }
        .box { background: white; padding: 15px; border-radius: 8px; max-width: 400px; margin: auto; }
        input { width: 100%; padding: 12px; margin: 5px 0; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #002d5a; color: white; border: none; border-radius: 5px; width: 100%; font-weight: bold; }
        .res { margin-top: 15px; padding: 10px; border-left: 5px solid #E30613; background: #fff; border-radius: 4px; }
        .all { font-size: 0.8rem; color: #666; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <form method="POST">
            <input type="number" name="ean" placeholder="Pípni EAN" autofocus required>
            <input type="text" name="vydani" placeholder="Číslo (např. 02)" required>
            <button type="submit">HLEDAT</button>
        </form>

        {% if title %}
            <h3 style="margin-bottom:5px">{{ title }}</h3>
            {% if results %}
                {% for r in results %}
                <div class="res">
                    <strong>Vydání: {{ r.vydani }}</strong><br>
                    NÁVOZ: {{ r.navoz }}<br>
                    REMITENDA: <span style="color:red; font-weight:bold">{{ r.remitenda }}</span>
                </div>
                {% endfor %}
            {% else %}
                <p style="color:red">Číslo "{{ query_vydani }}" nenalezeno v aktuálním seznamu.</p>
                <div class="all">
                    <strong>Dostupná čísla v katalogu:</strong><br>
                    {{ available_list }}
                </div>
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
    available_list = ""
    
    if request.method == 'POST':
        ean = request.form.get('ean').strip()
        query_vydani = request.form.get('vydani').strip()
        try:
            url = f"https://www.mediaprintkapa.cz/katalog-tisku/?search={ean}"
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else "Titul nenalezen"
            
            table = soup.find('table', {'class': 'katalog-tisku'})
            if table:
                rows = table.find_all('tr')[1:]
                found_vydani = []
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        v_web = cols[1].text.strip()
                        found_vydani.append(v_web)
                        # Pokud se zadané číslo (třeba 02) nachází v textu na webu (třeba 02/2026)
                        if query_vydani in v_web:
                            results.append({
                                "vydani": v_web,
                                "navoz": cols[2].text.strip(),
                                "remitenda": cols[5].text.strip()
                            })
                available_list = ", ".join(found_vydani)
        except Exception as e:
            title = f"Chyba: {str(e)}"
            
    return render_template_string(HTML_TEMPLATE, results=results, title=title, query_vydani=query_vydani, available_list=available_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
