import streamlit as st
import requests

def page_security_dashboard():
    st.title("Revisión de Seguridad")
    client = st.session_state.client
    
    try:
        all_requests = client.get_requests()
        # Filtramos por estado SECURITY_REVIEW
        pending_requests = [req for req in all_requests if req["status"] == "SECURITY_REVIEW"]
        
        if not pending_requests:
            st.info("No hay solicitudes que requieran revisión de seguridad por el momento.")
            return
            
        for req in pending_requests:
            with st.expander(f"🛡️ {req['target_system']} - {req['access_level']} (Usuario: {req['requester_id']})"):
                st.write(f"**ID Solicitud:** `{req['id']}`")
                st.write(f"**Nivel de Acceso:** `{req['access_level']}`")
                st.write(f"**Sistema:** `{req['target_system']}` ({req['system_type']})")
                st.write(f"**Justificación:** {req['justification']}")
                if req.get('expiration_date'):
                    st.write(f"**Fecha Expiración:** `{req['expiration_date']}`")
                
                st.divider()
                st.markdown("### Acciones de Seguridad")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Aprobar Acceso", key=f"sec_approve_{req['id']}", type="primary"):
                        try:
                            client.approve_request(req['id'])
                            st.success(f"Solicitud {req['id']} aprobada de forma segura.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al aprobar: {e}")
                
                with col2:
                    reason_reject = st.text_input("Motivo de rechazo de seguridad", key=f"sec_reason_reject_{req['id']}")
                    if st.button("❌ Rechazar Acceso", key=f"sec_reject_{req['id']}"):
                        if not reason_reject:
                            st.warning("Debes proporcionar un motivo de seguridad para rechazar.")
                        else:
                            try:
                                client.reject_request(req['id'], reason_reject)
                                st.success(f"Solicitud {req['id']} rechazada por seguridad.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al rechazar: {e}")
                                
    except Exception as e:
        st.error(f"Error al obtener las solicitudes: {e}")
