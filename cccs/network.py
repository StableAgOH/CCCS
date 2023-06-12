import requests
from requests.adapters import HTTPAdapter, Retry

ses = requests.Session()
retries = Retry(total=10, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
ses.mount("https://", HTTPAdapter(max_retries=retries))


def get(url: str):
    return ses.get(url, timeout=5)


def post(url: str, data):
    return ses.post(url, data, timeout=5)
