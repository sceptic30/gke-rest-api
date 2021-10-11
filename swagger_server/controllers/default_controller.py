from logging import ERROR
import connexion
from swagger_server.models.person_data import PersonData  # noqa: E501
from swagger_server import maria_db
from swagger_server.maria_db import tbl_name
from mysql.connector import Error
import uuid


def convert_bool(result):
    for index in range(len(result)):
        if result[index]['survived'] == 0:
            result[index]['survived'] = False
        elif result[index]['survived'] == 1:
            result[index]['survived'] = True


def people_list():  # noqa: E501
    """Get a list of all people

     # noqa: E501

    :rtype: People
    """
    try:
        conn = maria_db.connect()
        if conn.is_connected():
            cursor = conn.cursor(prepared=True)
            select_all= "SELECT `age`,`fare`,`name`,`parentsOrChildrenAboard`,`passengerClass`,`sex`,`siblingsOrSpousesAboard`,`survived`,`uuid` FROM {tbl_name}".format(tbl_name=tbl_name)
            cursor.execute(select_all)
            results = cursor.fetchall()
            result = [dict(zip(cursor.column_names, result)) for result in results]
            convert_bool(result)
    except Error as err:
        print("Error while connecting to MySQL. The error was:{}".format(err))
    return result


def person_get(uuid):  # noqa: E501
    """Get information about one person

     # noqa: E501

    :param uuid: 
    :type uuid: 

    :rtype: Person
    """
    try:
        conn = maria_db.connect()
        if conn.is_connected():
            cursor = conn.cursor(prepared=True)
            get_person = "SELECT age,fare,name,parentsOrChildrenAboard,passengerClass,sex,siblingsOrSpousesAboard,survived,uuid FROM {tbl_name} WHERE uuid = ?".format(tbl_name=tbl_name)
            cursor.execute(get_person, (uuid,) )
            result = cursor.fetchone()
            if result is None:
                return 'Not found', 404
            elif result:
                result = [dict(zip(cursor.column_names, result))]
                convert_bool(result)
    except Error as err:
        print("Error while connecting to MySQL. The error was:{}".format(err))
    return result


def people_add(person):  # noqa: E501
    """Add a person to the database

     # noqa: E501

    :param person: 
    :type person: dict | bytes

    :rtype: Person
    """
    if connexion.request.is_json:
        person = PersonData.from_dict(connexion.request.get_json())  # noqa: E501
    try:
        conn = maria_db.connect()
        if conn.is_connected():
            cursor = conn.cursor(prepared=True)
            add_person = "INSERT INTO {tbl_name} (age,fare,name,parentsOrChildrenAboard,passengerClass,sex,siblingsOrSpousesAboard,survived,uuid) VALUES (?,?,?,?,?,?,?,?,?)".format(tbl_name=tbl_name)

            person_data = person.age,person.fare,person.name,person.parents_or_children_aboard,person.passenger_class,person.sex,person.siblings_or_spouses_aboard,person.survived,str(uuid.uuid4())
            cursor.execute(add_person, person_data)
            conn.commit()
            cursor.execute("SELECT age,fare,name,parentsOrChildrenAboard,passengerClass,sex,siblingsOrSpousesAboard,survived,uuid FROM {tbl_name} ORDER BY id DESC LIMIT 1;".format(tbl_name=tbl_name))
            result = cursor.fetchone()
            result = [dict(zip(cursor.column_names, result))]
            convert_bool(result)
    except Error as err:
        print("Error while connecting to MySQL. The error was:{}".format(err))
    return result
    

def person_update(uuid, person):  # noqa: E501
    """Update information about one person

     # noqa: E501

    :param uuid: 
    :type uuid: 
    :param person: 
    :type person: dict | bytes

    :rtype: Person
    """
    if connexion.request.is_json:
        person = PersonData.from_dict(connexion.request.get_json())  # noqa: E501
    try:
        conn = maria_db.connect()
        if conn.is_connected():
            cursor = conn.cursor(prepared=True)
            find_uuid = "SELECT uuid FROM {tbl_name} WHERE uuid = ?".format(tbl_name=tbl_name)
            cursor.execute(find_uuid, (uuid,))
            result = cursor.fetchone()
            if result is None:
                return 'Not found', 404
            elif result:
                update_person = "UPDATE {tbl_name} SET age=?,fare=?,name=?,parentsOrChildrenAboard=?,passengerClass=?,sex=?,siblingsOrSpousesAboard=?,survived=? WHERE uuid = ?".format(tbl_name=tbl_name)
                # Since person_update() function accepts 2 parameters, and using a prepared statement we must pass uuid and person details as a tuple. Tuple values are taken from the PersonData Class properties. 
                person_data = person.age,person.fare,person.name,person.parents_or_children_aboard,person.passenger_class,person.sex,person.siblings_or_spouses_aboard,person.survived, uuid
                cursor.execute(update_person, person_data)
                conn.commit()
    except Error as err:
        print("Error while connecting to MySQL. The error was:{}".format(err))
    return 'Updated', 200
 

def person_delete(uuid):  # noqa: E501
    """Delete this person

     # noqa: E501

    :param uuid: 
    :type uuid: 

    :rtype: None
    """
    try:
        conn = maria_db.connect()
        if conn.is_connected():
            cursor = conn.cursor(prepared=True)
            find_uuid = "SELECT uuid FROM {tbl_name} WHERE uuid = ?".format(tbl_name=tbl_name)
            cursor.execute(find_uuid, (uuid,))
            result = cursor.fetchone()
            if result is None:
                return 'Not found', 404
            elif result:
                delete_person = "DELETE FROM {tbl_name} WHERE uuid = ?".format(tbl_name=tbl_name)
                cursor.execute(delete_person, (uuid,))
                conn.commit()
    except Error as err:
        print("Error while connecting to MySQL. The error was:{}".format(err))
    return ('OK', 200)