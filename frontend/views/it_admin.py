import streamlit as st

def page_it_admin_dashboard():
    st.title("Provisionamiento de Accesos")
    client = st.session_state.client
    
    try:
        all_requests = client.get_requests()
        provision_requests = [req for req in all_requests if req["status"] in ["READY_FOR_PROVISIONING", "COMPLETED"]]
        
        if not provision_requests:
            st.info("No hay solicitudes listas para provisionar.")
            return
            
        for req in provision_requests:
            is_completed = req["status"] == "COMPLETED"
            icon = "✅" if is_completed else "⚙️"
            with st.expander(f"{icon} {req['target_system']} - {req['access_level']} (Usuario: {req['requester_id']})"):
                st.write(f"**ID Solicitud:** `{req['id']}`")
                st.write(f"**Nivel de Acceso:** `{req['access_level']}`")
                st.write(f"**Sistema:** `{req['target_system']}` ({req['system_type']})")
                st.write(f"**Justificación:** {req['justification']}")
                st.write(f"**Estado:** `{req['status']}`")
                
                if not is_completed:
                    st.divider()
                    if st.button("Completar Provisioning", key=f"btn_prov_{req['id']}", type="primary"):
                        try:
                            client.provision_request(req['id'])
                            st.success(f"Provisionamiento completado para la solicitud {req['id']}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al completar provisioning: {e}")
                            
    except Exception as e:
        st.error(f"Error al obtener las solicitudes: {e}")
