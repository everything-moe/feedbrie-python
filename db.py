import logging
import MySQLdb as mariadb
import time
import datetime as dt

log = logging.getLogger("chatbot")

BRIES_ID = "436478155"

def connect():
    try:
        # Should probably move the credentials to a config
        mariadb_connection = mariadb.connect(host="localhost", user='brie', password='3th3rn3t', db='Brie', autocommit=True)
        return mariadb_connection
    except mariadb.Error as error:
        log.error(f"Failed to connect to the MariaDB server: {error}")
        raise

connection = connect()

def query(sql):
    global connection
    try:
      cursor = connection.cursor()
      cursor.execute(sql)
    except (AttributeError, mariadb.OperationalError):
      connection = connect()
      cursor = connection.cursor()
      cursor.execute(sql)
    return cursor

async def dict_query(sql):
    global connection
    try:
      dict_cursor = connection.cursor(mariadb.cursors.DictCursor)
      dict_cursor.execute(sql)
    except (AttributeError, mariadb.OperationalError):
      connection = connect()
      dict_cursor = connection.cursor(mariadb.cursors.DictCursor)
      dict_cursor.execute(sql)
    return dict_cursor

class DatabaseException(Exception):
    def __init__(self, message="This is a generic database error."):
        self.message = message

class InvalidFieldException(Exception):
    def __init__(self, field, table="users"):
        self.message = f"{field} is not a valid column in the {table} table!"

class NonBooleanTypeException(Exception):
    def __init__(self, message="The passed variable must be of type boolean!"):
        self.message = message

class InvaludUserIdTypeException(Exception):
    def __init__(self, user_id, reason):
        self.message = f"{user_id} is not a valid user id because: {reason}"

class Database():
    
    @staticmethod
    def user_id_check(user_id):

        if isinstance(user_id, str):
            if len(user_id) > 100:
                raise InvaludUserIdTypeException(user_id=user_id, reason="Max ID length is 100 characters")
        else:
            raise InvaludUserIdTypeException(user_id=user_id, reason="Non-string type.")

    def __get_table_fields(table):

        __sql = f"SHOW COLUMNS FROM {table}"
        fields = []
        try:
            cursor = query(__sql)
            res = cursor.fetchall()
            for field in res:
                fields.append(field[0])
            return fields
        except mariadb.Error as error:
            log.error(f"Failed to get table columns: {error}")
            raise

    __user_table_fields = __get_table_fields("users")

    @staticmethod
    async def create_new_user(user_id, username):
        '''
        Creates new user entry with default values from config.
        '''

        global connection
        try:
            Database.user_id_check(user_id)
            now = time.time()
            now = dt.datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")

            # By not updating last_fed_brie_timestamp it inherits the default value defined by the table schema.
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO users (username,user_id,affection,bond_level,bonds_available,has_feather,has_brush,has_scratcher,free_feed,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", 
                    (username,user_id,0,0,0,0,0,0,0,now,now)
                )
            except (AttributeError, mariadb.OperationalError):
                connection = connect()
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO users (username,user_id,affection,bond_level,bonds_available,has_feather,has_brush,has_scratcher,free_feed,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", 
                    (username,user_id,0,0,0,0,0,0,0,now,now)
                )
            return cursor
        except (mariadb.Error, InvaludUserIdTypeException) as error:
            log.error(f"Failed to create new user: {error}")
            raise

    @staticmethod
    async def set_value(index, val_name, val):
        if val_name not in Database.__user_table_fields: raise InvalidFieldException(field=val_name)

        __sql = f"UPDATE users SET {val_name} = {val} WHERE user_id = {index}"

        try:
            Database.user_id_check(index)
            cursor = query(__sql)
        except (mariadb.Error, InvaludUserIdTypeException) as error:
            log.error(f"Failed to set {val_name} to {val} for user_id: {index} \n {error}")
            raise

    @staticmethod
    async def add_value(index, val_name, val):
        if val_name not in Database.__user_table_fields: raise InvalidFieldException(field=val_name)

        __sql = f"UPDATE users SET {val_name} = {val_name} + {val} WHERE user_id = {index}"

        try:
            Database.user_id_check(index)
            cursor = query(__sql)
        except (mariadb.Error, InvaludUserIdTypeException) as error:
            log.error(f"Failed to set {val_name} to {val} for user_id: {index} \n {error}")
            raise

    @staticmethod
    async def remove_value(index, val_name, val):
        if val_name not in Database.__user_table_fields: raise InvalidFieldException(field=val_name)

        __sql = f"UPDATE users SET {val_name} = {val_name} - {val} WHERE user_id = {index}"

        try:
            Database.user_id_check(index)
            cursor = query(__sql)
        except (mariadb.Error, InvaludUserIdTypeException) as error:
            log.error(f"Failed to set {val_name} to {val} for user_id: {index} \n {error}")
            raise

    @staticmethod
    async def get_value(index, val_name):
        if val_name not in Database.__user_table_fields: raise InvalidFieldException(field=val_name)

        __sql = f"SELECT {val_name} FROM users WHERE user_id = {index}"

        try:
            Database.user_id_check(index)
            cursor = query(__sql)
            res = cursor.fetchall()
            return res[0][0]
        except (mariadb.Error, InvaludUserIdTypeException) as error:
            log.error(f"Failed to get {val_name} for user_id: {index} \n {error}")
            raise

    @staticmethod
    async def get_column(val_name):
        if val_name not in Database.__user_table_fields: raise InvalidFieldException(field=val_name)

        __sql = f"SELECT {val_name} FROM users"

        try:
            cursor = query(__sql)
            res = cursor.fetchall()
            out = [data[0] for data in res]
            return out
        except (mariadb.Error, InvaludUserIdTypeException) as error:
            log.error(f"Failed to get {val_name} column \n {error}")
            raise

    @staticmethod
    async def get_top_rows_by_column(col_name, order_name, limit):            
        return await Database.get_top_rows_by_column_exclude_uid(col_name, order_name, limit)

    @staticmethod
    async def get_top_rows_by_column_exclude_uid(col_name, order_name, limit, uid = None):
        if col_name not in Database.__user_table_fields: raise InvalidFieldException(field=col_name)

        if uid is None:
            __sql = f"SELECT {col_name} FROM users ORDER BY {order_name} DESC LIMIT {limit}"
        else:
            __sql = f"SELECT {col_name} FROM users WHERE user_id != {uid} ORDER BY {order_name} DESC LIMIT {limit}"

        try:
            cursor = query(__sql)
            res = cursor.fetchall()
            out = [data[0] for data in res]
            return out
        except (mariadb.Error, InvalidFieldException) as error:
            log.error(f"Failed to grab {col_name} ordered by {order_name} column \n {error}")
            raise

    #########################
    #                       #
    #       Helpers         #
    #                       #
    #########################

    @staticmethod
    async def get_created_timestamp(user_id):
        '''
        Returns timestamp for when the user entry was created.
        '''
        return await Database.get_value(user_id, "created_at")

    @staticmethod
    async def get_updated_timestamp(user_id):
        '''
        Returns the last time the given User's entry was updated.
        '''
        return await Database.get_value(user_id, "updated_at")

    @staticmethod
    async def set_fed_brie_timestamp(user_id, fed_timestamp=dt.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")):
        '''
        Updates the last time a user has fed Brie.
        '''
        await Database.set_value(user_id, "last_fed_brie_timestamp", f"'{fed_timestamp}'")

    @staticmethod
    async def get_last_fed_timestamp(user_id):
        '''
        Returns timestamp of User's last feeding.
        '''
        return await Database.get_value(user_id, "last_fed_brie_timestamp")

    @staticmethod
    async def get_brie_happiness():
        '''
        Returns the current level of happiness for Brie.
        '''
        output = await Database.get_value(BRIES_ID, "bond_level")
        # perhaps should do some formula to keep this on a 0-100 scale?
        return output

async def do_decay():

    __sql = f"""
            UPDATE users 
            SET free_feed = 0,
                bonds_available = 0, 
                affection = 
                    CASE 
                        WHEN last_fed_brie_timestamp <= NOW() - INTERVAL 1 DAY AND affection > 5 THEN affection - 5
                        WHEN last_fed_brie_timestamp >= NOW() - INTERVAL 1 DAY AND affection > 1 THEN affection - 1
                        WHEN last_fed_brie_timestamp <= NOW() - INTERVAL 1 DAY AND affection <= 0 THEN 0
                        WHEN last_fed_brie_timestamp >= NOW() - INTERVAL 1 DAY AND affection <= 0 THEN 0
                        ELSE affection
                    END,
                bond_level = 
                    CASE 
                        WHEN last_fed_brie_timestamp <= NOW() - INTERVAL 1 DAY AND bond_level > 5 THEN bond_level - 5
                        WHEN last_fed_brie_timestamp >= NOW() - INTERVAL 1 DAY AND bond_level > 1 THEN bond_level - 1
                        WHEN last_fed_brie_timestamp <= NOW() - INTERVAL 1 DAY AND bond_level <= 0 THEN 0
                        WHEN last_fed_brie_timestamp >= NOW() - INTERVAL 1 DAY AND bond_level <= 0 THEN 0
                        ELSE affection
                    END
            WHERE user_id != {BRIES_ID};
            """
    try:
        cursor = query(__sql)
        res = cursor.fetchall()
        log.info("Decayed affection and bond_level values in the database!")
    except (mariadb.Error) as error:
        log.error(f"Failed to decay affection and bond_level values! {error}")

async def do_calc_happiness():    
    happiness = 0
    
    old_happiness = await Database.get_value(BRIES_ID, "bond_level")

    __sql = f"SELECT bond_level FROM users WHERE user_id != {BRIES_ID}"
    
    dict_cursor = await dict_query(__sql)
    results = dict_cursor.fetchall()

    for res in results:
        bond_level = int(res["bond_level"])
        if bond_level > 100:
            happiness += 100
        else:
            happiness += bond_level

    await Database.set_value(BRIES_ID, "bond_level", happiness)
    log.info(f"Recalculated happiness! OLD: {old_happiness} NEW: {happiness}")
    
    await do_decay()
