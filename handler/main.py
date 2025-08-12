import xml.etree.ElementTree as ET
# from pathlib import Path
from handler.xml_saver import XMLSaver
from handler.xml_handler import XMLHandler
from handler.feeds import FEEDS
from handler.constants import (
    CUSTOM_LABEL,
    FEEDS_FOLDER,
    UNAVAILABLE_OFFER_ID_LIST,
    PARSE_FEEDS_FOLDER
)
from handler.decorators import time_of_function


@time_of_function
def main():
    saver = XMLSaver(FEEDS)
    handler = XMLHandler()
    saver.save_xml()
    handler.process_feeds(
        FEEDS,
        CUSTOM_LABEL,
        UNAVAILABLE_OFFER_ID_LIST
    )
    handler.full_outer_join_feeds(FEEDS)
    handler.inner_join_feeds(FEEDS)


if __name__ == '__main__':
    main()
