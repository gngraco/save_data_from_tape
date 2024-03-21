"""Functions to insert items from tape to the database."""
from collections import OrderedDict

import datetime

from pytape.client import Client
from pytape.transport import TransportException

from psycopg2 import Error as dbError
from psycopg2._psycopg import connection, cursor

from get_time import get_hour
from get_mydb import get_db

from tape_tools import handling_tape_error, get_field_text_values

from logging_tools import logger


def insert_items(tape: Client, apps_ids: list):
    """Insert tape items in the database.

    Args:
        tape (Client): tape client
        apps_ids (list): List of tape apps IDs

    Returns:
        int: Code to handle the main loop. `0` if no errors,
        `1` if the tape API limit is reached.
        `2` encountered another error with tape,
    """
    # Waiting for DB connection
    mydb = None
    while not mydb:
        mydb = get_db()
    cursor = mydb.cursor()

    for app_id in apps_ids:
        try:
            app_info = tape.App.find(app_id)
            workspace_id = app_info.get('workspace_id')

            # Retrieving all workspaces to get the workspace name
            workspaces = tape.Workspace.get_all_for_org()
            workspace = next(filter(lambda workspace: workspace['workspace_id'] == workspace_id, workspaces['workspaces']))

            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'tape' ORDER BY table_name;")
            tables = cursor.fetchall()

            table_name = workspace['slug'].replace('-', '_') + '__' + app_info['slug'].replace('-', '_')
            if (table_name,) in tables:
                # Data to fill in table
                table_data_model = OrderedDict()
                for field in app_info.get('fields'):
                    # Tape permits the following fields as simple attributes
                    if field['external_id'] not in ['record_id', 'created_on', 'last_modified_on']:
                        table_data_model[field['external_id']] = "''"

                try:

                    _insert_record_values(tape, app_id, mydb, cursor, table_name, table_data_model)

                except TransportException as err:
                    mydb.close()
                    logger.error(f"Erro no acesso ao Tape. {err}")
                    return 1
                except dbError as err:
                    continue

        except TransportException as err:
            mydb.close()
            logger.error(f"Erro no acesso ao Tape. {err}")
            return 1

    mydb.close()
    return 0


def _insert_record_values(tape: Client, app_id: int, mydb: connection, cursor: cursor, table_name: str, table_data_model: dict):
    """Insert records from tape in the database.
    """
    args = {"limit": 500}
    response = tape.App.get_records(app_id, **args)

    num_of_recs = response['total']
    data_counter = 0

    for values in _process_records(cursor, table_name, response['records'], table_data_model):
        _execute_insert_query(mydb, cursor, table_name, values)
        data_counter += 1

    if data_counter:
        for _ in range(data_counter, num_of_recs, 500):
            args['cursor'] = cursor

            response = tape.App.get_records(app_id, **args)

            for values in _process_records(cursor, table_name, response['records'], table_data_model):
                _execute_insert_query(mydb, cursor, table_name, values)


def _process_records(cursor: cursor, table_name: str, records: list, table_data_model: dict):
    """Process records from Tape.

    Yields:
        list: values from possibly each record to be inserted in the database.
    """
    for record in records:
        # New record being the copy of the model
        new_rec = table_data_model.copy()

        last_modified_on_tape = datetime.datetime.strptime(record['last_modified_on'], "%Y-%m-%d %H:%M:%S")
        cursor.execute(f"SELECT last_modified_on FROM tape.{table_name} WHERE record_id='{record['record_id']}'")
        if cursor.rowcount:

            last_modified_on_db = cursor.fetchone()[0]

            if last_modified_on_tape > last_modified_on_db:
                message = f"Registro de ID={record['item_id']} atualizado no tape. Excluindo-o da tabela '{table_name}' e inserindo-o a seguir."
                logger.info(message)
                cursor.execute(f"DELETE FROM tape.{table_name} WHERE record_id='{record['record_id']}'")

        if not cursor.rowcount or last_modified_on_tape > last_modified_on_db:

            values = [f"'{str(record['record_id'])}','{record['created_on']}','{record['last_modified_on']}'"]

            # Update new database record data with the record data from Tape
            for field in record.get('fields'):

                if field['external_id'] in table_data_model:
                    new_rec.update({field['external_id']: get_field_text_values(field)})

            values.extend(list(new_rec.values()))

            yield values


def _execute_insert_query(mydb: connection, cursor: cursor, table_name: str, values: list):
    """Execute the insert query.

    Raises:
        dbError: DB exception
    """
    query = [f"INSERT INTO tape.{table_name}", " VALUES", "("]
    query.extend(','.join(values))
    query.append(")")

    try:
        message = f"Inserindo resgistro de ID={values[0]} na tabela `{table_name}`"
        cursor.execute(''.join(query))
        logger.info(message)

        mydb.commit()
    except dbError as err:

        message = f"Aplicativo alterado. Excluindo a tabela `{table_name}`. {err}"
        logger.info(message)

        cursor.execute(f"DROP TABLE tape.{table_name}")
        raise dbError('Tabela excluída com sucesso!') from err
