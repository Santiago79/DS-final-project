import streamlit as st
from utils import format_local_date

def page_notifications():
    st.title("Mis Notificaciones")
    client = st.session_state.client
    
    unread_only = st.checkbox("Mostrar solo no leídas", value=False)
    
    try:
        notifications = client.get_notifications(unread_only=unread_only)
        
        if not notifications:
            st.info("No tienes notificaciones.")
            return
            
        for notif in notifications:
            is_unread = notif["status"] == "PENDING"
            color = "🟢" if is_unread else "⚪"
            with st.container():
                cols = st.columns([0.8, 0.2])
                with cols[0]:
                    st.markdown(f"**{color} {notif['title']}**")
                    st.write(notif['message'])
                    st.caption(f"Fecha: {format_local_date(notif['created_at'])}")
                
                with cols[1]:
                    if is_unread:
                        if st.button("Marcar como leída", key=f"read_{notif['id']}"):
                            try:
                                client.mark_notification_read(notif['id'])
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                st.divider()
                
    except Exception as e:
        st.error(f"Error al obtener notificaciones: {e}")
