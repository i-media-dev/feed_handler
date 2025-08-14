import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from handler.decorators import time_of_function
from handler.logging_config import setup_logging
from handler.feeds import FEEDS
from handler.constants import FEEDS_FOLDER, PARSE_FEEDS_FOLDER

setup_logging()


class XMLHandler:

    def __init__(
        self,
        feeds_folder: str = FEEDS_FOLDER,
        new_feeds_folder: str = PARSE_FEEDS_FOLDER
    ) -> None:
        self.feeds_folder = feeds_folder
        self.new_feeds_folder = new_feeds_folder

    def _get_filenames_list(self, feeds_list):
        return [feed.split('/')[-1] for feed in feeds_list]

    def _make_dir(self):
        file_path = Path(__file__).parent.parent / self.new_feeds_folder
        logging.debug(f'Путь к файлу: {file_path}')
        file_path.mkdir(parents=True, exist_ok=True)
        return file_path

    def _get_tree(self, file_name: str):
        file_path = (
            Path(__file__).parent.parent / self.feeds_folder / file_name
        )
        logging.debug(f'Путь к файлу: {file_path}')
        return ET.parse(file_path)

    def _indent(self, elem, level=0) -> None:
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
        root = elem
        self._indent(root)
        formatted_xml = ET.tostring(root, encoding='unicode')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_xml)

    def _super_feed(self, feeds_list: list[str] = FEEDS):
        file_names: list[str] = self._get_filenames_list(feeds_list)
        first_file_tree = self._get_tree(file_names[0])
        root = first_file_tree.getroot()
        offers = root.find('.//offers')
        if offers is not None:
            offers.clear()
        return root, offers

    def _collect_all_offers(self, file_names: list[str]) -> tuple[dict, dict]:
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
