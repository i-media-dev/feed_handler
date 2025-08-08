import xml.etree.ElementTree as ET
from pathlib import Path
from handler.xml_saver import XMLSaver
from handler.xml_handler import XMLHandler
from handler.feeds import FEEDS
from handler.constants import (
    FEEDS_FOLDER,
    UNAVAILABLE_OFFER_ID_LIST,
    PARSE_FEEDS_FOLDER
)


def main():
    saver = XMLSaver(FEEDS)
    handler = XMLHandler()
    saver.save_xml()
    handler.make_offers_unavailable(
        FEEDS,
        UNAVAILABLE_OFFER_ID_LIST,
    )


if __name__ == '__main__':
    main()
