import streamlit as st
import requests
from api_client import AccessFlowClient
from datetime import date

# Configuracion de página
st.set_page_config(page_title="AccessFlow", page_icon="🔐", layout="wide")

def _init_session():
    if "token" not in st.session_state:
        st.session_state.token = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "client" not in st.session_state:
        st.session_state.client = AccessFlowClient()

def page_login():
    st.title("🔐 AccessFlow - Iniciar Sesión")
    st.markdown("Bienvenido al sistema de gestión de accesos.")
    
    with st.container():
        email = st.text_input("Correo electrónico", placeholder="ejemplo@accessflow.com")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", type="primary"):
            if email and password:
                try:
                    client = st.session_state.client
                    data = client.login(email, password)
                    st.session_state.token = data["access_token"]
                    st.session_state.role = data["role"]
                    st.success("Inicio de sesión exitoso!")
                    st.rerun()
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        st.error("Credenciales incorrectas.")
                    else:
                        st.error(f"Error del servidor: {e}")
                except Exception as e:
                    st.error(f"Ocurrió un error: {e}")
            else:
                st.warning("Por favor, ingresa correo y contraseña.")

def logout():
    st.session_state.token = None
    st.session_state.role = None
    st.session_state.client = AccessFlowClient() # Reset client
    st.rerun()

def render_sidebar():
    st.sidebar.title("Menú Principal")
    role = st.session_state.role
    st.sidebar.markdown(f"**Rol:** {role}")
    
    # Menú dependiendo del rol
    selected_page = None
    if role == "EMPLOYEE":
        selected_page = st.sidebar.radio(
            "Navegación",
            ["Mis Solicitudes", "Nueva Solicitud"]
        )
    else:
        st.sidebar.info(f"Vistas para el rol {role} se implementarán posteriormente.")
        selected_page = "Pendiente"
    
    st.sidebar.divider()
    if st.sidebar.button("Cerrar Sesión"):
        logout()
        
    return selected_page

def page_my_requests():
    st.title("Mis Solicitudes")
    client = st.session_state.client
    
    try:
        requests_list = client.get_requests()
        if not requests_list:
            st.info("No tienes solicitudes creadas.")
            return
        
        # Muestra un listado, usando expanders para el detalle
        for req in requests_list:
            status_color = "🟢" if req["status"] == "APPROVED" else "🟡" if req["status"] in ["DRAFT", "SUBMITTED", "MANAGER_REVIEW", "SECURITY_REVIEW"] else "🔴"
            with st.expander(f"{status_color} {req['target_system']} - {req['access_level']} ({req['status']})"):
                st.write(f"**ID:** `{req['id']}`")
                st.write(f"**Estado:** `{req['status']}`")
                st.write(f"**Nivel de Acceso:** `{req['access_level']}`")
                st.write(f"**Sistema:** `{req['target_system']}` ({req['system_type']})")
                st.write(f"**Fecha Creación:** `{req['created_at']}`")
                if req.get('expiration_date'):
                    st.write(f"**Expira:** `{req['expiration_date']}`")
                st.write(f"**Justificación:** {req['justification']}")
                
    except Exception as e:
        st.error(f"Error al obtener solicitudes: {e}")

def page_new_request():
    st.title("Nueva Solicitud de Acceso")
    client = st.session_state.client
    
    target_system = st.text_input("Sistema Destino", placeholder="Ej. Base de datos de clientes")
    
    system_types = ["GITHUB", "DATABASE", "DASHBOARD", "CRM", "SUPPORT", "CLOUD", "ADMIN_PANEL", "PRODUCTIVE_DATABASE", "OTHER"]
    system_type = st.selectbox("Tipo de Sistema", system_types)
    
    access_levels = ["READ", "WRITE", "ADMIN"]
    access_level = st.selectbox("Nivel de Acceso Requerido", access_levels)
    
    justification = st.text_area("Justificación", placeholder="Motivo por el cual necesitas este acceso...")
    
    # Lógica condicional para la fecha de expiración
    if access_level == "ADMIN":
        st.warning("El nivel ADMIN requiere obligatoriamente una fecha de expiración.")
        exp_date_input = st.date_input("Fecha de Expiración", min_value=date.today())
        expiration_date = exp_date_input.isoformat()
    else:
        use_exp_date = st.checkbox("¿Deseas establecer una fecha de expiración? (Opcional)")
        if use_exp_date:
            exp_date_input = st.date_input("Fecha de Expiración", min_value=date.today())
            expiration_date = exp_date_input.isoformat()
        else:
            expiration_date = None
            
    if st.button("Crear Solicitud", type="primary"):
        if not target_system or not justification:
            st.error("Por favor, completa los campos requeridos (Sistema Destino y Justificación).")
        elif access_level == "ADMIN" and not expiration_date:
             st.error("Para nivel ADMIN, debes proporcionar una fecha de expiración válida.")
        else:
            try:
                res = client.create_request(
                    target_system=target_system,
                    access_level=access_level,
                    justification=justification,
                    system_type=system_type,
                    expiration_date=expiration_date
                )
                st.success(f"Solicitud creada exitosamente con ID: {res['id']}")
            except Exception as e:
                st.error(f"Error al crear la solicitud: {e}")

def main():
    _init_session()
    
    if not st.session_state.token:
        page_login()
    else:
        page = render_sidebar()
        if page == "Mis Solicitudes":
            page_my_requests()
        elif page == "Nueva Solicitud":
            page_new_request()
        elif page == "Pendiente":
            st.title("Pantalla Pendiente")
            st.info("Funcionalidad no implementada en esta fase.")

if __name__ == "__main__":
    main()
