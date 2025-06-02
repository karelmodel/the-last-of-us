import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px

HEADERS = {
    "Accept-Language": "pt-BR,pt;q=0.9,en-US,en;q=0.8",
    "User-Agent": "Mozilla/5.0"
}

@st.cache_data
def pegar_episodios_temporada(season_num):
    url = f"https://www.imdb.com/pt/title/tt3581920/episodes/?season={season_num}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    artigos = soup.find_all("article", class_="episode-item-wrapper")
    episodios = []
    for art in artigos:
        titulo_div = art.select_one("div.ipc-title__text")
        titulo = titulo_div.get_text(strip=True) if titulo_div else "Título não encontrado"
        
        a_tag = art.select_one("a[href]")
        link = "https://www.imdb.com" + a_tag['href'] if a_tag and 'href' in a_tag.attrs else ""
        
        rating_span = art.select_one("span.ipc-rating-star--rating")
        rating_str = rating_span.get_text(strip=True).replace(',', '.') if rating_span else "0"
        try:
            rating = float(rating_str)
        except ValueError:
            rating = 0.0
        
        votos_span = art.select_one("span.ipc-rating-star--voteCount")
        votos_str = votos_span.get_text(strip=True) if votos_span else "0"
        # limpar string de votos: remover parenteses e converter 'mil' para número
        votos_str = votos_str.replace('(', '').replace(')', '').replace('.', '').lower()
        if 'mil' in votos_str:
            votos_str = votos_str.replace('mil', '').strip()
            try:
                votos = int(float(votos_str) * 1000)
            except ValueError:
                votos = 0
        else:
            try:
                votos = int(votos_str)
            except ValueError:
                votos = 0
        
        episodios.append({
            "temporada": season_num,
            "titulo": titulo,
            "link": link,
            "nota": rating,
            "votos": votos
        })
    return episodios

# --- Streamlit UI ---
st.set_page_config(
    page_title="The Last of Us - IMDb Explorer",  # Título da aba do navegador
    title="🎬 The Last of Us - IMDb",
    page_icon="🎬",  # Ícone da aba (pode ser emoji ou URL)
    layout="centered"
)

st.image(
    "https://m.media-amazon.com/images/M/MV5BYWI3ODJlMzktY2U5NC00ZjdlLWE1MGItNWQxZDk3NWNjN2RhXkEyXkFqcGc@._V1_FMjpg_UY2048_.jpg",
    width=400
)

# --- Coletar dados ---
todas_temporadas = [1, 2]
dados = []
for temporada in todas_temporadas:
    dados += pegar_episodios_temporada(temporada)

df = pd.DataFrame(dados)

# --- Mostrar por temporada ---
for temporada in sorted(df["temporada"].unique()):
    df_temp = df[df["temporada"] == temporada].reset_index(drop=True)
    media_nota = df_temp["nota"].mean()
    total_votos = df_temp["votos"].sum()

    st.subheader(f"Temporada {temporada} — Média: {media_nota:.2f} ⭐, 👥 Votos: {total_votos:,}")

    # Gráfico de notas
    fig_rating = px.bar(
        df_temp,
        x=df_temp.index + 1,  # índice para número do episódio
        y="nota",
        text="nota",
        title=f"Notas dos episódios - Temporada {temporada}",
        labels={"x": "Número do Episódio", "nota": "Nota IMDb"},
        color="nota",
        color_continuous_scale="Viridis"
    )
    fig_rating.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig_rating.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=1), yaxis_range=[0, 10])
    st.plotly_chart(fig_rating, use_container_width=True)

    # Gráfico de votos
    fig_votos = px.bar(
        df_temp,
        x=df_temp.index + 1,
        y="votos",
        text="votos",
        title=f"Total de votos por episódio - Temporada {temporada}",
        labels={"x": "Número do Episódio", "votos": "Votos"},
        color="votos",
        color_continuous_scale="Blues"
    )
    fig_votos.update_traces(texttemplate='%{text:d}', textposition='outside')
    fig_votos.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=1))
    st.plotly_chart(fig_votos, use_container_width=True)

    # Lista de episódios
    #st.markdown("📺 Lista de Episódios")
    #for _, ep in df_temp.iterrows():
    #    st.markdown(f"**🧾 [{ep['titulo']}]({ep['link']})**")
    #    st.markdown(f"⭐ Nota: **{ep['nota']}**")
    #    st.markdown(f"👥 Votos: **{ep['votos']:,}**")
    #    st.markdown("---")

    with st.expander("📺 Lista de Episódios", expanded=False):
        for _, ep in df_temp.iterrows():
            st.markdown(f"**🧾 [{ep['titulo']}]({ep['link']})**")
            st.markdown(f"⭐ Nota: **{ep['nota']}**")
            st.markdown(f"👥 Votos: **{ep['votos']:,}**")
            st.markdown("---")