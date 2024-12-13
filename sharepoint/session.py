import time

from requests import Session
from requests.adapters import HTTPAdapter, Retry

class SharePointError(Exception):
    ...

def delay_hook(delay_seconds):
    def delay(r, *args, **kwargs):
        time.sleep(delay_seconds)
        return r
    return delay

def rise_status_hoook(r, *args, **kwargs):
    try:
        r.raise_for_status()
    except Exception as e:

        error = r.json()
        raise SharePointError(str(error)) from e
    return r

class SharepointSession(Session):
    """Modifica request.Session para agregar funcionalidad de esperar entre requests y reintentar en caso de fallar"""

    def __init__(self, delay_secs=0.01, num_retries=5, backoff_factor=0.1, status_forcelist=(500, 502, 503, 504),
                 **kwargs):
        super().__init__()

        # Agregar delays en segudos para no sobrecargar el servidor de PreviRed
        self.hooks['response'].append(delay_hook(delay_secs))

        # Agregar auto rise
        self.hooks['response'].append(rise_status_hoook)

        # Configurar retries en caso de requests fallidos
        retries = Retry(total=num_retries, backoff_factor=backoff_factor, status_forcelist=status_forcelist, **kwargs)
        adapter = HTTPAdapter(max_retries=retries)
        self.mount('http://', adapter)
        self.mount('https://', adapter)