import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

IAM_TOKEN_URL = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'
OAUTH_TOKEN = os.getenv('YANDEX_OAUTH_TOKEN')
FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')

_cached_token = None
_token_expire = 0

class YandexIAMError(Exception):
    pass

def get_iam_token():
    """Получает IAM-токен по OAuth-токену, с кэшированием и обработкой ошибок."""
    global _cached_token, _token_expire
    now = int(time.time())
    if _cached_token and _token_expire > now + 60:  # 60 сек. запас
        return _cached_token
    if not OAUTH_TOKEN:
        raise YandexIAMError('Не задан YANDEX_OAUTH_TOKEN в .env')
    try:
        resp = requests.post(IAM_TOKEN_URL, json={'yandexPassportOauthToken': OAUTH_TOKEN})
        resp.raise_for_status()
        data = resp.json()
        _cached_token = data['iamToken']
        _token_expire = int(time.time()) + int(data.get('expiresIn', 3600))
        return _cached_token
    except Exception as e:
        raise YandexIAMError(f'Ошибка получения IAM-токена: {e}') 