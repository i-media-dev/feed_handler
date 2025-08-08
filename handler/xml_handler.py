import xml.etree.ElementTree as ET
from pathlib import Path


class XMLHandler():

    def _indent(self, elem, level=0) -> None:
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent(child, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def format_xml(self, elem, file_path):
        root = elem
        self._indent(root)
        formatted_xml = ET.tostring(root, encoding='unicode')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_xml)

    def make_offers_unavailable(self, tree, offers_id_list, XML_file_name):
        file_path = Path(__file__).parent.parent / 'new_feeds'
        file_path.mkdir(parents=True, exist_ok=True)
        try:
            root = tree.getroot()
            for offer in root.findall('.//offer'):
                offer_id = offer.get('id')

                if offer_id and offer_id in offers_id_list:
                    offer.set('available', 'false')
            tree.write(
                f'{file_path}/{XML_file_name}',
                encoding='utf-8',
                xml_declaration=True
            )
            return True

        except Exception as e:
            print(f'Произошла ошибка: {e}')
            return False
