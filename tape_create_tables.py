"""Functions to create tables in the database based on tape apps."""
from psycopg2 import Error as dbError

from pytape.client import Client
from pytape.transport import TransportException

from get_time import get_hour
from get_mydb import get_db
from tape_tools import handling_tape_error
# from telegram_tools import send_to_bot
from logging_tools import logger


def create_tables(tape: Client, apps_ids: list):
    """Create tables in the database for each tape app.

    Args:
        tape (_type_): _description_
        apps_ids (_type_): _description_

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

        # Creating database tables for each tape app
        try:
            app_info = tape.App.find(app_id)
            workspace_id = app_info.get('workspace_id')

            # Retrieving all workspaces to get the workspace name
            workspaces = tape.Workspace.get_all_for_org()
            workspace = next(filter(lambda workspace: workspace['workspace_id'] == workspace_id, workspaces['workspaces']))

            cursor.execute("SELECT table_name FROM information_schema.tables "\
                "WHERE table_schema = 'tape' ORDER BY table_name;")
            tables = cursor.fetchall()

            table_name = workspace['slug'].replace('-', '_') + '__' + app_info['slug'].replace('-', '_')
            if (table_name,) not in tables:
                query = [f"CREATE TABLE IF NOT EXISTS tape.{table_name}", "("]
                query.append('"record_id" TEXT PRIMARY KEY NOT NULL')
                query.append(', "created_on" TIMESTAMP')
                query.append(', "last_modified_on" TIMESTAMP')

                for field in app_info.get('fields'):
                    # Tape permits the following fields as simple attributes
                    if field['external_id'] not in ['record_id', 'created_on', 'last_modified_on']:
                        query.append(f", \"{field['external_id']}\" TEXT")
                query.append(")")

                message = f"Criando a tabela `{table_name}`"
                cursor.execute(''.join(query))
                hour = get_hour()
                mydb.commit()
                logger.info(message)

        except dbError as err:
            message = f"Erro no acesso ao BD. {err}"
            hour = get_hour()
            logger.error(message)

        except TransportException as err:
            message = 'Erro no acesso ao Tape.'
            logger.error(message)
            return 1
    mydb.close()
    return 0
