import re
import streamlit as st
import sqlite3
import pandas as pd
import os
import tempfile
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq

load_dotenv()

def get_schema(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    return "\n".join(tables)

prompt = PromptTemplate(
    input_variables=["schema", "pergunta"],
    template="""
Você é um especialista em SQL para bancos SQLite.

Abaixo está o schema do banco de dados. Com base nele e na pergunta do usuário, gere **apenas uma consulta SQL funcional e otimizada ao máximo**, sem qualquer explicação, comentário ou formatação em Markdown.

- Não explique o código.
- Não use blocos ```sql.
- Não escreva texto antes ou depois da consulta.
- A resposta deve conter **somente a consulta SQL**, nada mais.

Schema:
{schema}

Pergunta:
{pergunta}

SQL:
"""
)

def gerar_sql(pergunta, schema):
    llm = ChatGroq(
        model_name="llama3-70b-8192",
        groq_api_key = os.getenv("GROQ_API_KEY")
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(schema=schema, pergunta=pergunta)

def extrair_sql(texto):
    # Tenta pegar trecho entre ```sql e ```
    match = re.search(r"```sql(.*?)```", texto, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    else:
        # Se não encontrar, tenta extrair a partir de SELECT
        select_pos = texto.upper().find("SELECT")
        if select_pos != -1:
            return texto[select_pos:].strip()
        return texto.strip()

def main():
    st.set_page_config(page_title="Otimizador SQL com IA", page_icon="🧠")
    st.title("🧠 Otimizador de Consultas SQL com IA")

    st.markdown("Faça upload de um banco de dados `.db` para análise e melhoria de consultas.")

    uploaded_file = st.file_uploader("📁 Envie seu arquivo .db (SQLite):", type="db")

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            db_path = tmp_file.name

        conn = sqlite3.connect(db_path)
        schema = get_schema(conn)
        st.success("Banco carregado com sucesso!")
        st.text_area("📘 Schema extraído:", schema, height=600, disabled=True)

        pergunta = st.text_area("❓ Pergunta ou pedido de melhoria:", height=100)

        if st.button("Gerar SQL Otimizado"):
            if not pergunta.strip():
                st.warning("Digite uma pergunta antes de continuar.")
            else:
                resposta = gerar_sql(pergunta, schema)
                sql = extrair_sql(resposta)
                st.code(sql, language="sql")

                try:
                    df = pd.read_sql_query(sql, conn)
                    st.success("✅ Consulta executada com sucesso!")
                    st.dataframe(df)
                except Exception as e:
                    pass

if __name__ == "__main__":
    main()


