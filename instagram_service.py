import requests
from bs4 import BeautifulSoup
import re
import random
import time

def obtener_datos_instagram():
    """
    Método de Respaldo: Lee las metaetiquetas HTML (og:description).
    Es menos propenso a bloqueos que Instaloader.
    """
    # Tu usuario (EL QUE TIENE GUION BAJO)
    USER = "laura_nailsbeautystudio"
    URL = f"https://www.instagram.com/{USER}/"

    # Cabeceras para parecer un navegador Chrome real de Windows
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9",
    }

    try:
        # Pausa mini para no saturar
        time.sleep(random.uniform(0.5, 1.5))

        response = requests.get(URL, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            return _datos_error(f"Error Código {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscamos la etiqueta que Google usa para ver tu perfil
        # Suele tener formato: "15 Followers, 48 Following, 13 Posts - ..."
        meta = soup.find("meta", property="og:description")

        if meta:
            texto = meta.attrs['content']
            print(f"DEBUG INSTAGRAM: {texto}") # Para que veas en consola qué lee

            # Extraer números usando Expresiones Regulares
            # Busca patrones como "15 Followers" o "15 Seguidores"
            seguidores = "0"
            siguiendo = "0"
            posts = "0"

            # Logica de extracción simple
            parts = texto.split(' - ')[0].split(', ')
            for part in parts:
                if 'Follower' in part or 'Seguidores' in part:
                    seguidores = part.split(' ')[0]
                elif 'Following' in part or 'Seguidos' in part:
                    siguiendo = part.split(' ')[0]
                elif 'Post' in part or 'Publicaciones' in part:
                    posts = part.split(' ')[0]

            return {
                "foto": "", # Scraping simple no saca la foto HD fácil sin login, se deja vacía o default
                "seguidores": seguidores,
                "conectado": True,
                "posts_count": posts,
                "likes": "Ver en App", # Metaetiquetas NO dan likes totales, solo perfil
                "comments": "Activo"
            }
        else:
            # Si Instagram nos manda al Login, fallamos silenciosamente
            return _datos_error("Redirección a Login")

    except Exception as e:
        print(f"⚠️ Error HTML Scraping: {e}")
        return _datos_error("Excepción")

def _datos_error(msg):
    return {
        "foto": "", 
        "seguidores": "-",
        "conectado": False,
        "posts_count": "-",
        "likes": "-",
        "comments": "-"
    }