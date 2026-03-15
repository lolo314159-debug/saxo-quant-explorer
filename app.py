import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import kurtosis, skew, norm
import matplotlib.pyplot as plt

# Configuration de la page
st.set_page_config(page_title="Saxo Quant Analyzer", layout="wide")

st.title("📊 Saxo Portfolio Quant Analyzer")
st.markdown("""
Cette application calcule le **Kurtosis** (risque de queue) et le **Skewness** (asymétrie) 
en utilisant les données réelles de la Saxo OpenAPI.
""")

# --- BARRE LATÉRALE : CONFIGURATION ---
st.sidebar.header("Configuration API")
token = st.sidebar.text_input("Saxo Access Token (24h)", type="password", help="Générez votre token sur developer.saxo")

# Sélection d'actifs (Exemples d'UIC courants)
asset_dict = {
    "Apple (AAPL)": "211",
    "LVMH (MC)": "16556",
    "TotalEnergies (TTE)": "16458",
    "S&P 500 ETF (SPY)": "40809",
    "Bitcoin Tracker (BTC)": "163627"
}
selected_asset = st.sidebar.selectbox("Choisir un actif", list(asset_dict.keys()))
uic = asset_dict[selected_asset]

# Paramètres de temps
horizon = st.sidebar.selectbox("Horizon", ["1Day", "1Hour"], index=0)
sample_size = st.sidebar.slider("Nombre de points de données", 100, 1000, 250)

# --- LOGIQUE DE CALCUL ---
if st.button("Lancer l'Analyse"):
    if not token:
        st.warning("⚠️ Veuillez entrer un token Saxo dans la barre latérale.")
    else:
        headers = {"Authorization": f"Bearer {token}"}
        # URL de l'API Saxo (Simulation/SIM)
        url = "https://gateway.saxobank.com/sim/openapi/chart/v1/charts/"
        params = {
            "Uic": uic,
            "AssetType": "Stock",
            "Horizon": horizon,
            "Count": sample_size
        }

        with st.spinner('Récupération des données Saxo...'):
            try:
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Extraction des prix de clôture
                prices = [d['Close'] for d in data['Data']]
                df = pd.DataFrame(prices, columns=['Close'])
                
                # Calcul des rendements (Returns)
                df['Returns'] = df['Close'].pct_change().dropna()
                returns = df['Returns'].dropna()

                # --- STATISTIQUES ---
                k_excess = kurtosis(returns, fisher=True)
                s_value = skew(returns)
                vol = returns.std() * np.sqrt(252 if horizon == "1Day" else 252*8)

                # Affichage des métriques
                col1, col2, col3 = st.columns(3)
                col1.metric("Kurtosis (Excès)", f"{k_excess:.4f}")
                col2.metric("Skewness (Asymétrie)", f"{s_value:.4f}")
                col3.metric("Volatilité Ann.", f"{vol:.2%}")

                # --- INTERPRÉTATION ---
                st.subheader("Analyse du Risque")
                if k_excess > 1:
                    st.error(f"🚩 **Kurtosis élevé ({k_excess:.2f})** : Ce titre présente des 'queues épaisses'. Les krachs ou hausses brutales sont plus fréquents que la normale.")
                else:
                    st.success("✅ **Kurtosis modéré** : La distribution est relativement proche d'une loi normale.")

                if s_value < -0.5:
                    st.warning(f"📉 **Skewness Négatif ({s_value:.2f})** : Les rendements ont une queue à gauche plus longue. Risque de pertes extrêmes plus probable.")

                # --- VISUALISATION ---
                st.subheader("Distribution des rendements vs Loi Normale")
                fig, ax = plt.subplots(figsize=(10, 5))
                
                # Histogramme des rendements réels
                count, bins, ignored = ax.hist(returns, bins=40, density=True, alpha=0.6, color='#1E88E5', label="Rendements Réels")
                
                # Courbe de Gauss (Loi Normale) pour comparaison
                mu, std = returns.mean(), returns.std()
                x = np.linspace(returns.min(), returns.max(), 100)
                p = norm.pdf(x, mu, std)
                ax.plot(x, p, 'r', linewidth=2, label="Loi Normale (Théorique)")
                
                ax.set_title(f"Distribution pour {selected_asset}")
                ax.legend()
                st.pyplot(fig)

            except Exception as e:
                st.error(f"Erreur lors de l'appel API : {e}")
                st.info("Vérifiez que votre Token est toujours valide (durée de 24h).")

st.sidebar.markdown("---")
st.sidebar.info("💡 Le Kurtosis mesure l'épaisseur des queues. Un score > 0 indique un risque de 'Cygne Noir'.")
