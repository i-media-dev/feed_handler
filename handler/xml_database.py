import logging

from handler.constants import CREATE_LOGS_TABLE, NAME_OF_SHOP, INSERT_LOGS
from handler.decorators import connection_db
from handler.exceptions import TableNameError
from handler.logging_config import setup_logging

setup_logging()


class XMLDataBase:
    """Класс, предоставляющий интерфейс для работы с базой данных"""

    def __init__(self, shop_name: str = NAME_OF_SHOP):
        self.shop_name = shop_name

    @connection_db
    def _allowed_tables(self, cursor=None) -> list:
        """
        Защищенный метод, возвращает список существующих
        таблиц в базе данных.
        """
        cursor.execute('SHOW TABLES')
        return [table[0] for table in cursor.fetchall()]

    @connection_db
    def _create_table_if_not_exists(self, cursor=None) -> str:
        """
        Защищенный метод, создает таблицу в базе данных, если ее не существует.
        Если таблица есть в базе данных - возварщает ее имя.
        """
        table_name = f'test_report_offers_{self.shop_name}'
        if table_name in self._allowed_tables():
            logging.info(f'Таблица {table_name} найдена в базе')
            return table_name
        create_table_query = CREATE_LOGS_TABLE.format(table_name=table_name)
        cursor.execute(create_table_query)
        logging.info(f'Таблица {table_name} успешно создана')
        return table_name

    @connection_db
    def insert_data(self, data, cursor=None) -> None:
        """Метод наполняет данными таблицу базы данных."""
        table_name = self._create_table_if_not_exists()
        query = INSERT_LOGS.format(table_name=table_name)
        params = [
            (
                item['date'],
                item['feed_name'],
                item['category_id'],
                item['parent_id'],
                item['count_offers'],
                item['min_price'],
                item['clear_min_price'],
                item['max_price'],
                item['clear_max_price'],
                item['avg_price'],
                item['median_price']
            ) for item in data
        ]
        if isinstance(params, list):
            cursor.executemany(query, params)
        else:
            cursor.execute(query, params)
        logging.info('✅ Данные успешно сохранены!')

    @connection_db
    def clean_db(self, cursor=None, **tables: bool) -> None:
        """
        Метод очищает базу данных,
        не удаляя сами таблицы
        """
        try:
            existing_tables = self._allowed_tables()
            for table_name, should_clean in tables.items():
                if should_clean and table_name in existing_tables:
                    cursor.execute(f'DELETE FROM {table_name}')
                    logging.info(f'Таблица {table_name} очищена')
                else:
                    raise TableNameError(
                        f'В базе данных отсутствует таблица {table_name}.'
                    )
        except Exception as e:
            logging.error(f'Ошибка очистки: {e}')
            raise
