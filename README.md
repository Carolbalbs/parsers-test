# Comparador de Parsers para Português 🇧🇷

Este projeto é uma interface Streamlit para comparar diferentes analisadores sintáticos (parsers) aplicados ao Português Brasileiro e Europeu.

## Parsers Incluídos
1. **spaCy**: Utiliza o modelo `pt_core_news_lg`.
2. **Stanza**: Pipeline da Stanford calibrado para Português.
3. **LX-Parser**: Serviço da Universidade de Lisboa (via API).

## Como Rodar Localmente

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute o app:
   ```bash
   streamlit run app.py
   ```

## Requisitos para Publicação no Streamlit Cloud

Para que este app funcione corretamente no [Streamlit Cloud](https://streamlit.io/cloud), os seguintes arquivos devem estar na raiz do repositório:

1. **`requirements.txt`**: Já configurado com todas as bibliotecas e o link direto para o modelo do spaCy.
2. **`app.py`**: O script principal da interface.
3. **Conexão com Internet**: Necessária para o Stanza baixar seus modelos na primeira execução e para as chamadas de API do LX-Parser.

### Dicas de Performance no Cloud:
- O modelo do Stanza (~500MB) será baixado na primeira vez que o parser for selecionado. O app usa `@st.cache_resource` para garantir que isso aconteça apenas uma vez por instância.
- O modelo do spaCy é instalado via `requirements.txt` para estar pronto no startup.

---
Desenvolvido para testes de Processamento de Linguagem Natural (PLN).
