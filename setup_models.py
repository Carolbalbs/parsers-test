import sys
import subprocess

def install_spacy_model():
    print("=== Baixando modelo do spaCy (pt_core_news_lg) ===")
    # Usando subprocess para garantir que instalamos no mesmo ambiente do python atual
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "pt_core_news_lg"])

def install_stanza_model():
    print("\n=== Baixando modelo do Stanza (pt) ===")
    import stanza
    # Baixa o modelo padrão para português
    stanza.download('pt')

if __name__ == "__main__":
    print("Iniciando configuração dos modelos NLP...\n")
    try:
        install_spacy_model()
        install_stanza_model()
        print("\n✅ Todos os modelos foram baixados com sucesso!")
        print("Agora você pode rodar a aplicação com: streamlit run app.py")
    except Exception as e:
        print(f"\n❌ Erro ao baixar modelos: {e}")
