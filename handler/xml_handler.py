import logging
import numpy as np
import xml.etree.ElementTree as ET
from datetime import datetime as dt, timedelta
from pathlib import Path
from collections import defaultdict
from handler.decorators import time_of_function
from handler.logging_config import setup_logging
from handler.feeds import FEEDS
from handler.constants import (
    DECIMAL_ROUNDING,
    FEEDS_FOLDER,
    PARSE_FEEDS_FOLDER
)
import json
import os

setup_logging()


class XMLHandler:
    """
    Класс, предоставляющий интерфейс
    для обработки xml-файлов.
    """

    def __init__(
        self,
        feeds_folder: str = FEEDS_FOLDER,
        new_feeds_folder: str = PARSE_FEEDS_FOLDER,
        feeds_list: list[str] = FEEDS
    ) -> None:
        self.feeds_folder = feeds_folder
        self.new_feeds_folder = new_feeds_folder
        self.feeds_list = feeds_list

    def _get_filenames_list(self, feeds_list):
        """Защищенный метод, возвращает список названий фидов."""
        return [feed.split('/')[-1] for feed in feeds_list]

    def _make_dir(self):
        """Защищенный метод, создает директорию."""
        file_path = Path(__file__).parent.parent / self.new_feeds_folder
        logging.debug(f'Путь к файлу: {file_path}')
        file_path.mkdir(parents=True, exist_ok=True)
        return file_path

    def _get_tree(self, file_name: str):
        """Защищенный метод, создает экземпляра класса ElementTree."""
        file_path = (
            Path(__file__).parent.parent / self.feeds_folder / file_name
        )
        logging.debug(f'Путь к файлу: {file_path}')
        return ET.parse(file_path)

    def _indent(self, elem, level=0) -> None:
        """Защищенный метод, расставляет правильные отступы в XML файлах."""
        i = '\n' + level * '  '
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + '  '
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent(child, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def _format_xml(self, elem, file_path) -> None:
        """Защищенный метод, сохраняет отформатированные файлы."""
        root = elem
        self._indent(root)
        formatted_xml = ET.tostring(root, encoding='unicode')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_xml)

    def _super_feed(self, feeds_list: list[str] = FEEDS):
        """Защищенный метод, создает шаблон фида с пустыми offers."""
        file_names: list[str] = self._get_filenames_list(feeds_list)
        first_file_tree = self._get_tree(file_names[0])
        root = first_file_tree.getroot()
        offers = root.find('.//offers')
        if offers is not None:
            offers.clear()
        return root, offers

    def _collect_all_offers(self, file_names: list[str]) -> tuple[dict, dict]:
        """
        Защищенный метод, подсчитывает встречался ли оффер в том или ином фиде.
        """
        offer_counts: dict = defaultdict(int)
        all_offers = {}
        for file_name in file_names:
            tree = self._get_tree(file_name)
            root = tree.getroot()
            for offer in root.findall('.//offer'):
                offer_id = offer.get('id')
                if offer_id:
                    offer_counts[offer_id] += 1
                    all_offers[offer_id] = offer
        return offer_counts, all_offers

    @time_of_function
    def inner_join_feeds(self, feeds_list: list) -> bool:
        """
        Метод, объединяющий все офферы в один фид
        по принципу inner join.
        """
        file_names: list[str] = self._get_filenames_list(feeds_list)
        offer_counts, all_offers = self._collect_all_offers(file_names)
        root, offers = self._super_feed()
        for offer_id, count in offer_counts.items():
            if count == len(file_names):
                offers.append(all_offers[offer_id])
        output_path = self._make_dir() / 'inner_join_feed.xml'
        self._format_xml(root, output_path)
        logging.debug(f'Файл создан по адресу: {output_path}')
        return True

    @time_of_function
    def full_outer_join_feeds(self, feeds_list: list) -> bool:
        """
        Метод, объединяющий все офферы в один фид
        по принципу full outer join.
        """
        file_names: list[str] = self._get_filenames_list(feeds_list)
        _, all_offers = self._collect_all_offers(file_names)
        root, offers = self._super_feed()
        for offer in all_offers.values():
            offers.append(offer)
        output_path = self._make_dir() / 'full_outer_join_feed.xml'
        self._format_xml(root, output_path)
        logging.debug(f'Файл создан по адресу: {output_path}')
        return True

    @time_of_function
    def process_feeds(
        self,
        feeds_list: list,
        custom_label: dict[str, dict],
        offers_id_list: list[str],
        flag: str = 'false'
    ) -> bool:
        """
        Метод, подставляющий в фиды данные
        из настраиваемого словаря CUSTOM_LABEL.
        """
        try:
            for file_name in self._get_filenames_list(feeds_list):
                tree = self._get_tree(file_name)
                root = tree.getroot()
                for offer in root.findall('.//offer'):
                    offer_name_text = offer.findtext('name')
                    offer_url_text = offer.findtext('url')
                    offer_id = offer.get('id')
                    if None in (
                        offer_name_text,
                        offer_url_text,
                        offer_id
                    ):
                        continue
                    if offer_id in offers_id_list:
                        offer.set('available', flag)
                    existing_nums = set()
                    for el in offer.findall('*'):
                        if el.tag.startswith('custom_label_'):
                            try:
                                existing_nums.add(int(el.tag.split('_')[-1]))
                            except ValueError:
                                continue
                    for label_name, conditions in custom_label.items():
                        name_match = any(
                            sub.lower() in offer_name_text.lower()
                            for sub in conditions.get('name', [])
                        )
                        url_match = any(
                            sub.lower() in offer_url_text.lower()
                            for sub in conditions.get('url', [])
                        )
                        id_match = offer_id in conditions.get('id', [])
                        if name_match or url_match or id_match:
                            next_num = 0
                            while next_num in existing_nums:
                                next_num += 1
                            existing_nums.add(next_num)
                            ET.SubElement(
                                offer, f'custom_label_{next_num}'
                            ).text = label_name
                output_path = self._make_dir() / f'new_{file_name}'
                self._format_xml(root, output_path)
                logging.debug(f'Файл записан по адресу: {output_path}')
            return True
        except Exception as e:
            logging.error(f'Произошла ошибка: {e}')
            return False

    def get_offers_report(self, feeds_list: list[str] = FEEDS) -> list[dict]:
        """Метод, формирующий отчет по офферам."""
        result = []
        date_str = (dt.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        for file_name in self._get_filenames_list(feeds_list):
            tree = self._get_tree(file_name)
            root = tree.getroot()

            for category in root.findall('.//category'):
                price_list = []
                offers_list = []
                category_id = category.get('id')

                for offer in root.findall(
                    f".//offer[categoryId='{category_id}']"
                ):
                    price = offer.findtext('price')
                    price_list.append(int(price))
                    offers_list.append(offer)

                result.append({
                    'date': date_str,
                    'feed_name': file_name,
                    'category_id': category_id,
                    'count_offers': len(offers_list),
                    'min_price': min(price_list) if price_list else 0,
                    'max_price': max(price_list) if price_list else 0,
                    'avg_price': round(
                        sum(price_list) / len(price_list), DECIMAL_ROUNDING
                    ) if price_list else 0,
                    'median_price': round(
                        np.median(price_list), DECIMAL_ROUNDING
                    ) if price_list else 0
                })
        return result

    def save_to_json(
        self,
        data: list,
        prefix: str = 'offers_report',
        folder: str = 'data'
    ) -> None:
        """Отладочный метод сохраняет данные в файл формата json."""
        logging.debug('Сохранение файла...')
        os.makedirs(folder, exist_ok=True)
        date_str = (dt.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        filename = os.path.join(folder, f'{prefix}_{date_str}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f'✅ Данные сохранены в {filename}')
        logging.debug('Файл сохранен.')
