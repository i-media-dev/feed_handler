from io import BytesIO
import logging
from pathlib import Path
from PIL import Image
import requests
import xml.etree.ElementTree as ET

from handler.constants import FEEDS_FOLDER, IMAGE_FOLDER, NEW_IMAGE_FOLDER
from handler.feeds import FEEDS
from handler.logging_config import setup_logging

setup_logging()


class XMLImage:
    """
    Класс, предоставляющий интерфейс
    для работы с изображениями.
    """

    def __init__(
        self,
        feeds_folder: str = FEEDS_FOLDER,
        image_folder: str = IMAGE_FOLDER,
        new_image_folder: str = NEW_IMAGE_FOLDER,
        feeds_list: list[str] = FEEDS
    ) -> None:
        self.feeds_folder = feeds_folder
        self.image_folder = image_folder
        self.new_image_folder = new_image_folder
        self.feeds_list = feeds_list

    def _get_filenames_list(self) -> list[str]:
        """Защищенный метод, возвращает список названий фидов."""
        return [feed.split('/')[-1] for feed in self.feeds_list]

    def _get_tree(self, file_name: str):
        """Защищенный метод, создает экземпляра класса ElementTree."""
        file_path = (
            Path(__file__).parent.parent / self.feeds_folder / file_name
        )
        logging.debug(f'Путь к файлу: {file_path}')
        return ET.parse(file_path)

    def _make_dir(self, image_folder) -> str:
        """Защищенный метод, создает директорию."""
        folder_path = Path(__file__).parent.parent / image_folder
        logging.debug(f'Путь к файлу: {folder_path}')
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    def _get_image_filename(self, offer_id: str, url: str) -> str:
        """Защищенный метод, создает имя файла с изображением."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            image_format = image.format.lower() if image.format else None
            return f'{offer_id}.{image_format}'
        except Exception as e:
            print(f'Ошибка при обработке изображения {url}: {e}')
            logging.error(f'Ошибка при обработке изображения {url}: {e}')
        return ''

    def _save_image(self, url: str, folder_path: Path, image_filename: str):
        """Защищенный метод, сохраняет изображение по указанному пути."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            with Image.open(BytesIO(response.content)) as img:
                file_path = folder_path / image_filename
                img.load()
                img.save(file_path)
        except requests.RequestException as e:
            logging.error(f'Ошибка при загрузке {url}: {e}')
        except Exception as e:
            logging.error(f'Ошибка при обработке изображения {url}: {e}')

    def get_images(self):
        """Метод получения и сохранения изображений из xml-файла."""
        for file_name in self._get_filenames_list():
            tree = self._get_tree(file_name)
            root = tree.getroot()
            for offer in root.findall('.//offer'):
                offer_id = offer.get('id')
                offer_image = offer.findtext('picture')
                if not offer_image:
                    logging.warning(f'Offer {offer_id} не имеет изображения')
                    continue
                image_filename = self._get_image_filename(
                    offer_id,
                    offer_image
                )
                folder_path = self._make_dir(self.image_folder)
                self._save_image(offer_image, folder_path, image_filename)
