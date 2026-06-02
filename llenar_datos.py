from app import app
from models import db, Servicio, User
from werkzeug.security import generate_password_hash

with app.app_context():
    print("⏳ Iniciando restauración completa del sistema...")

    # ==========================================
    # PARTE 1: RESTAURAR SERVICIOS (CATÁLOGO)
    # ==========================================
    if Servicio.query.count() == 0:
        servicios = [
            Servicio(nombre="Manicure Tradicional", precio=5.00, categoria="Manos"),
            Servicio(nombre="Pedicure Spa", precio=12.00, categoria="Pies"),
            Servicio(nombre="Sistema Softgel", precio=25.00, categoria="Uñas"),
            Servicio(nombre="Retiro de Sistema", precio=5.00, categoria="Mantenimiento"),
            Servicio(nombre="Corte de Cabello", precio=8.00, categoria="Cabello"),
            Servicio(nombre="Esmaltado Semipermanente", precio=10.00, categoria="Manos")
        ]
        db.session.add_all(servicios)
        print("✅ Servicios agregados correctamente.")
    else:
        print("ℹ️ Los servicios ya existían.")

    # ==========================================
    # PARTE 2: RESTAURAR USUARIOS (DESDE TU AUTH.PY)
    # ==========================================
    
    # Lista copiada de tu código
    usuarios_a_crear = [
        # ADMINS
        {'email': 'lauranadmin@gmail.com',  'pass': 'Anabella03#.,', 'role': 'admin'},
        {'email': 'lauranadmin2@gmail.com', 'pass': 'Anabella03#.,', 'role': 'admin'},
        
        # MANICURISTAS
        {'email': 'lauranails01@gmail.com', 'pass': 'Beauty01',   'role': 'empleada'},
        {'email': 'lauranails02@gmail.com', 'pass': 'Studio71',   'role': 'empleada'},
        {'email': 'lauranails03@gmail.com', 'pass': 'Nails2026',  'role': 'empleada'}
    ]

    count_users = 0
    for u in usuarios_a_crear:
        # Verificamos si el usuario ya existe para no duplicar
        user_existente = User.query.filter_by(email=u['email']).first()
        
        if not user_existente:
            # Encriptamos la clave (IMPORTANTE)
            hashed_pw = generate_password_hash(u['pass']) # Usamos el método por defecto que es compatible
            
            nuevo_usuario = User(email=u['email'], password=hashed_pw, role=u['role'])
            db.session.add(nuevo_usuario)
            count_users += 1
    
    db.session.commit()
    print(f"✅ Usuarios restaurados: {count_users} nuevos usuarios creados.")
    print("🚀 ¡BASE DE DATOS LISTA PARA USAR!")