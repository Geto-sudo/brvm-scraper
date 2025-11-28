import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time
import re
import warnings

# Ignorer les avertissements SSL
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

# --- CONFIGURATION ---
# C'est l'URL spécifique que tu m'as donnée
START_URL = "https://www.brvm.org/fr/emetteurs/type-annonces/convocations-assemblees-generales"
BASE_FOLDER = "BRVM_Convocations"  # Dossier où tout sera sauvegardé
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def clean_filename(name):
    """Nettoie un nom pour qu'il soit valide comme nom de fichier/dossier."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def download_file(session, url, folder, filename_prefix=""):
    """Télécharge un fichier PDF."""
    try:
        # Nettoyage du nom du fichier distant
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename.lower().endswith('.pdf'):
            filename += ".pdf"
        
        # On ajoute un préfixe (ex: nom de l'entreprise) si fourni
        if filename_prefix:
            # On coupe si c'est trop long pour éviter les erreurs Windows
            prefix_clean = clean_filename(filename_prefix)[:50] 
            full_filename = f"{prefix_clean}_{filename}"
        else:
            full_filename = filename
            
        save_path = os.path.join(folder, full_filename)

        if os.path.exists(save_path):
            print(f"  [Info] Déjà présent : {full_filename}")
            return

        print(f"  [Téléchargement] {full_filename}...")
        response = session.get(url, verify=False, timeout=20)
        
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"  [Succès] Sauvegardé.")
        else:
            print(f"  [Erreur] Statut {response.status_code}")
            
    except Exception as e:
        print(f"  [Echec] Erreur : {e}")

def scrape_convocations():
    # Création du dossier principal
    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)
        print(f"Dossier créé : {os.path.abspath(BASE_FOLDER)}")

    session = requests.Session()
    session.headers.update(HEADERS)
    
    current_page = 0
    
    while True:
        # Gestion de la pagination (page=0, page=1...)
        url = f"{START_URL}?page={current_page}"
        print(f"\n>>> Analyse de la page {current_page} : {url}")
        
        try:
            response = session.get(url, verify=False, timeout=15)
            if response.status_code != 200:
                print("Fin des pages ou erreur d'accès.")
                break
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Recherche de tous les liens PDF sur la page
            # Sur ce site, les liens de téléchargement contiennent souvent "file" ou finissent par .pdf
            # On cherche aussi les balises qui contiennent le texte "Télécharger"
            
            links_found = 0
            
            # Stratégie : On cherche les blocs d'annonces (souvent dans des 'views-row')
            rows = soup.find_all('div', class_='views-row')
            
            if not rows:
                print("Aucune annonce trouvée sur cette page (structure différente ?).")
                # Tentative de secours : chercher tous les liens PDF bruts
                raw_pdf_links = soup.select('a[href$=".pdf"]')
                for link in raw_pdf_links:
                    pdf_url = urljoin(START_URL, link['href'])
                    download_file(session, pdf_url, BASE_FOLDER)
                    links_found += 1
            else:
                for row in rows:
                    # Essai de trouver le titre ou l'entreprise dans la ligne
                    text_content = row.get_text(separator=" ", strip=True)
                    
                    # On cherche le lien PDF à l'intérieur de cette ligne
                    pdf_link = row.find('a', href=True)
                    
                    # Parfois il y a plusieurs liens, on cherche celui qui mène à un fichier
                    # ou qui contient 'Télécharger'
                    valid_link = None
                    for a in row.find_all('a', href=True):
                        if '.pdf' in a['href'].lower() or 'upload' in a['href'].lower():
                            valid_link = a['href']
                            break
                    
                    if valid_link:
                        pdf_url = urljoin(START_URL, valid_link)
                        # On utilise le début du texte comme "Nom d'entreprise" présumé
                        # Ex: "BOA SENEGAL : Avis de convocation..." -> on garde "BOA SENEGAL"
                        company_guess = text_content.split(':')[0] if ':' in text_content else "Document"
                        
                        download_file(session, pdf_url, BASE_FOLDER, filename_prefix=company_guess)
                        links_found += 1

            print(f"   -> {links_found} documents traités sur cette page.")
            
            # Si on ne trouve rien sur la page 0 ou 1, c'est suspect, mais on continue un peu
            if links_found == 0 and current_page > 2:
                print("Aucun document trouvé sur plusieurs pages consécutives. Arrêt.")
                break

            # Vérification s'il y a une page suivante (bouton 'suivant' ou 'next')
            next_button = soup.find('a', title='Aller à la page suivante')
            if not next_button and links_found == 0:
                 # Si pas de bouton suivant et pas de liens, c'est fini
                 break
            
            current_page += 1
            time.sleep(1) # Pause politesse
            
        except Exception as e:
            print(f"Erreur critique : {e}")
            break

if __name__ == "__main__":
    scrape_convocations()