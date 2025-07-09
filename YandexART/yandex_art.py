import os
import requests
from .yandex_iam import get_iam_token, YandexIAMError
import logging
import random
import base64
import time
from dotenv import load_dotenv

load_dotenv()

FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
IMG_MAX_SIZE_MB = int(os.getenv('IMG_MAX_SIZE_MB', 300))
IMG_DIR = os.path.join('static', 'img')

YANDEX_ART_URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync'
YANDEX_ART_RESULT_URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync/result'

logger = logging.getLogger('yandex_art')

class YandexARTError(Exception):
    pass

def save_image_to_disk(base64_img, user_id, msg_id):
    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)
    filename = f'img_{user_id}_{msg_id}.jpeg'
    filepath = os.path.join(IMG_DIR, filename)
    try:
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(base64_img))
        logger.info(f'Изображение сохранено: {filepath}')
    except Exception as e:
        logger.error(f'Ошибка при сохранении изображения {filepath}: {e}')
        return None
    # Проверяем, что файл действительно существует
    if not os.path.exists(filepath):
        logger.error(f'Файл не найден после сохранения: {filepath}')
        return None
    logger.info(f'Файл доступен для отдачи: {filepath}')
    return f'/images/{filename}'

def get_img_dir_size_mb():
    total = 0
    for root, dirs, files in os.walk(IMG_DIR):
        for file in files:
            total += os.path.getsize(os.path.join(root, file))
    return total / (1024 * 1024)

def cleanup_img_dir():
    """Удаляет самые старые изображения при превышении лимита IMG_MAX_SIZE_MB"""
    if not os.path.exists(IMG_DIR):
        return
    files = [os.path.join(IMG_DIR, f) for f in os.listdir(IMG_DIR) if os.path.isfile(os.path.join(IMG_DIR, f))]
    files = sorted(files, key=os.path.getctime)
    while get_img_dir_size_mb() > IMG_MAX_SIZE_MB and files:
        oldest = files.pop(0)
        try:
            os.remove(oldest)
            logger.info(f'Удалено изображение: {oldest}')
        except Exception as e:
            logger.error(f'Ошибка при удалении {oldest}: {e}')

def generate_image(prompt, aspect_ratio=(1,1), user_id=None, msg_id=None):
    try:
        token = get_iam_token()
    except YandexIAMError as e:
        logger.error(f'IAM error: {e}')
        raise YandexARTError(f'IAM error: {e}')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'x-folder-id': FOLDER_ID
    }
    seed = random.randint(10000, 10000000)
    width, height = aspect_ratio
    data = {
        'modelUri': f'art://{FOLDER_ID}/yandex-art/latest',
        'generationOptions': {
            'seed': str(seed),
            'aspectRatio': {
                'widthRatio': str(width),
                'heightRatio': str(height)
            }
        },
        'messages': [
            {
                'weight': '1',
                'text': prompt
            }
        ]
    }
    logger.info(f'Отправляю запрос к YandexART: {data}')
    try:
        logger.info(f'headers: {headers}')
        resp = requests.post(YANDEX_ART_URL, headers=headers, json=data, timeout=30)
        logger.info(f'Ответ на POST: {resp.text}')
        resp.raise_for_status()
        operation = resp.json()
        op_id = operation.get('id')
        logger.info(f'op_id: {op_id}')
        if not op_id:
            logger.error(f'Нет id операции в ответе: {operation}')
            raise YandexARTError('Не получен id операции')
        logger.info('Жду 10 секунд перед получением результата...')
        time.sleep(10)
        result_url = f'https://llm.api.cloud.yandex.net:443/operations/{op_id}'
        logger.info(f'GET {result_url}')
        result = requests.get(result_url, headers={'Authorization': f'Bearer {token}'})
        logger.info(f'Ответ на GET: {result.text}')
        result.raise_for_status()
        result_json = result.json()
        logger.info(f'Ответ на получение результата: {result_json}')
        if "response" in result_json:
            response = result_json["response"]
            if "image" in response:
                logger.info('Получено изображение в base64')
                if user_id and msg_id:
                    cleanup_img_dir()
                    local_url = save_image_to_disk(response["image"], user_id, msg_id)
                    return local_url
                else:
                    return response["image"]
            if "images" in response and response["images"]:
                logger.info('Получен список изображений (url)')
                return response["images"][0]
        raise YandexARTError('Нет изображения в ответе')
    except Exception as e:
        logger.error(f'Ошибка генерации изображения: {e}')
        raise YandexARTError(f'Ошибка генерации изображения: {e}') 