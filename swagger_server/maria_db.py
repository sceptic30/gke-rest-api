from configparser import ConfigParser
import mysql.connector as msql

config = ConfigParser()
config.read('/usr/src/app/swagger_server/config.cfg')
db_name = config['MariaDB']['database']
tbl_name = config['MariaDB']['table']

def connect():
    return msql.connect(host = config['MariaDB']['host'],
                user = config['MariaDB']['user'],
                password = config['MariaDB']['password'],
                database = config['MariaDB']['database'])