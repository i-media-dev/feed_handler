from handler.xml_saver import XMLSaver

from handler.feeds import FEEDS
from handler.constants import FEEDS_FOLDER


def main():
    save = XMLSaver(FEEDS, FEEDS_FOLDER)
    save.save_xml()


if __name__ == '__main__':
    main()
