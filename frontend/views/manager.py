import streamlit as st
import requests
from utils import format_local_date

def page_manager_dashboard():
    st.title("Bandeja de Aprobación - Manager")
    client = st.session_state.client
    
    try:
        all_requests = client.get_requests()
        # Filtramos por estado MANAGER_REVIEW
        pending_requests = [req for req in all_requests if req["status"] == "MANAGER_REVIEW"]
        
        if not pending_requests:
            st.info("No hay solicitudes pendientes de aprobación por el momento.")
            return
            
        for req in pending_requests:
            with st.expander(f"🟡 {req['target_system']} - {req['access_level']} (Usuario: {req['requester_id']})"):
                st.write(f"**ID Solicitud:** `{req['id']}`")
                st.write(f"**Nivel de Acceso:** `{req['access_level']}`")
                st.write(f"**Sistema:** `{req['target_system']}` ({req['system_type']})")
                st.write(f"**Justificación:** {req['justification']}")
                if req.get('expiration_date'):
                    st.write(f"**Fecha Expiración:** `{req['expiration_date']}`")
                
                st.divider()
                st.markdown("### Acciones")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✅ Aprobar", key=f"btn_approve_{req['id']}", type="primary"):
                        try:
                            client.approve_request(req['id'])
                            st.success(f"Solicitud {req['id']} aprobada correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al aprobar: {e}")
                
                with col2:
                    reason_reject = st.text_input("Motivo de rechazo", key=f"reason_reject_{req['id']}")
                    if st.button("❌ Rechazar", key=f"btn_reject_{req['id']}"):
                        if not reason_reject:
                            st.warning("Debes proporcionar un motivo para rechazar.")
                        else:
                            try:
                                client.reject_request(req['id'], reason_reject)
                                st.success(f"Solicitud {req['id']} rechazada.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al rechazar: {e}")
                
                with col3:
                    reason_changes = st.text_input("Comentario para cambios", key=f"reason_changes_{req['id']}")
                    if st.button("🔄 Solicitar Cambios", key=f"btn_changes_{req['id']}"):
                        if not reason_changes:
                            st.warning("Debes proporcionar un comentario para solicitar cambios.")
                        else:
                            try:
                                client.request_changes(req['id'], reason_changes)
                                st.success(f"Se han solicitado cambios para {req['id']}.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al solicitar cambios: {e}")
                                
                st.divider()
                if st.checkbox("Ver Historial de Auditoría", key=f"audit_{req['id']}"):
                    try:
                        logs = client.get_audit_log(req['id'])
                        if logs:
                            for log in logs:
                                st.markdown(f"- `{format_local_date(log['created_at'])}` **{log['action']}** (por {log['user_id']}): {log['details']}")
                        else:
                            st.write("No hay registros disponibles.")
                    except Exception as e:
                        st.error("No se pudo cargar el historial.")
                                
    except Exception as e:
        st.error(f"Error al obtener las solicitudes: {e}")
