import streamlit as st
import pandas as pd
from utils import format_local_date

def page_system_audit():
    st.title("Auditoría Global del Sistema")
    client = st.session_state.client
    
    try:
        logs = client.get_audit_log()
        
        if not logs:
            st.info("No hay registros de auditoría en el sistema.")
            return
            
        df = pd.DataFrame(logs)
        df = df.rename(columns={
            "created_at": "Fecha/Hora",
            "user_id": "Actor (ID)",
            "action": "Acción",
            "request_id": "ID Solicitud",
            "details": "Detalles"
        })
        
        if "Fecha/Hora" in df.columns:
            df["Fecha/Hora"] = df["Fecha/Hora"].apply(format_local_date)
            
        cols = ["Fecha/Hora", "Acción", "Actor (ID)", "ID Solicitud", "Detalles"]
        # Keep only columns that exist
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
                
    except Exception as e:
        st.error(f"Error al obtener el registro de auditoría: {e}")
