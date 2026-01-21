

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
        body { font-family: sans-serif; padding: 10px; background: #f0f0f0; margin: 0; }
        .box { background: white; padding: 15px; border-radius: 8px; max-width: 450px; margin: 10px auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        input { width: 100%; padding: 15px; margin: 5px 0; box-sizing: border-box; font-size: 1.1rem; border: 1px solid #ccc; border-radius: 5px; }
        button { width: 100%; padding: 15px; background: #002d5a; color: white; border: none; border-radius: 5px; font-weight: bold; font-size: 1.1rem; cursor: pointer; }
        .res { margin-top: 15px; padding: 12px; border-left: 6px solid #E30613; background: #f9f9f9; border-radius: 4px; box-shadow: inset 0 0 5px rgba(0,0,0,0.05); }
        .source { font-size: 0.7rem; color: #999; text-transform: uppercase; margin-bottom: 5px; }
        .title { font-size: 1.2rem; font-weight: bold; color: #002d5a; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <form method="POST">
            <input type="number" name="ean" placeholder="Pípni EAN" value="{{ request.form.get('ean', '') }}" autofocus required>
            <input type="text" name="vydani" placeholder="Číslo (např. 02 nebo 9)" value="{{ request.form.get('vydani', '') }}" required>
            <button type="submit">HLEDAT TERMÍNY</button>
        </form>

        {% if title or results %}
            <div style="margin-top: 20px;">
                <div class="title">{{ title if title else "Výsledky hledání" }}</div>
                
                {% if results %}
                    {% for r in results %}
                    <div class="res">
                        <div class="source">Zdroj: {{ r.source }}</div>
                        <strong>Vydání: {{ r.vydani }}</strong><br>
                        PŘIŠLO: <b>{{ r.navoz }}</b><br>
                        REMITENDA: <span style="color:red; font-weight:bold">{{ r.remitenda }}</span>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="color:red;">Pro číslo "{{ query_vydani }}" nebyly nalezeny žádné konkrétní termíny. Zkontroluj, zda je titul v aktuální nabídce.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

def get_data(ean, query_vydani):
    results = []
    found_title = ""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    # --- MEDIAPRINT KAPA ---
    try:
        mpk_url = f"https://www.mediaprintkapa.cz/katalog-tisku/?search={ean}"
        r = requests.get(mpk_url, headers=headers, timeout=8)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        if not found_title:
            h1 = soup.find('h1')
            if h1: found_title = h1.text.strip()

        table = soup.find('table', {'class': 'katalog-tisku'})
        if table:
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 6:
                    v_text = cols[1].text.strip()
                    if query_vydani.lower() in v_text.lower() or query_vydani.lstrip('0') in v_text:
                        results.append({
                            "source": "Mediaprint",
                            "vydani": v_text,
                            "navoz": cols[2].text.strip(),
                            "remitenda": cols[5].text.strip()
                        })
    except: pass

    # --- PNS ---
    try:
        pns_url = f"https://www.pns.cz/katalog-tisku?query={ean}"
        r = requests.get(pns_url, headers=headers, timeout=8)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # PNS má tituly v kartách/seznamu
        items = soup.select('.catalog-item') # Toto se může lišit dle struktury PNS
        for item in items:
            # PNS vyžaduje komplexnější scrapování, přidáme základní detekci názvu
            if not found_title:
                t = item.select_one('.catalog-item__title')
                if t: found_title = t.text.strip()
    except: pass

    return found_title, results

@app.route('/', methods=['GET', 'POST'])
def index():
    title, results, query_vydani = "", [], ""
    if request.method == 'POST':
        ean = request.form.get('ean', '').strip()
        query_vydani = request.form.get('vydani', '').strip()
        title, results = get_data(ean, query_vydani)
            
    return render_template_string(HTML_TEMPLATE, title=title, results=results, query_vydani=query_vydani)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
