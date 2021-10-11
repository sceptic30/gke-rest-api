
import connexion
import time
from swagger_server import maria_db, encoder
import pandas as pd
from mysql.connector import Error
from mysql.connector.errors import InterfaceError, DatabaseError
import uuid, os

def mysql_db():
    # check if the new csv file is already created. IF not, create a dataframe and add a uuid column, and auto-generate uuids for each row
    if os.path.isfile('/usr/src/app/titanic-new.csv'):
        print("Updated titanic.csv has been already created")
    else:
        csv_df = pd.read_csv('/usr/src/app/titanic.csv', index_col=False, delimiter = ',')
        csv_df["uuid"] = ""
        csv_df['uuid'] = [uuid.uuid4() for _ in range(len(csv_df.index))]
        #Reorganized dataframe colums with the exact output order as shown in Swagger UI
        csv_df = csv_df[['Age','Fare','Name','Parents/Children Aboard','Pclass','Sex','Siblings/Spouses Aboard','Survived','uuid']]
        csv_df.to_csv("/usr/src/app/titanic-new.csv")
    try:
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(db_name))
            print("{} Database is created".format(db_name))
            cursor.execute("USE {}".format(db_name))
            # check if table already exists. If not, create it
            people_tbl_sql = "SHOW TABLES LIKE '{}'".format(tbl_name)
            cursor.execute(people_tbl_sql)
            people_tbl_existance = cursor.fetchone()
            if people_tbl_existance is not None:
                print("Table \"{}\" Already Exists".format(tbl_name))
            else:
                # Database creation statement with appropriate cells and data types 
                db_creation_sql = "CREATE TABLE IF NOT EXISTS {} (`age` INT NOT NULL,`fare` FLOAT NOT NULL,`name` VARCHAR(255) NOT NULL,`parentsOrChildrenAboard` INT NOT NULL,`passengerClass` INT NOT NULL,`sex` VARCHAR(255) NOT NULL,`siblingsOrSpousesAboard` INT NOT NULL,`survived` BOOLEAN NOT NULL,`uuid` VARCHAR(36) NOT NULL);".format(tbl_name)
                print("Creating {} Table into {} Database...".format(tbl_name, db_name))
                cursor.execute(db_creation_sql)
            # Checking if tables contains any data by trying to fetch 1 single record
            select_all_rows="SELECT * FROM {}".format(tbl_name)
            cursor.execute(select_all_rows)
            people_row = cursor.fetchone()
            # Drop the Unnamed: 0 auto-created from pandas column from the created new csv file
            titanic_df = pd.read_csv('/usr/src/app/titanic-new.csv').drop(['Unnamed: 0'], axis=1)
            # If there not a single record in the table, loop through the data frame
            if people_row is None:
                # Change the cursor to prepared=True
                cursor = conn.cursor(prepared=True)
                for i, row in titanic_df.iterrows():
                    # Create the insert statement, and save it to a variable
                    initial_sql = "INSERT INTO {} VALUES (?,?,?,?,?,?,?,?,?)".format(tbl_name)
                    # Execute the insert query
                    cursor.execute(initial_sql, tuple(row))
                    print("Titanic Passenger Record Inserted")
                #Add an ID column in the front of all columns
                cursor.execute("ALTER TABLE {} ADD id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST".format(tbl_name))
                # the connection is not auto committed by default, so we must commit for the insertion to actually take place.
                conn.commit()
            else:
                print("Passenger Data Recods Already Exists. Moving On..")
    except Error as err:
        print("An unexpected error occurred while connecting to MySQL. The error was: {}".format(err))
    finally:
        if (conn.is_connected()):
            cursor.close()
            conn.close()
            print("MySQL connection is closed")
def main():
    mysql_db()
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Titanic'})
    app.run(port=8080)


if __name__ == '__main__':
    db_connected=False
    while db_connected==False: # Using a while loop for not letting the pod to crash if connection with the database has not established. If connection is not possible, the loop will conntinue to run every 1 second trying to reconnect to the database. When connection is possible, the flag db_connected changes from False to True, breaking out of the loop, and the main() function is eventually called.
        try:
            conn = maria_db.connect()
            print("Attempting Connection To MySQL Database")
            if (conn.is_connected()):   
                print("Database Connection Established")
                db_connected=True
                db_name=maria_db.db_name
                tbl_name=maria_db.tbl_name
                main()
        except InterfaceError as interf_error:
            print("Interface Error detected. The error is: {}".format(interf_error))
            time.sleep(1)
        except DatabaseError as db_error:
            print("Database Error detected. The error is: {}".format(db_error))
            time.sleep(1)