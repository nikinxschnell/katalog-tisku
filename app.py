

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
        .box { background: white; padding: 15px; border-radius: 8px; max-width: 450px; margin: auto; }
        input { width: 100%; padding: 12px; margin: 5px 0; box-sizing: border-box; font-size: 1.1rem; }
        button { width: 100%; padding: 15px; background: #E30613; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
        .res { margin-top: 15px; padding: 10px; border-left: 5px solid #002d5a; background: #f9f9f9; }
        .info { font-size: 0.8rem; color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="box">
        <h3>Čtečka Mediaprint & PNS</h3>
        <form method="POST">
            <input type="text" name="ean" placeholder="Pípni EAN" value="{{ ean }}" required>
            <input type="text" name="vydani" placeholder="Vydání (např. 09)" value="{{ query_vydani }}" required>
            <button type="submit">HLEDAT</button>
        </form>

        {% if title %}
            <h4 style="margin-bottom:5px">{{ title }}</h4>
            {% if results %}
                {% for r in results %}
                <div class="res">
                    <strong>Vydání: {{ r.vydani }}</strong><br>
                    NÁVOZ: {{ r.navoz }}<br>
                    REMITENDA: <span style="color:red; font-weight:bold">{{ r.remitenda }}</span>
                </div>
                {% endfor %}
            {% else %}
                <p style="color:red">Pro vydání "{{ query_vydani }}" nic nenalezeno.</p>
                <div class="info">Zjištěná vydání na webu: {{ debug }}</div>
            {% endif %}
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    results, title, ean, query_vydani, debug = [], "", "", "", ""
    if request.method == 'POST':
        ean = request.form.get('ean', '').strip()
        query_vydani = request.form.get('vydani', '').strip()
        
        # Simulujeme prohlížeč Chrome na Windows
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'cs-CZ,cs;q=0.9',
            'Referer': 'https://www.mediaprintkapa.cz/katalog-tisku/'
        }
        
        try:
            url = f"https://www.mediaprintkapa.cz/katalog-tisku/?search={ean}"
            session = requests.Session()
            r = session.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.content, 'html.parser')
            
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else "Titul nenalezen"
            
            table = soup.find('table', {'class': 'katalog-tisku'})
            found_v = []
            if table:
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        v_web = cols[1].text.strip()
                        found_v.append(v_web)
                        # Hledáme číslo vydání v textu (např "9" v "09/2026")
                        if query_vydani.lstrip('0') in v_web.lstrip('0'):
                            results.append({
                                "vydani": v_web,
                                "navoz": cols[2].text.strip(),
                                "remitenda": cols[5].text.strip()
                            })
            debug = ", ".join(found_v) if found_v else "Web neposlal žádná data."
        except Exception as e:
            title = f"Chyba spojení: {str(e)}"
            
    return render_template_string(HTML_TEMPLATE, results=results, title=title, ean=ean, query_vydani=query_vydani, debug=debug)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
