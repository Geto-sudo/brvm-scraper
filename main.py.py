from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import pandas as pd
import time
from datetime import datetime
import os
import io

# --- CONFIGURATION ---
URL = "https://www.brvm.org/fr/cours/actions"
FICHIER_SORTIE = "cours_brvm_edge.csv"
INTERVALLE = 60

def clean_money_column(col):
    """Nettoie les colonnes de prix"""
    if col.dtype == 'object':
        col = col.str.replace(r'[^\d,-]', '', regex=True)
        col = col.str.replace(',', '.')
        col = pd.to_numeric(col, errors='coerce').fillna(0.0)
    return col

def capture_cours_edge():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n⚡ [{now}] Lancement de Microsoft Edge...")

    try:
        # Configuration spécifique pour Edge
        options = webdriver.EdgeOptions()
        # options.add_argument("--headless") # Enlève le # pour cacher la fenêtre
        
        # On installe et lance le pilote Edge
        driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
        
        driver.get(URL)
        
        print("   ⏳ Attente de 10 secondes (Chargement tableau)...")
        time.sleep(10) 
        
        # On prend le HTML une fois chargé
        html_complet = driver.page_source
        
        # Pandas lit le HTML
        dfs = pd.read_html(io.StringIO(html_complet))
        print(f"   🔎 Pandas a trouvé {len(dfs)} tableaux.")
        
        target_df = None
        for df in dfs:
            # Recherche des colonnes clés
            cols = [str(c).strip() for c in df.columns]
            if "Symbole" in cols and "Volume" in cols:
                target_df = df
                break
        
        if target_df is None:
            print("   ❌ Tableau non trouvé.")
            driver.quit()
            return

        print("   ✅ Tableau identifié ! Extraction...")

        # Ajout date et nettoyage
        target_df['Date_Releve'] = now
        for col in target_df.columns:
            c_str = str(col)
            if any(x in c_str for x in ["Clôture", "Volume", "Variation", "Veille"]):
                target_df[col] = clean_money_column(target_df[col])

        # Sauvegarde
        header = not os.path.exists(FICHIER_SORTIE)
        target_df.to_csv(FICHIER_SORTIE, mode='a', header=header, index=False, sep=';', encoding='utf-8-sig')
        
        print(f"   💾 {len(target_df)} lignes sauvegardées dans {FICHIER_SORTIE}.")
        
        # Fermeture
        driver.quit()

    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        try:
            driver.quit()
        except:
            pass

# BOUCLE
print("🚀 Démarrage Moniteur (Version Edge)...")
while True:
    capture_cours_edge()
    print(f"   💤 Pause de {INTERVALLE}s...")
    time.sleep(INTERVALLE)