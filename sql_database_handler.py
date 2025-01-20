import traceback
import mysql.connector
from mysql.connector import Error

class MysqlConnectionManager:
    def __init__(self, HOST, PORT, DATABASE, USER, PASSWORD):
        self.HOST = HOST
        self.PORT = PORT
        self.DATABASE = DATABASE
        self.USER = USER
        self.PASSWORD = PASSWORD
        self.dbConn_ = None

    def initConn(self):
        """Initialize a database connection."""
        try:
            self.dbConn_ = mysql.connector.connect(
                host=self.HOST,
                port=self.PORT,
                user=self.USER,
                password=self.PASSWORD,
                database=self.DATABASE,
                charset='utf8'
            )
        except Error as e:
            print(f"Error: {e}")
            raise

    def getData(self, table_name, json_data, json_where_clause=None, group_by=None, order_by=None, limit=None, logger=None):
        """Fetch data from the database."""
        sql_query = 'SELECT '
        results = []
        
        try:
            if not json_data:
                sql_query += '*'
            else:
                sql_query += ', '.join(json_data)

            sql_query += f" FROM {table_name}"

            if json_where_clause:
                sql_query += f" WHERE {json_where_clause}"

            if group_by:
                sql_query += f" GROUP BY {group_by}"

            if order_by:
                sql_query += f" ORDER BY {order_by}"

            if limit:
                sql_query += f" LIMIT {limit}"

            sql_query += ' ;'

            if logger:
                logger.info(f'Executing query: {sql_query}')

            self.initConn()
            cursor = self.dbConn_.cursor()
            cursor.execute(sql_query)
            column_names = [column[0] for column in cursor.description]
            records = cursor.fetchall()

            for record in records:
                results.append(dict(zip(column_names, record)))

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            if logger:
                logger.exception(e)
        finally:
            self.closeConn()
        return results

    def insertData(self, tableName, jsonObjData, logger=None):
        """Insert data into the table."""
        try:
            self.initConn()
            escaped_qoutes = {}
            for col, val in jsonObjData.items():
                if isinstance(val, str):
                    escaped_qoutes[col] = val.replace("'", "\\'")
                else:
                    escaped_qoutes[col] = val
            columns = ', '.join(escaped_qoutes.keys())
            values = ', '.join([f"'{v}'" for v in escaped_qoutes.values()])
            insert_query = f"INSERT INTO {tableName} ({columns}) VALUES ({values})"
            if logger is not None:
                logger.debug(f"insert query: {insert_query}")

            cursor = self.dbConn_.cursor()
            cursor.execute(insert_query)
            self.dbConn_.commit()
            return cursor.lastrowid

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            if logger:
                logger.exception(e)
            return False
        finally:
            self.closeConn()

    def deleteData(self, tableName, whereClause, logger=None):
        """Delete data from the table."""
        try:
            self.initConn()

            select_query = f"SELECT * FROM {tableName} WHERE {whereClause}"
            delete_query = f"DELETE FROM {tableName} WHERE {whereClause}"

            cursor = self.dbConn_.cursor()
            cursor.execute(select_query)
            records = cursor.fetchall()

            if not records:
                if logger:
                    logger.info(f"No records found for the query: {select_query}")
                return True  # No data to delete

            cursor.execute(delete_query)
            self.dbConn_.commit()

            return cursor.rowcount > 0

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            if logger:
                logger.exception(e)
            return False
        finally:
            self.closeConn()

    def updateData(self, table_name, column_values, condition, logger=None):
        """Update data in the table."""
        try:
            # initialize the mysql connection
            self.initConn()
            escaped_qoutes = {}
            for col, val in column_values.items():
                if isinstance(val, str):
                    escaped_qoutes[col] = val.replace("'", "\\'")
                else:
                    escaped_qoutes[col] = val
            # create set statement
            set_clause = ", ".join([f"{col} = '{val}'" if isinstance(val, str) else
                                    f"{col} = {val}" if isinstance(val, int) else
                                    f"{col} = {'TRUE' if val else 'FALSE'}" for col, val in escaped_qoutes.items()])
            update_query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
            if logger:
                logger.info(f"update_query {update_query}.")
            cursor = self.dbConn_.cursor()
            cursor.execute(update_query)
            self.dbConn_.commit()
            if logger:
                logger.debug(f"Record updated successfully in table {table_name}.")
            return cursor.rowcount > 0

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            if logger:
                logger.exception(e)
            return False
        finally:
            self.closeConn()

    def closeConn(self):
        """Close the database connection."""
        if self.dbConn_:
            self.dbConn_.commit()
            self.dbConn_.close()
            self.dbConn_ = None
