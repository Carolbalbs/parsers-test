import streamlit as st
import pandas as pd
import requests
import io
import os

# Imports protegidos para evitar que o script quebre se a instalação falhar
try:
    import spacy
    import spacy_streamlit
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    import stanza
    STANZA_AVAILABLE = True
except ImportError:
    STANZA_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# Configuração da página
st.set_page_config(
    page_title="Comparador de Parsers de Português",
    page_icon="🇧🇷",
    layout="wide"
)

# Estilo CSS customizado
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #0068c9;
        color: white;
    }
    .stDataFrame {
        background-color: white;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🇧🇷 Analisador Sintático para Português")
st.markdown("""
Esta ferramenta permite testar e comparar os outputs de três poderosos analisadores sintáticos:
**spaCy**, **Stanza** (Stanford) e **LX-Parser** (Universidade de Lisboa).
""")

# --- Sidebar ---
st.sidebar.image("https://www.streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=200)
st.sidebar.header("⚙️ Configurações")
parser_choice = st.sidebar.radio(
    "Escolha o Parser:",
    ("spaCy", "Stanza", "LX-Parser"),
    help="Selecione o motor de processamento de linguagem natural."
)

st.sidebar.markdown("---")
st.sidebar.info("""
### Sobre os Parsers:
- **spaCy**: Rápido e eficiente, usa o modelo `pt_core_news_lg`.
- **Stanza**: Alta precisão, baseado em redes neurais da Stanford.
- **LX-Parser**: Especializado em Português (LX-Center, Lisboa).
""")

# --- Funções de Carregamento ---

@st.cache_resource
def load_spacy_model():
    model_name = "pt_core_news_lg"
    try:
        return spacy.load(model_name)
    except OSError:
        with st.spinner(f"Baixando modelo {model_name} (primeira execução)..."):
            spacy.cli.download(model_name)
            return spacy.load(model_name)
    except Exception as e:
        st.error(f"Erro ao carregar spaCy: {e}")
        return None

@st.cache_resource
def load_stanza_pipeline():
    # Verifica se os modelos já foram baixados para evitar downloads repetidos em cada sessão
    models_path = os.path.join(os.path.expanduser("~"), "stanza_resources")
    if not os.path.exists(os.path.join(models_path, "pt")):
        with st.spinner("Baixando modelos do Stanza para Português (pode demorar alguns minutos na primeira execução)..."):
            stanza.download('pt', processors='tokenize,mwt,pos,lemma,depparse')
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
    url = "http://ws.lxcenter.di.fc.ul.pt/services/parser/jsonrpc" 
    payload = {
        "method": "parse",
        "params": {
            "text": text,
            "format": "json"
        },
        "jsonrpc": "2.0",
        "id": 0
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                return result["result"], None
            else:
                return None, f"Erro na resposta da API: {result.get('error', 'Desconhecido')}"
        else:
            return None, f"Erro HTTP: {response.status_code}"
    except Exception as e:
        return None, f"Erro de conexão: {str(e)}"

# --- Interface Principal ---

# Avisos de bibliotecas faltando
if not SPACY_AVAILABLE:
    st.error("⚠️ **spaCy** não está instalado corretamente. Algumas funcionalidades podem não funcionar.")
if not STANZA_AVAILABLE:
    st.warning("⚠️ **Stanza** não está disponível. O parser da Stanford foi desabilitado.")
if not PYPDF_AVAILABLE:
    st.info("ℹ️ Suporte a PDF desabilitado (pypdf não encontrado).")

# Inicialização do estado
if "input_text" not in st.session_state:
    st.session_state["input_text"] = "O rato roeu a roupa do rei de Roma."

# Upload de arquivos
with st.expander("📂 Carregar Documento (TXT ou PDF)"):
    if not PYPDF_AVAILABLE:
        st.warning("Upload de PDF desabilitado. Instale 'pypdf' para habilitar.")
        uploaded_file = st.file_uploader("Arraste ou selecione um arquivo TXT", type=["txt"])
    else:
        uploaded_file = st.file_uploader("Arraste ou selecione um arquivo", type=["txt", "pdf"])
    
    if uploaded_file is not None:
        if st.session_state.get("last_uploaded_file") != uploaded_file.name:
            try:
                content = ""
                if uploaded_file.type == "text/plain":
                    content = str(uploaded_file.read(), "utf-8")
                elif uploaded_file.type == "application/pdf" and PYPDF_AVAILABLE:
                    reader = pypdf.PdfReader(uploaded_file)
                    content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                
                st.session_state["input_text"] = content
                st.session_state["last_uploaded_file"] = uploaded_file.name
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")

# Entrada de texto
text_input = st.text_area("Texto para análise:", key="input_text", height=200)

col1, col2 = st.columns([1, 4])
with col1:
    analyze_btn = st.button("🚀 Analisar")

if analyze_btn:
    if not text_input.strip():
        st.warning("⚠️ Por favor, insira algum texto para analisar.")
    else:
        st.markdown(f"### 📊 Resultados: {parser_choice}")
        
        if parser_choice == "spaCy":
            if not SPACY_AVAILABLE:
                st.error("Erro: spaCy não disponível.")
            else:
                nlp = load_spacy_model()
                if nlp:
                    with st.spinner("Processando com spaCy..."):
                        doc, df = process_spacy(text_input, nlp)
                        
                        st.write("#### Tabela de Tokens")
                        st.dataframe(df, use_container_width=True)
                        
                        st.write("#### Visualização de Dependência")
                        spacy_streamlit.visualize_parser(doc)

        elif parser_choice == "Stanza":
            if not STANZA_AVAILABLE:
                st.error("Erro: Stanza não disponível.")
            else:
                nlp = load_stanza_pipeline()
                with st.spinner("Processando com Stanza..."):
                    doc, df = process_stanza(text_input, nlp)
                    
                    st.write("#### Tabela de Tokens")
                    st.dataframe(df, use_container_width=True)
                    
                    with st.expander("Ver Dados Brutos (JSON)"):
                        st.json(doc.to_dict())

        elif parser_choice == "LX-Parser":
            st.info("ℹ️ O LX-Parser utiliza uma API externa. Certifique-se de estar conectado à internet.")
            with st.spinner("Enviando para LX-Center (Lisboa)..."):
                result, error = process_lx_parser(text_input)
                
                if error:
                    st.error(f"❌ {error}")
                    st.markdown("O serviço pode estar temporariamente offline. Verifique o status em [LX-Parser Workbench](https://portulanclarin.net/workbench/lx-parser/).")
                else:
                    st.success("✅ Análise concluída!")
                    st.write("#### Resultado da API (JSON)")
                    st.json(result)

# Rodapé
st.markdown("---")
st.markdown("Desenvolvido para fins de pesquisa em Linguística Computacional.")
