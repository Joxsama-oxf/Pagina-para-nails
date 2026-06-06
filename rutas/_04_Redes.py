from flask import Blueprint, render_template
from flask_login import login_required
from rutas._helpers import requiere_permiso
import requests

redes_bp = Blueprint('redes', __name__)
TOKEN = 'EAAMq9wrRXPIBQZBIe6K2zLoBZCAAOR6d60pCcazhIYl70idb9HLGhxS1Mz9HXOtsSBnSs5ulqov0eZCPD4RGMVZCOjJMz8tTIbuBIePeFzRbfRXs5PDq6U1QP9vIxhQIt621bUDuqkNswq6tpnecYM9JK436B3WgyHnsAbpk2btOg7lyDyoYz8MkuxMB2HZB7AHy6eEXpl8hwdCUyJqon0is2ZBfy6C1eVyQ7ZA'


@redes_bp.route('/redes')
@login_required
@requiere_permiso('redes.ver')
def index():
    datos_ig = {'conectado': False, 'error': None, 'perfil': {}, 'metricas': {}, 'publicaciones': []}

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
