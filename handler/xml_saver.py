import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET

from handler.logging_config import setup_logging
from handler.exceptions import EmptyXMLError, InvalidXMLError


setup_logging()


class XMLSaver():
    load_dotenv()

    def __init__(
        self,
        feeds_list: list[str],
        feeds_folder: str = 'temp_feeds'
    ) -> None:
        if not feeds_list:
            logging.error('Не передан список фидов.')
            raise ValueError('List of feeds is required.')

        self.feeds_list = feeds_list
        self.feeds_folder = feeds_folder

    def _get_file(self, feed: str):
        try:
            response = requests.get(feed)

            if response.status_code == requests.codes.ok:
                return response

            if response.status_code == requests.codes.unauthorized:
                username = os.getenv('XML_FEED_USERNAME')
                password = os.getenv('XML_FEED_PASSWORD')
                auth_response = requests.get(
                    feed,
                    auth=(username, password)
                )

                if auth_response.status_code == requests.codes.ok:
                    return auth_response
                else:
                    logging.error(
                        f'Ошибка авторизации: {auth_response.status_code}')
                    return None
        except requests.RequestException as e:
            logging.error(f'Ошибка при загрузке {feed}: {e}')
            return None

    def _get_filename(self, feed: str) -> str:
        return feed.split('/')[-1]

    def _chek_syntax(self, str_feed):
        try:
            ET.fromstring(str_feed)
            return True
        except ET.ParseError:
            return False

    def _chek_empty(self, str_feed):
        return not bool(str_feed.strip())

    def _validate_xml(self, str_feed):
        if self._chek_empty(str_feed):
            raise EmptyXMLError('XML пуст')
        if not self._chek_syntax(str_feed):
            raise InvalidXMLError('XML содержит синтаксические ошибки')
        try:
            root = ET.fromstring(str_feed)
            if not list(root):
                raise InvalidXMLError('XML содержит только корневой элемент')
        except ET.ParseError as e:
            raise ValueError(f'Ошибка при анализе XML: {str(e)}')

    def save_xml(self) -> None:
        total_files: int = len(self.feeds_list)
        saved_files = 0
        folder_path = Path(__file__).parent.parent / self.feeds_folder
        folder_path.mkdir(parents=True, exist_ok=True)
        for feed in self.feeds_list:
            file_name = self._get_filename(feed)
            file_path = folder_path / file_name
            response = self._get_file(feed)
            encoding = response.text.split('>')[0].split('=')[-1].strip('?"\'')
            logging.info(f'Кодировка XML-файла {file_name}: {encoding}')
            logging.info(
                'Автоматическое определение кодировки '
                f'XML-фала {file_name}: {response.encoding}'
            )

            if response is None:
                logging.warning(f'XML-файл {file_name} не получен.')
                continue
            self._validate_xml(response.text)

            try:
                with open(file_path, 'wb') as file:
                    for chunk in response.iter_content(
                        chunk_size=8192
                    ):
                        file.write(chunk)
                saved_files += 1
            except IOError as e:
                logging.error(f'Ошибка при записи файла {file_name}: {e}')
        logging.info(
            f'Успешно записано {saved_files} файлов из {total_files}.')
