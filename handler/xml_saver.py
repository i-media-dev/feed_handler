import os
from pathlib import Path
from dotenv import load_dotenv
import requests
# import xml.etree.ElementTree as ET


class XMLSaver():
    load_dotenv()

    def __init__(self, feeds_list: list[str], feeds_folder: str) -> None:
        self.feeds_list = feeds_list
        self.feeds_folder = feeds_folder

    def _get_file(self, feed: str):
        try:
            response = requests.get(feed)

            if response.status_code == 200:
                return response

            if response.status_code == 401:
                username = os.getenv('XML_FEED_USERNAME')
                password = os.getenv('XML_FEED_PASSWORD')
                auth_response = requests.get(
                    feed,
                    auth=(username, password)
                )

                if auth_response.status_code == 200:
                    return auth_response
                else:
                    print(f'Ошибка авторизации: {auth_response.status_code}')
                    return None
        except requests.RequestException as e:
            print(f'Ошибка при загрузке {feed}: {e}')
            return None

    def _get_filename(self, feed: str) -> str:
        return feed.split('/')[-1]

    def save_xml(self) -> None:
        folder_path = Path(__file__).parent.parent / self.feeds_folder
        folder_path.mkdir(parents=True, exist_ok=True)
        for feed in self.feeds_list:
            file_name = self._get_filename(feed)
            file_path = folder_path / file_name

            if file_path.is_file():
                print(f'Файл {file_name} уже существует.')
                continue

            response = self._get_file(feed)

            if response is None:
                continue
            try:
                with open(file_path, 'wb') as file:
                    for chunk in response.iter_content(
                        chunk_size=8192
                    ):
                        file.write(chunk)
            except IOError as e:
                print(f'Ошибка при записи файла {file_name}: {e}')
        print('Файлы успешно записаны.')
