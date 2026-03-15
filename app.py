import streamlit as st
import requests
import pandas as pd
from scipy.stats import kurtosis
import matplotlib.pyplot as plt

st.set_page_config(page_title="Saxo Quant Analytics", layout="wide")

st.title("📊 Analyse de Kurtosis - Saxo OpenAPI")

# Barre latérale pour l'authentification
token = st.sidebar.text_input("Saxo Token (24h)", type="password")
uic = st.sidebar.text_input("Code UIC de l'actif", value="211") # 211 = Apple

if st.button("Lancer l'analyse"):
    if not token:
        st.error("Veuillez entrer un token valide.")
    else:
        # Configuration API
        headers = {"Authorization": f"Bearer {token}"}
        url = "https://gateway.saxobank.com/sim/openapi/chart/v1/charts/"
        params = {"Uic": uic, "AssetType": "Stock", "Horizon": "1Day", "Count": 250}

        with st.spinner('Récupération des données...'):
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                prices = [d['Close'] for d in data['Data']]
                df = pd.DataFrame(prices, columns=['Close'])
                df['Returns'] = df['Close'].pct_change().dropna()

                # Calculs
                k_excess = kurtosis(df['Returns'].dropna(), fisher=True)
                
                # Affichage des métriques
                col1, col2 = st.columns(2)
                col1.metric("Kurtosis en excès", round(k_excess, 4))
                
                if k_excess > 0:
                    st.warning("⚠️ Attention : Queues épaisses détectées (Risque d'événements extrêmes).")
                else:
                    st.success("✅ Distribution stable (Faible risque de queues épaisses).")

                # Graphique de distribution
                fig, ax = plt.subplots()
                df['Returns'].hist(bins=50, ax=ax, color='skyblue', edgecolor='black')
                st.pyplot(fig)
            else:
                st.error(f"Erreur API : {response.status_code}")
