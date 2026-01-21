import os
from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; padding: 10px; background: #f4f4f9; }
        .box { background: white; padding: 15px; border-radius: 10px; max-width: 450px; margin: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        input { width: 100%; padding: 12px; margin: 5px 0; box-sizing: border-box; font-size: 1.1rem; border: 1px solid #ccc; border-radius: 5px; }
        button { width: 100%; padding: 15px; background: #002d5a; color: white; border: none; border-radius: 5px; font-weight: bold; font-size: 1.1rem; cursor: pointer; }
        .res { margin-top: 15px; padding: 12px; border-left: 6px solid #E30613; background: #fff; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .title { font-size: 1.2rem; font-weight: bold; color: #002d5a; margin-bottom: 10px; }
        .debug { font-size: 0.7rem; color: #999; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <form method="POST">
            <input type="text" name="ean" placeholder="Pípni EAN" value="{{ ean }}" autofocus required>
            <input type="text" name="vydani" placeholder="Číslo (např. 09)" value="{{ query_vydani }}" required>
            <button type="submit">HLEDAT</button>
        </form>

        {% if title or results %}
            <div style="margin-top: 20px;">
                <div class="title">{{ title }}</div>
                {% for r in results %}
                <div class="res">
                    <strong>Vydání: {{ r.vydani }}</strong><br>
                    NÁVOZ: <b>{{ r.navoz }}</b><br>
                    REMITENDA: <span style="color:red; font-weight:bold">{{ r.remitenda }}</span>
                </div>
                {% endfor %}
                {% if not results %}
                    <p style="color:red;">Číslo "{{ query_vydani }}" nenalezeno. Zkus zadat jen "{{ query_vydani.lstrip('0') }}".</p>
                {% endif %}
            </div>
        {% endif %}
        
        {% if debug_info %}
        <div class="debug">
            <strong>Nalezená vydání na webu:</strong> {{ debug_info }}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    results, title, ean, query_vydani, debug_info = [], "", "", "", ""
    if request.method == 'POST':
        ean = request.form.get('ean', '').strip()
        query_vydani = request.form.get('vydani', '').strip()
        
        try:
            # Mediaprint Kapa
            url = f"https://www.mediaprintkapa.cz/katalog-tisku/?search={ean}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            
            h1 = soup.find('h1')
            title = h1.text.strip() if h1 else "Titul nenalezen"
            
            all_vydani = []
            # Prohledáme všechny tabulky na stránce
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        v_text = cols[1].text.strip()
                        all_vydani.append(v_text)
                        
                        # Porovnání: zkusíme shodu čísla (např. "09" v "09/2024")
                        clean_q = query_vydani.lstrip('0')
                        if query_vydani in v_text or (clean_q and clean_q in v_text):
                            results.append({
                                "vydani": v_text,
                                "navoz": cols[2].text.strip(),
                                "remitenda": cols[5].text.strip() if len(cols) > 5 else "Nezadáno"
                            })
            debug_info = ", ".join(list(set(all_vydani)))
        except Exception as e:
            title = f"Chyba: {str(e)}"
            
    return render_template_string(HTML_TEMPLATE, results=results, title=title, ean=ean, query_vydani=query_vydani, debug_info=debug_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

