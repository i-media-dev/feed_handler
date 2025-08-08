import os
import xml.etree.ElementTree as ET
from pathlib import Path
from handler.xml_saver import XMLSaver
from handler.xml_handler import XMLHandler
from handler.feeds import FEEDS
from handler.constants import FEEDS_FOLDER, UNAVAILABLE_OFFER_ID_LIST


def main():
    file_path = Path(__file__).parent.parent / \
        'temp_feeds' / 'context_msk_cl.xml'
    tree = ET.parse(file_path)
    root = tree.getroot()
    saver = XMLSaver(FEEDS, FEEDS_FOLDER)
    handler = XMLHandler()
    # saver.save_xml()

    handler.make_offers_unavailable(
        tree, UNAVAILABLE_OFFER_ID_LIST, 'new_context_msk_cl.xml')


if __name__ == '__main__':
    main()
