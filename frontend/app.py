import streamlit as st
import requests
from api_client import AccessFlowClient

# Importar las vistas
from views.employee import page_my_requests, page_new_request
from views.manager import page_manager_dashboard
from views.security import page_security_dashboard
from views.it_admin import page_it_admin_dashboard
from views.notifications import page_notifications
from views.audit import page_system_audit

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
    st.session_state.client = AccessFlowClient()
    st.rerun()

def render_sidebar():
    st.sidebar.title("Menú Principal")
    role = st.session_state.role
    st.sidebar.markdown(f"**Rol:** {role}")
    
    # Opciones de navegación dependiendo del rol
    options = []
    if role == "EMPLOYEE":
        options = ["Mis Solicitudes", "Nueva Solicitud", "Notificaciones"]
    elif role == "MANAGER":
        options = ["Bandeja de Aprobación", "Notificaciones"]
    elif role == "SECURITY_REVIEWER":
        options = ["Revisión de Seguridad", "Notificaciones"]
    elif role == "IT_ADMIN":
        options = ["Provisionamiento", "Notificaciones"]
    elif role == "SYSTEM_ADMIN":
        options = ["Auditoría Global", "Notificaciones"]
    else:
        st.sidebar.info(f"Vistas para el rol {role} se implementarán posteriormente.")
        options = ["Notificaciones"]

    selected_page = st.sidebar.radio("Navegación", options)
    
    st.sidebar.divider()
    if st.sidebar.button("Cerrar Sesión"):
        logout()
        
    return selected_page

def main():
    _init_session()
    
    if not st.session_state.token:
        page_login()
    else:
        page = render_sidebar()
        
        # Enrutamiento de vistas
        if page == "Mis Solicitudes":
            page_my_requests()
        elif page == "Nueva Solicitud":
            page_new_request()
        elif page == "Bandeja de Aprobación":
            page_manager_dashboard()
        elif page == "Revisión de Seguridad":
            page_security_dashboard()
        elif page == "Provisionamiento":
            page_it_admin_dashboard()
        elif page == "Notificaciones":
            page_notifications()
        elif page == "Auditoría Global":
            page_system_audit()
        else:
            st.title("Pantalla Pendiente")
            st.info("Funcionalidad no implementada en esta fase.")

if __name__ == "__main__":
    main()
