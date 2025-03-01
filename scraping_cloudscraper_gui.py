import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import logging
import os
import json
from flask import Flask, render_template, request, jsonify, send_file
import threading
import re
from urllib.parse import urlparse, parse_qs

# Configurações Globais
LOG_FILE = "scraping_log.txt"
STATE_FILE = "scraping_state.json"
BASE_PREFIX = "busca_multioperador_"
PAUSA_A_CADA = 2000
LEADS_POR_PAGINA = 20

# Configuração de Logging para arquivo e console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),
        logging.StreamHandler()
    ]
)

# Variáveis globais para controle
app = Flask(__name__)
pausado = False
parar = False
status = {
    "leads": 0,
    "pagina": 1,
    "bloco": 1,
    "mensagem": "Insira uma URL válida para começar",
    "progresso": 0.0,
    "arquivo": "",
    "url": "",
    "termo": "",
    "total_leads": 0,
    "total_paginas": 0,
    "total_blocos": 0,
    "iniciado": False
}

# Função para extrair o termo da URL
def extrair_termo_da_url(url):
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        termo = query_params.get('q', [''])[0]
        logging.debug(f"Termo extraído da URL {url}: {termo}")
        return termo if termo else "desconhecido"
    except Exception as e:
        logging.error(f"Erro ao extrair termo da URL {url}: {e}")
        return "desconhecido"

# Função para carregar o estado anterior
def carregar_estado():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        logging.info(f"Estado carregado: página {state['pagina_atual']}, {len(state['dados'])} leads, bloco {state['bloco_atual']}, URL: {state['url']}")
        return state["pagina_atual"], state["dados"], state["bloco_atual"], state["url"], state["total_leads"], state["total_paginas"]
    logging.debug("Nenhum estado anterior encontrado, iniciando do zero.")
    return 1, [], 1, status["url"], status["total_leads"], status["total_paginas"]

# Função para salvar o estado
def salvar_estado(pagina_atual, dados, bloco_atual, url, total_leads, total_paginas):
    state = {
        "pagina_atual": pagina_atual,
        "dados": dados,
        "bloco_atual": bloco_atual,
        "url": url,
        "total_leads": total_leads,
        "total_paginas": total_paginas
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)
    logging.info(f"Estado salvo: página {pagina_atual}, {len(dados)} leads, bloco {bloco_atual}, URL: {url}")

# Função para determinar total_paginas e total_leads a partir da URL
def obter_totais_da_url(url):
    try:
        scraper = cloudscraper.create_scraper()
        logging.debug(f"Iniciando requisição para obter totais: {url}&page=1")
        response = scraper.get(f"{url}&page=1")
        if response.status_code != 200:
            logging.warning(f"Resposta inválida para {url}: Status {response.status_code}")
            return 0, 0
        soup = BeautifulSoup(response.text, 'html.parser')
        total_text = soup.find("p", class_=lambda x: x and "subtitle" in x)
        if total_text:
            logging.info(f"Texto encontrado na página inicial: {total_text.text}")
            match = re.search(r"Encontrado[s]?\s+(\d+[\d,\.]*)", total_text.text, re.IGNORECASE)
            if match:
                total_leads = int(match.group(1).replace(".", "").replace(",", ""))
                total_paginas = (total_leads + LEADS_POR_PAGINA - 1) // LEADS_POR_PAGINA
                logging.info(f"Total leads extraído: {total_leads}, Total páginas calculado: {total_paginas}")
                return total_leads, total_paginas
            else:
                logging.warning(f"Número de leads não encontrado no texto: {total_text.text}")
        else:
            logging.warning(f"Elemento 'subtitle' não encontrado na página: {url}")
        return 0, 0
    except Exception as e:
        logging.error(f"Erro ao obter totais da URL {url}: {e}")
        return 0, 0

# Função para extrair dados da página detalhada
def extrair_dados_detalhados(scraper, url):
    try:
        logging.debug(f"Tentando extrair dados da página detalhada: {url}")
        response = scraper.get(url)
        if response.status_code != 200:
            logging.error(f"Falha ao acessar {url}: Status {response.status_code}")
            return {"Nome da Empresa": "N/A", "Nome dos Sócios": "N/A", "Telefone Comercial": "N/A", "Situação Cadastral": "N/A"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        dados = {
            "Nome da Empresa": "N/A",
            "Nome dos Sócios": "N/A",
            "Telefone Comercial": "N/A",
            "Situação Cadastral": "N/A"
        }
        
        razao_social = soup.select_one("label:contains('Razão Social') + p")
        if razao_social:
            dados["Nome da Empresa"] = razao_social.text.strip()
        
        telefones = soup.select("label:contains('Telefone') + p a[href^='tel:']")
        if telefones:
            dados["Telefone Comercial"] = "; ".join([tel.text.strip() for tel in telefones])
        else:
            tel_p = soup.select_one("label:contains('Telefone') + p")
            if tel_p:
                dados["Telefone Comercial"] = tel_p.text.strip()

        socios_label = soup.find("label", string=lambda text: text and "Sócios:" in text)
        if socios_label:
            socios_div = socios_label.find_parent("div")
            if socios_div:
                socios = socios_div.find_all("p", class_="has-text-weight-bold")
                if socios:
                    dados["Nome dos Sócios"] = "; ".join([socio.text.strip() for socio in socios])
                else:
                    logging.warning(f"Nenhum sócio encontrado em {url} dentro do div 'Sócios:'.")
            else:
                logging.warning(f"Div dos sócios não encontrado em {url}.")
        else:
            logging.warning(f"Seção 'Sócios:' não encontrada em {url}.")

        situacao = soup.select_one("label:contains('Situação Cadastral') + p")
        if situacao:
            dados["Situação Cadastral"] = situacao.text.strip()

        logging.info(f"Lead extraído de {url}: {dados}")
        return dados
    except Exception as e:
        logging.error(f"Erro ao extrair dados de {url}: {e}")
        return {"Nome da Empresa": "N/A", "Nome dos Sócios": "N/A", "Telefone Comercial": "N/A", "Situação Cadastral": "N/A"}

# Função para salvar em Excel com sufixo de bloco
def salvar_excel(dados, bloco_atual):
    arquivo = f"{BASE_PREFIX}_atualizado_bloco{bloco_atual}.xlsx"
    try:
        df = pd.DataFrame(dados, columns=["Nome da Empresa", "Nome dos Sócios", "Telefone Comercial", "Situação Cadastral"])
        df.to_excel(arquivo, index=False)
        logging.info(f"Arquivo Excel salvo: {arquivo} com {len(df)} registros")
        print(f"Salvo {len(df)} registros em {arquivo}")
        return arquivo
    except Exception as e:
        logging.error(f"Erro ao salvar no Excel (bloco {bloco_atual}): {e}")
        print(f"Erro ao salvar no Excel (bloco {bloco_atual}): {e}")
        return None

# Função principal de scraping (roda em thread separada)
def scrap_casa_dos_dados():
    global pausado, parar, status
    scraper = cloudscraper.create_scraper()
    pagina_atual, dados, bloco_atual, url_atual, total_leads, total_paginas = carregar_estado()
    
    # Garantir que a URL atual seja a do status global
    if not url_atual and status["url"]:
        url_atual = status["url"]
        total_leads = status["total_leads"]
        total_paginas = status["total_paginas"]
        logging.debug(f"URL carregada do status global: {url_atual}")

    if not url_atual:
        logging.warning("Nenhuma URL carregada para iniciar o scraping.")
        status["mensagem"] = "Erro: Nenhuma URL carregada"
        return

    status["pagina"] = pagina_atual
    status["leads"] = len(dados)
    status["bloco"] = bloco_atual
    status["url"] = url_atual
    status["total_leads"] = total_leads
    status["total_paginas"] = total_paginas
    status["total_blocos"] = (total_leads + PAUSA_A_CADA - 1) // PAUSA_A_CADA
    status["progresso"] = (len(dados) / total_leads) * 100 if total_leads > 0 else 0
    status["mensagem"] = f"Iniciando extração do termo: {status['termo']} na Casa dos Dados..."
    logging.info(f"Iniciando scraping com: página {pagina_atual}, leads {len(dados)}, total_leads {total_leads}, total_paginas {total_paginas}")

    while status["pagina"] <= total_paginas and not parar:
        try:
            if pausado:
                status["mensagem"] = "PAUSADO"
                logging.debug(f"Scraping pausado na página {status['pagina']}")
                time.sleep(1)
                continue
            
            status["mensagem"] = f"Extraindo termo: {status['termo']} na Casa dos Dados..."
            logging.debug(f"Processando página {status['pagina']} de {total_paginas}")
            print(f"Processando página {status['pagina']}...")
            url = f"{status['url']}&page={status['pagina']}"
            response = scraper.get(url)
            if response.status_code != 200:
                logging.error(f"Falha ao acessar página {status['pagina']}: Status {response.status_code}")
                print(f"Falha ao acessar página {status['pagina']}: Status {response.status_code}")
                break
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [a['href'] for a in soup.select("div.box article.media a[href*='/solucao/cnpj/']")]
            logging.debug(f"Encontrados {len(links)} links na página {status['pagina']}")
            if not links:
                logging.warning(f"Nenhum link encontrado na página {status['pagina']}. Finalizando.")
                print(f"Nenhum link encontrado na página {status['pagina']}. Finalizando.")
                break

            for link in links:
                if pausado or parar:
                    break
                full_link = "https://casadosdados.com.br" + link if link.startswith("/") else link
                dado = extrair_dados_detalhados(scraper, full_link)
                if dado not in dados:
                    dados.append(dado)
                status["leads"] = len(dados)
                status["progresso"] = (len(dados) / total_leads) * 100 if total_leads > 0 else 0
                logging.debug(f"Lead adicionado, total atual: {status['leads']}, progresso: {status['progresso']}%")
                time.sleep(random.uniform(1, 3))

            logging.info(f"Extraídos {len(dados)} leads até a página {status['pagina']}.")
            print(f"Extraídos {len(dados)} leads até a página {status['pagina']}.")
            status["mensagem"] = f"Extraindo termo: {status['termo']} na Casa dos Dados... ({status['leads']}/{status['total_leads']} leads)"

            if len(dados) >= PAUSA_A_CADA and len(dados) % PAUSA_A_CADA == 0:
                arquivo = salvar_excel(dados, status["bloco"])
                salvar_estado(status["pagina"] + 1, dados, status["bloco"] + 1, status["url"], total_leads, total_paginas)
                status["arquivo"] = arquivo
                status["mensagem"] = "PAUSADO"
                pausado = True
                status["bloco"] += 1
                status["iniciado"] = True
                logging.info(f"Bloco {status['bloco'] - 1} concluído, pausado automaticamente.")

            status["pagina"] += 1

        except Exception as e:
            logging.error(f"Erro ao processar página {status['pagina']}: {e}")
            print(f"Erro ao processar página {status['pagina']}: {e}")
            salvar_excel(dados, status["bloco"])
            salvar_estado(status["pagina"], dados, status["bloco"], status["url"], total_leads, total_paginas)
            status["mensagem"] = "Erro durante extração"
            break

    if not parar:
        arquivo = salvar_excel(dados, status["bloco"])
        salvar_estado(status["pagina"], dados, status["bloco"], status["url"], total_leads, total_paginas)
        status["mensagem"] = f"Extração concluída para termo: {status['termo']}."
        status["arquivo"] = arquivo
        os.remove(STATE_FILE)
        logging.info("Scraping concluído com sucesso.")
    else:
        arquivo = salvar_excel(dados, status["bloco"])
        salvar_estado(status["pagina"], dados, status["bloco"], status["url"], total_leads, total_paginas)
        status["mensagem"] = "PARADO"
        status["arquivo"] = arquivo
        logging.info("Scraping parado manualmente.")

# Rotas Flask
@app.route('/')
def index():
    logging.debug("Renderizando página inicial")
    return render_template('index.html', status=status)

@app.route('/start', methods=['POST'])
def start():
    global pausado, parar, status
    pausado = False
    parar = False
    status["iniciado"] = True
    status["mensagem"] = f"Iniciando extração do termo: {status['termo']} na Casa dos Dados..."
    logging.debug("Botão 'Iniciar' clicado, iniciando thread de scraping")
    if not hasattr(app, 'thread') or not app.thread.is_alive():
        app.thread = threading.Thread(target=scrap_casa_dos_dados)
        app.thread.start()
    return '', 204

@app.route('/pause', methods=['POST'])
def pause():
    global pausado
    pausado = True
    status["mensagem"] = "PAUSADO"
    logging.debug("Botão 'Pausar' clicado")
    return '', 204

@app.route('/stop', methods=['POST'])
def stop():
    global parar
    parar = True
    status["mensagem"] = "PARADO"
    logging.debug("Botão 'Parar' clicado")
    return '', 204

@app.route('/set_url', methods=['POST'])
def set_url():
    global status
    url = request.form.get('url', '').strip()
    logging.debug(f"URL recebida no backend: {url}")
    if "casadosdados.com.br" in url.lower():
        total_leads, total_paginas = obter_totais_da_url(url)
        termo = extrair_termo_da_url(url)
        status["termo"] = termo
        if total_leads > 0:  # Aceita a URL se os totais forem válidos
            status["url"] = url
            status["total_leads"] = total_leads
            status["total_paginas"] = total_paginas
            status["total_blocos"] = (total_leads + PAUSA_A_CADA - 1) // PAUSA_A_CADA
            status["mensagem"] = f"Você está pesquisando por termo: {termo} na Casa dos Dados. Pronto para iniciar."
            status["leads"] = 0
            status["pagina"] = 1
            status["bloco"] = 1
            status["progresso"] = 0.0
            status["arquivo"] = ""
            status["iniciado"] = False
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
            logging.info(f"URL válida processada: {url}, Total leads: {total_leads}, Total páginas: {total_paginas}")
            return jsonify({"success": True, "message": "URL válida"})
        else:
            # Se não encontrar totais, aceita a URL com valores padrão e tenta scraping
            status["url"] = url
            status["total_leads"] = 1000  # Valor padrão para começar
            status["total_paginas"] = 50  # Valor padrão para começar
            status["total_blocos"] = (1000 + PAUSA_A_CADA - 1) // PAUSA_A_CADA
            status["mensagem"] = f"Você está pesquisando por termo: {termo} na Casa dos Dados. Pronto para iniciar."
            status["leads"] = 0
            status["pagina"] = 1
            status["bloco"] = 1
            status["progresso"] = 0.0
            status["arquivo"] = ""
            status["iniciado"] = False
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
            logging.info(f"URL aceita com totais padrão: {url}, Total leads: 1000, Total páginas: 50")
            return jsonify({"success": True, "message": "URL aceita com totais estimados"})
    status["mensagem"] = "URL inválida. Use Casa dos Dados ou similar."
    logging.warning(f"URL inválida fornecida: {url}")
    return jsonify({"success": False, "message": "URL inválida"})

@app.route('/reset', methods=['POST'])
def reset():
    global status, pausado, parar
    pausado = False
    parar = True
    status = {
        "leads": 0,
        "pagina": 1,
        "bloco": 1,
        "mensagem": "Insira uma URL válida para começar",
        "progresso": 0.0,
        "arquivo": "",
        "url": "",
        "termo": "",
        "total_leads": 0,
        "total_paginas": 0,
        "total_blocos": 0,
        "iniciado": False
    }
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    logging.debug("Botão 'Voltar' clicado, estado resetado")
    return '', 204

@app.route('/download', methods=['GET'])
def download():
    arquivo = status["arquivo"]
    if arquivo and os.path.exists(arquivo):
        logging.debug(f"Download solicitado para {arquivo}")
        return send_file(arquivo, as_attachment=True)
    logging.warning("Tentativa de download sem arquivo disponível")
    return jsonify({"error": "Nenhum arquivo disponível"}), 404

# Sistema principal
def sistema_autonomo():
    logging.debug("Iniciando servidor Flask em http://127.0.0.1:5000")
    app.run(debug=False, host='127.0.0.1', port=5000)

if __name__ == "__main__":
    sistema_autonomo()