from os import getenv
import sys
import time

from pytape import api
from pytape.transport import TransportException

from get_time import get_hour
from tape_create_tables import create_tables
from tape_insert_records import insert_records
from tape_tools import handling_tape_error

from logging_tools import logger


if __name__ == '__main__':
    # Database update period in seconds
    timeOffset = int(getenv('TIMEOFFSET'))

    # tape credentials
    user_key = getenv('TAPE_USER_KEY')
    # Apps IDs
    apps_ids = list(map(int, getenv('TAPE_APPS_IDS').split(',')))

    MESSAGE = "==== SAVE DATA FROM TAPE ===="
    logger.debug(MESSAGE)

    # tape authentication
    try:
        tape = api.BearerClient(user_key)
    # Possible initial error
    except TransportException as err:
        handled = handling_tape_error(err)
        if handled == 'status_400':
            logger.error("Terminando o programa...")
        sys.exit()
    else:
        CYCLE = 1
        while True:
            MESSAGE = f"==== Ciclo {CYCLE} ===="
            logger.info(MESSAGE)

            CREATION = create_tables(tape, apps_ids)

            if CREATION == 0:

                INSERTION = insert_records(tape, apps_ids)

                # Caso o limite de requisições seja atingido, espera-se mais 1 hora até a seguinte iteração
                if INSERTION == 1:
                    hour = get_hour(hours=1)
                    MESSAGE = f"Esperando a hora seguinte. Até às {hour}"
                    logger.info(MESSAGE)
                    time.sleep(3600)
                    try:
                        tape = api.BearerClient(user_key)
                    except:
                        MESSAGE = 'Erro na obtenção do novo cliente Tape! Tentando novamente...'
                        logger.warning(MESSAGE)

                elif INSERTION == 0:
                    # Nesse caso foi criado o primeiro snapshot do tape no BD. Próxima iteração no dia seguinte
                    hours = get_hour(seconds=timeOffset)
                    MESSAGE = f"Esperando as próximas {timeOffset/3600}hs. Até às {hours}"
                    logger.info(MESSAGE)
                    time.sleep(timeOffset)
                    try:
                        tape = api.BearerClient(user_key)
                    except:
                        MESSAGE = 'Erro na obtenção do novo cliente Tape! Tentando novamente...'
                        logger.warning(MESSAGE)

                else:
                    MESSAGE = "Tentando novamente..."
                    logger.info(MESSAGE)

                    try:
                        tape = api.BearerClient(user_key)
                    except:
                        MESSAGE = 'Erro na obtenção do novo cliente Tape! Tentando novamente...'
                        logger.warning(MESSAGE)
                    # time.sleep(1)

            elif CREATION == 1:
                hour = get_hour(hours=1)
                MESSAGE = f"Esperando a hora seguinte às {hour}"
                logger.info(MESSAGE)
                time.sleep(3600)
                try:
                    tape = api.BearerClient(user_key)
                except:
                    MESSAGE = 'Erro na obtenção do novo cliente Tape! Tentando novamente...'
                    logger.warning(MESSAGE)

            elif CREATION == 2:
                MESSAGE = "Tentando novamente..."
                logger.info(MESSAGE)
                try:
                    tape = api.BearerClient(user_key)
                except:
                    MESSAGE = 'Erro na obtenção do novo cliente Tape! Tentando novamente...'
                    logger.warning(MESSAGE)

                # time.sleep(1)

            else:
                MESSAGE = "Erro inesperado na criação/atualização do BD. Terminando o programa."
                logger.error(MESSAGE)
                sys.exit()
            CYCLE += 1
