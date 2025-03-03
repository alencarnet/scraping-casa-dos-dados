SCRAPPING CASA DE DADOS COM PLANILHA E FRONT END
---

### Criando o `README.md`

#### Conteúdo do `README.md`
Salve este texto em `C:\Users\user\Desktop\tete\README.md`:

```markdown
# Scraping Multioperador da Casa dos Dados

Este é um projeto em Python que realiza scraping dinâmico e automatizado de dados da plataforma **Casa dos Dados** (https://casadosdados.com.br/). Ele extrai informações detalhadas de empresas (como nome, sócios, telefone e situação cadastral) a partir de uma URL fornecida, salvando os resultados em arquivos Excel de forma organizada.

## Funcionalidades
- **Interface Web Simples**: Uma interface gráfica acessível pelo navegador para inserir URLs e controlar o scraping.
- **Extração Dinâmica**: Lê automaticamente o número total de leads e páginas da URL fornecida.
- **Scraping Automatizado**: Extrai dados detalhados de cada lead (nome da empresa, sócios, telefone comercial, situação cadastral).
- **Indicadores em Tempo Real**: Mostra o progresso (barra de progresso), leads extraídos, páginas processadas e blocos gerados.
- **Controle Interativo**: Botões para "Iniciar", "Pausar", "Parar", "Voltar" e "Clique e baixe" para gerenciar o processo e baixar os resultados.
- **Saída em Excel**: Gera arquivos Excel por blocos (2000 leads por arquivo) com os dados coletados.

## Requisitos
Para executar o projeto, você precisa de:
- **Python 3.6+**: Certifique-se de ter o Python instalado (https://www.python.org/downloads/).
- **Dependências Python**:
  ```
  cloudscraper
  requests
  beautifulsoup4
  pandas
  flask
  ```
- **Sistema Operacional**: Testado no Windows (funciona em Linux/Mac com ajustes mínimos).

## Instalação
Siga estes passos para configurar o projeto localmente:

1. **Clone o Repositório**:
   Abra o terminal e execute:
   ```
   git clone https://github.com/alencarnet/scraping-casa-dos-dados.git
   cd scraping-casa-dos-dados
   ```

2. **Instale as Dependências**:
   Certifique-se de ter o `pip` instalado e execute:
   ```
   pip install -r requirements.txt
   ```
   Isso instalará todas as bibliotecas necessárias listadas no `requirements.txt`.

3. **Verifique os Arquivos**:
   Após clonar, você verá:
   - `scraping_cloudscraper_gui.py`: O script principal.
   - `templates/index.html`: O arquivo HTML da interface web.
   - `requirements.txt`: Lista de dependências.

## Como Usar
Aqui está o guia passo a passo para rodar e usar o scraping:

1. **Execute o Script**:
   No terminal, na pasta do projeto, execute:
   ```
   python scraping_cloudscraper_gui.py
   ```
   Você verá mensagens de log no terminal e a confirmação de que o servidor Flask está rodando em `http://127.0.0.1:5000`.

2. **Acesse a Interface**:
   Abra seu navegador (Chrome, Firefox, etc.) e vá para:
   ```
   http://127.0.0.1:5000/
   ```
   A tela inicial aparecerá com um campo para inserir a URL.

3. **Insira uma URL da Casa dos Dados**:
   - Exemplo: `https://casadosdados.com.br/solucao/cnpj?q=fluxo+juridicos`.
   - Digite ou cole a URL no campo e clique em **"Confirmar URL"**.
   - A tela 2 será exibida com os totais extraídos (ex.: "Leads Extraídos: 0 / 1", "Total de Páginas: 1").

4. **Inicie o Scraping**:
   - Clique em **"Iniciar"**.
   - A barra de progresso começará a se mover, e os indicadores (leads extraídos, página atual) serão atualizados em tempo real.
   - Use **"Pausar"** para pausar o processo (mostra "PAUSADO"), **"Parar"** para encerrar (mostra "PARADO"), ou deixe concluir.

5. **Baixe os Resultados**:
   - Após o primeiro bloco (ou ao parar), o "Último Arquivo disponível para download" aparecerá (ex.: `busca_multioperador_atualizado_bloco1.xlsx`).
   - Clique em **"Clique e baixe"** para baixar o arquivo Excel com os dados extraídos.

6. **Volte para uma Nova URL**:
   - Clique em **"Voltar"** para retornar à tela inicial e inserir outra URL.

## Exemplo de Uso
- **URL**: `https://casadosdados.com.br/solucao/cnpj?q=fluxo+juridicos`
- **Tela 2 Inicial**:
  ```
  Você está pesquisando por termo: fluxo juridicos na Casa dos Dados. Pronto para iniciar.
  Leads Extraídos: 0 / 1
  Total de Páginas: 1
  Página Atual: 1 / 1
  Bloco Atual: 1 / 1
  ```
- **Após Iniciar**:
  - A barra de progresso vai a 100%, "Leads Extraídos" muda para "1 / 1", e o arquivo Excel é gerado.

## Arquivos Gerados
- **`scraping_log.txt`**: Log detalhado do processo (criado automaticamente na pasta do projeto).
- **`scraping_state.json`**: Estado temporário do scraping (removido ao concluir).
- **`busca_multioperador_atualizado_blocoX.xlsx`**: Arquivos Excel com os dados (X é o número do bloco).

## Possíveis Problemas e Soluções
- **Erro ao Instalar Dependências**: Certifique-se de ter o Python no PATH e tente `pip3 install -r requirements.txt`.
- **Servidor Não Inicia**: Verifique se a porta 5000 está livre (ex.: feche outros servidores locais).
- **Scraping Não Funciona**: Confirme que a URL é válida da Casa dos Dados e que você tem conexão com a internet.

## Contribuições
Este projeto foi desenvolvido por [alencarnet]. Sinta-se à vontade para abrir issues ou pull requests no GitHub!

## Licença
MIT License - Use, modifique e distribua livremente, mantendo os créditos ao alencar neto e fluxo juridicos.
```

