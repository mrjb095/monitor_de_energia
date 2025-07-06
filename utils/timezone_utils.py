from datetime import datetime, timezone, timedelta

def utc_to_local(utc_str):
    if utc_str:
        utc_dt = datetime.strptime(utc_str, '%Y-%m-%d %H:%M:%S')
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        local_dt = utc_dt.astimezone()
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    return None

def local_to_utc(local_str):
    if local_str:
        local_dt = datetime.strptime(local_str, '%Y-%m-%d %H:%M:%S')
        utc_dt = local_dt + timedelta(hours=3)  # Ajuste para seu fuso (ex: Brasil -3h)
        return utc_dt.strftime('%Y-%m-%d %H:%M:%S')
    return None
