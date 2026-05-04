from datetime import datetime, timedelta, timezone

def format_local_date(date_str: str) -> str:
    """Convierte una fecha ISO UTC a la hora local de Ecuador (UTC-5) y la formatea."""
    if not date_str:
        return ""
    try:
        clean_str = str(date_str).replace('Z', '+00:00')
        dt_utc = datetime.fromisoformat(clean_str)
        tz_ecuador = timezone(timedelta(hours=-5))
        dt_local = dt_utc.astimezone(tz_ecuador)
        return dt_local.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(date_str)[:19].replace('T', ' ')
