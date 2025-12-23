import requests
from bs4 import BeautifulSoup

# URL cible
URL = "https://www.brvm.org/fr/emetteurs/societes-cotees"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def espionner():
    print(f"🕵️‍♂️ Connexion au site : {URL}")
    try:
        session = requests.Session()
        response = session.get(URL, headers=HEADERS, verify=False)
        
        print(f"   Statut de la connexion : {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            
            # TEST 1 : Chercher "AIR LIQUIDE"
            print("\n--- TEST DE VISION ---")
            if "AIR LIQUIDE" in content or "Air Liquide" in content:
                print("✅ SUCES : Le robot VOIT le texte 'Air Liquide' !")
                
                # On cherche la balise autour pour savoir comment la cibler
                # On cherche un lien qui contient ce texte
                element = soup.find('a', string=lambda t: t and "AIR LIQUIDE" in t.upper())
                if element:
                    print(f"   Il est caché dans cette balise : {element.name}")
                    print(f"   Ses attributs sont : {element.attrs}")
                    print(f"   Son parent est : {element.parent.name} (Class: {element.parent.get('class')})")
                else:
                    print("   Je vois le texte, mais je n'arrive pas à isoler la balise exacte.")
            else:
                print("❌ ECHEC : Le robot NE VOIT PAS 'Air Liquide'.")
                print("👉 Conclusion : Le site utilise probablement du JavaScript pour afficher le tableau.")
                print("👉 Solution : On devra utiliser 'Selenium' au lieu de 'Requests'.")

            # TEST 2 : Compter les liens totaux
            links = soup.find_all('a')
            print(f"\nNombre total de liens trouvés sur la page : {len(links)}")
            
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    espionner()