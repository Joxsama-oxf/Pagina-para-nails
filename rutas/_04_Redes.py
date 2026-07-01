import os
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from rutas._helpers import requiere_permiso
import requests

redes_bp = Blueprint('redes', __name__)

# El token de la Graph API se lee del .env (IG_TOKEN). Nunca va en el código.
TOKEN = os.environ.get('IG_TOKEN', '')

# Módulo de Redes deshabilitado temporalmente (sin cuenta de Instagram fija).
# Para reactivar: pon REDES_ACTIVO = True y configura IG_TOKEN en el .env.
REDES_ACTIVO = False


@redes_bp.route('/redes')
@login_required
@requiere_permiso('redes.ver')
def index():
    if not REDES_ACTIVO:
        return redirect(url_for('inicio.home'))

    datos_ig = {'conectado': False, 'error': None, 'perfil': {}, 'metricas': {}, 'publicaciones': []}

    if not TOKEN:
        datos_ig['error'] = "Instagram no está configurado (falta IG_TOKEN en el .env)."
        return render_template('redes.html', ig=datos_ig)

    try:
        url_accounts = f"https://graph.facebook.com/v19.0/me/accounts?fields=instagram_business_account&access_token={TOKEN}"
        res_accounts = requests.get(url_accounts).json()

        ig_id = None
        if 'data' in res_accounts:
            for page in res_accounts['data']:
                if 'instagram_business_account' in page:
                    ig_id = page['instagram_business_account']['id']
                    break

        if ig_id:
            campos_api = "username,name,profile_picture_url,biography,followers_count,media_count,media.limit(6){caption,media_type,media_url,thumbnail_url,permalink,like_count,comments_count}"
            url_ig = f"https://graph.facebook.com/v19.0/{ig_id}?fields={campos_api}&access_token={TOKEN}"
            res_ig = requests.get(url_ig).json()

            if 'username' in res_ig:
                datos_ig['conectado'] = True
                datos_ig['perfil'] = {
                    'username': res_ig.get('username', ''),
                    'name'    : res_ig.get('name', ''),
                    'biography': res_ig.get('biography', ''),
                    'picture' : res_ig.get('profile_picture_url', '')
                }
                datos_ig['metricas'] = {
                    'followers': f"{res_ig.get('followers_count', 0):,}",
                    'posts'    : f"{res_ig.get('media_count', 0):,}"
                }
                if 'media' in res_ig and 'data' in res_ig['media']:
                    datos_ig['publicaciones'] = res_ig['media']['data']
            else:
                datos_ig['error'] = "Permisos insuficientes para extraer el nodo de perfil."
        else:
            datos_ig['error'] = "Identificador de Instagram no localizado en la cuenta."
    except Exception as e:
        datos_ig['error'] = f"Error de ejecución interna: {str(e)}"

    return render_template('redes.html', ig=datos_ig)
