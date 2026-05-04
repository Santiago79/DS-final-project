import streamlit as st
from datetime import date
import requests

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
                st.write(f"**Fecha Creación:** `{req['created_at'][:10]}`")
                if req.get('expiration_date'):
                    st.write(f"**Expira:** `{req['expiration_date']}`")
                st.write(f"**Justificación:** {req['justification']}")
                if req['status'] == "REJECTED" and req.get('rejection_reason'):
                    st.error(f"**Motivo del rechazo:** {req['rejection_reason']}")
                if req['status'] == "CHANGES_REQUESTED" and req.get('changes_requested_comment'):
                    st.warning(f"**Cambios solicitados:** {req['changes_requested_comment']}")
                
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
        if not target_system or len(target_system) < 2:
            st.error("El Sistema Destino debe tener al menos 2 caracteres.")
        elif not justification or len(justification) < 5:
            st.error("La Justificación debe tener al menos 5 caracteres.")
        elif access_level == "ADMIN" and not expiration_date:
            st.error("Para nivel ADMIN, debes proporcionar una fecha de expiración válida.")
        elif expiration_date and exp_date_input <= date.today():
            st.error("La fecha de expiración no puede ser hoy. Debe ser una fecha futura.")
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
            except requests.exceptions.HTTPError as e:
                try:
                    err_msg = e.response.json().get("detail", str(e))
                    if isinstance(err_msg, list):
                        msgs = [f"- {err.get('loc', [''])[-1]}: {err.get('msg', '')}" for err in err_msg]
                        st.error("Error de validación del servidor:\n" + "\n".join(msgs))
                    else:
                        st.error(f"Error devuelto por el servidor: {err_msg}")
                except Exception:
                    st.error(f"Error al crear la solicitud: {e}")
            except Exception as e:
                st.error(f"Error inesperado: {e}")
