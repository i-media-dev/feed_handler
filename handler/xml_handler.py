import xml.etree.ElementTree as ET
from pathlib import Path


class XMLHandler():

    def __init__(
        self,
        feeds_folder: str = 'temp_feeds',
        new_feeds_folder: str = 'new_feeds'
    ) -> None:
        self.feeds_folder = feeds_folder
        self.new_feeds_folder = new_feeds_folder

    def _get_tree(self, file_name: str):
        file_path = (
            Path(__file__).parent.parent / self.feeds_folder / file_name
        )
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

    def format_xml(self, elem, file_path) -> None:
        root = elem
        self._indent(root)
        formatted_xml = ET.tostring(root, encoding='unicode')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_xml)

    def make_offers_unavailable(
        self,
        feeds_list,
        offers_id_list,
        flag='false'
    ) -> bool:
        file_path = Path(__file__).parent.parent / self.new_feeds_folder
        file_path.mkdir(parents=True, exist_ok=True)
        try:
            file_name_list = [feed.split('/')[-1] for feed in feeds_list]
            for file_name in file_name_list:
                tree = self._get_tree(file_name)
                root = tree.getroot()
                for offer in root.findall('.//offer'):
                    offer_id = offer.get('id')

                    if offer_id and offer_id in offers_id_list:
                        offer.set('available', flag)
                tree.write(
                    f'{file_path}/new_{file_name}',
                    encoding='utf-8',
                    xml_declaration=True
                )
            return True

        except Exception as e:
            print(f'Произошла ошибка: {e}')
            return False
