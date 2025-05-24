import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime
import matplotlib.pyplot as plt
import os

# Configurações de conexão com MySQL usando variáveis de ambiente
db_config = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "user"),
    "password": os.environ.get("DB_PASSWORD", "pass"),
    "database": os.environ.get("DB_NAME", "lab")
}

def conectar_db():
    return mysql.connector.connect(**db_config)

def criar_tabela():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            ID VARCHAR(255) PRIMARY KEY,
            DataEntrada DATE,
            Equipamento VARCHAR(255),
            SN VARCHAR(255),
            Quantidade INT,
            Fabricante VARCHAR(255),
            Status VARCHAR(255),
            Responsavel VARCHAR(255),
            Email VARCHAR(255),
            DataSaida DATE
        )
    """)
    conn.commit()
    conn.close()

def carregar_dados():
    conn = conectar_db()
    df = pd.read_sql("SELECT * FROM chamados", conn, parse_dates=["DataEntrada", "DataSaida"])
    conn.close()
    return df

def salvar_chamado(chamado):
    conn = conectar_db()
    cursor = conn.cursor()
    sql = """
        INSERT INTO chamados (
            ID, DataEntrada, Equipamento, SN, Quantidade, Fabricante,
            Status, Responsavel, Email, DataSaida
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (
        chamado["ID"], chamado["DataEntrada"], chamado["Equipamento"],
        chamado["S/N"], chamado["Quantidade"], chamado["Fabricante"],
        chamado["Status"], chamado["Responsável"], chamado["Email"], None
    ))
    conn.commit()
    conn.close()

def deletar_chamado(id_chamado):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chamados WHERE ID = %s", (id_chamado,))
    conn.commit()
    conn.close()

criar_tabela()

def dias_no_lab(data_entrada):
    return (datetime.now() - pd.to_datetime(data_entrada)).days

def cor_status(dias):
    if dias <= 14:
        return '🟩'
    elif dias <= 25:
        return '🟧'
    else:
        return '🟥'

st.title("📊 Controle de Equipamentos LAB")

df = carregar_dados()

with st.form("novo_chamado"):
    st.subheader("📝 Registrar novo chamado")
    id_chamado = st.text_input("ID")
    data_entrada = st.date_input("Data de Entrada", value=datetime.now())
    equipamento = st.text_input("Equipamento")
    sn = st.text_input("S/N")
    quantidade = st.number_input("Quantidade", min_value=1, step=1)
    fabricante = st.selectbox("Fabricante", sorted([
        "Huawei", "Mikrotik", "Juniper", "A10", "ZTE", "Nokia", "Vsol", "Dell",
        "Lenovo", "XPS", "TP Link", "Zyxel", "DLink", "Desktop",
        "Multilaser", "Positivo", "Notebook", "Realtek"
    ]))
    status = st.selectbox("Status", [
        "Configurar", "Homologar", "Teste de qualidade", "Verificação de Funcionamento",
        "Finalizado", "Homologado", "Teste OK", "Verificação concluida",
        "Aguardando Aprovação", "Devolução ao Almoxarifado"
    ])
    responsavel = st.text_input("Nome do Responsável")
    email = st.text_input("Email do Responsável")
    submitted = st.form_submit_button("Adicionar")

    if submitted:
        novo = {
            "ID": id_chamado,
            "DataEntrada": data_entrada,
            "Equipamento": equipamento,
            "S/N": sn,
            "Quantidade": quantidade,
            "Fabricante": fabricante,
            "Status": status,
            "Responsável": responsavel,
            "Email": email
        }
        salvar_chamado(novo)
        st.success("Chamado adicionado com sucesso!")
        st.experimental_rerun()

df["Dias no LAB"] = df["DataEntrada"].apply(dias_no_lab)
df["Indicador"] = df["Dias no LAB"].apply(cor_status)

st.subheader("📋 Painel de Equipamentos")
for i, row in df.iterrows():
    with st.expander(f"🔧 Chamado {row['ID']} - {row['Equipamento']}"):
        st.write(f"**Data de Entrada:** {row['DataEntrada'].date()}")
        st.write(f"**Fabricante:** {row['Fabricante']}")
        st.write(f"**Status:** {row['Status']}")
        st.write(f"**Responsável:** {row['Responsavel']} ({row['Email']})")
        st.write(f"**Dias no LAB:** {row['Dias no LAB']} {row['Indicador']}")
        st.write(f"**Quantidade:** {row['Quantidade']}")
        if st.button("🗑️ Deletar", key=f"del_{i}"):
            deletar_chamado(row["ID"])
            st.success(f"Chamado {row['ID']} deletado.")
            st.experimental_rerun()

alertas = df[df["Dias no LAB"] >= 30]
if not alertas.empty:
    st.warning("⚠️ Existem chamados com mais de 30 dias. Enviar e-mail ao responsável!")