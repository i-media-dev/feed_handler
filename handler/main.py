from handler.xml_saver import XMLSaver

from handler.feeds import FEEDS
from handler.constants import FEEDS_FOLDER


def main():
    saver = XMLSaver(FEEDS, FEEDS_FOLDER)
    saver.save_xml()


if __name__ == '__main__':
    main()
