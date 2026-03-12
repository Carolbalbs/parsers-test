import streamlit as st
import spacy
import stanza
import pandas as pd
import requests
import spacy_streamlit
import pypdf
import io

# Configuração da página
st.set_page_config(
    page_title="Comparador de Parsers de Português",
    layout="wide"
)

st.title("🇧🇷Teste de Parsers para Português Brasileiro🇧🇷")
st.markdown("""
Esta ferramenta permite testar e comparar os outputs de três analisadores sintáticos:
**spaCy**, **Stanza** e **LX-Parser**.
""")

# --- Sidebar ---
st.sidebar.header("Configurações")
parser_choice = st.sidebar.radio(
    "Escolha o Parser:",
    ("spaCy", "Stanza", "LX-Parser")
)

# --- Funções de Carregamento (Cache para performance) ---

@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load("pt_core_news_lg")
    except OSError:
        st.error("Modelo do spaCy não encontrado. Rode `python setup_models.py`.")
        return None

@st.cache_resource
def load_stanza_pipeline():
    # Stanza carrega o pipeline na memória
    return stanza.Pipeline('pt', processors='tokenize,mwt,pos,lemma,depparse')

# --- Funções de Processamento ---

def process_spacy(text, nlp):
    doc = nlp(text)
    data = []
    for token in doc:
        data.append({
            "Texto": token.text,
            "Lema": token.lemma_,
            "POS": token.pos_,
            "Tag": token.tag_,
            "Dep": token.dep_,
            "Head": token.head.text
        })
    return doc, pd.DataFrame(data)

def process_stanza(text, nlp):
    doc = nlp(text)
    data = []
    # Stanza organiza em sentenças -> palavras
    for sent in doc.sentences:
        for word in sent.words:
            data.append({
                "Texto": word.text,
                "Lema": word.lemma,
                "POS": word.upos,
                "Tag": word.xpos,
                "Dep": word.deprel,
                "Head ID": word.head
            })
    return doc, pd.DataFrame(data)

def process_lx_parser(text):
    # Nota: LX-Parser via API pública (Online Service)
    # Endpoint público do LX-Center
    # Documentação de referência: https://portulanclarin.net/workbench/lx-parser/
    
    # ATENÇÃO: Esta é uma implementação de exemplo para a API JSON-RPC do LX-Parser.
    # A URL e o formato podem variar. Se falhar, mostraremos mensagem apropriada.
    
    # URL oficial pública para o parser de constituintes
    url = "http://ws.lxcenter.di.fc.ul.pt/services/parser/jsonrpc" 
    
    payload = {
        "method": "parse",
        "params": {
            "text": text,
            "format": "json" # Solicitando JSON para tentar estruturar
        },
        "jsonrpc": "2.0",
        "id": 0
    }
    
    try:
        # Tenta conectar. O timeout é importante para não travar a interface.
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                return result["result"], None # Retorna o raw por enquanto
            else:
                return None, f"Erro na resposta da API: {result}"
        else:
            return None, f"Erro HTTP: {response.status_code}"
            
    except Exception as e:
        return None, f"Erro ao conectar com LX-Parser: {str(e)}"

# --- Interface Principal ---

# Inicializa o session_state para o texto se não existir
if "input_text" not in st.session_state:
    st.session_state["input_text"] = "O rato roeu a roupa do rei de Roma."

# Widget de Upload
uploaded_file = st.file_uploader("Carregar arquivo (TXT ou PDF)", type=["txt", "pdf"])

if uploaded_file is not None:
    # Verifica se é um novo arquivo comparando com o último salvo
    if st.session_state.get("last_uploaded_file") != uploaded_file.name:
        try:
            string_data = ""
            if uploaded_file.type == "text/plain":
                string_data = str(uploaded_file.read(), "utf-8")
            elif uploaded_file.type == "application/pdf":
                reader = pypdf.PdfReader(uploaded_file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        string_data += text + "\n"
            
            # Atualiza o estado e salva o nome do arquivo para não recarregar no rerun
            st.session_state["input_text"] = string_data
            st.session_state["last_uploaded_file"] = uploaded_file.name
            st.rerun() # Força atualização da interface
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

# Text Area vinculado ao session_state
text_input = st.text_area("Digite ou edite o texto para análise:", key="input_text", height=150)

if st.button("Analisar Texto"):
    if not text_input.strip():
        st.warning("Por favor, digite um texto.")
    else:
        st.subheader(f"Resultados: {parser_choice}")
        
        if parser_choice == "spaCy":
            nlp = load_spacy_model()
            if nlp:
                with st.spinner("Processando com spaCy..."):
                    doc, df = process_spacy(text_input, nlp)
                    
                    st.write("### Tabela de Tokens")
                    st.dataframe(df, use_container_width=True)
                    
                    st.write("### Visualização de Dependência")
                    spacy_streamlit.visualize_parser(doc)

        elif parser_choice == "Stanza":
            with st.spinner("Carregando Stanza (pode demorar na primeira vez)..."):
                nlp = load_stanza_pipeline()
            
            with st.spinner("Processando com Stanza..."):
                doc, df = process_stanza(text_input, nlp)
                
                st.write("### Tabela de Tokens")
                st.dataframe(df, use_container_width=True)
                
                st.write("### Estrutura (Raw Data)")
                st.json(doc.to_dict())

        elif parser_choice == "LX-Parser":
            st.info("O LX-Parser está rodando via API (requer internet).")
            with st.spinner("Enviando para LX-Center..."):
                result, error = process_lx_parser(text_input)
                
                if error:
                    st.error(error)
                    st.markdown("Verifique se o serviço está online em [LX-Parser Workbench](https://portulanclarin.net/workbench/lx-parser/).")
                else:
                    st.success("Análise concluída!")
                    st.write("### Resultado (JSON Raw)")
                    st.json(result)
                    # Melhoria futura: implementar visualização de árvore de constituintes a partir do output do LX
