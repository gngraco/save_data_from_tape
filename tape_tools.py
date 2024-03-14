"""Auxiliary functions for Tape API"""
import json

from pytape.transport import TransportException
from logging_tools import logger


def handling_tape_error(err: TransportException):
    """Management of tape API errors

    Args:
        err (TransportException): tape transport error exception

    Returns:
        str: A string with the error message
    """
    if 'x-rate-limit-remaining' in err.status and err.status['x-rate-limit-remaining'] == '0':
        logger.warning("Quantidade de requisições chegou ao limite por hora.")
        return "rate_limit"

    if err.status['status'] == '401':
        logger.warning("Token expirado. Renovando...")
        return "token_expired"

    if err.status['status'] == '400':
        if json.loads(err.content)['error_detail'] == 'oauth.client.invalid_secret':
            message = "Secret inválido!"
        elif json.loads(err.content)['error_detail'] == 'user.invalid.username':
            message = "Usuário inválido!"
        elif json.loads(err.content)['error_detail'] == 'oauth.client.invalid_id':
            message = "ID do cliente inválido!"
        elif json.loads(err.content)['error_detail'] == 'user.invalid.password':
            message = "Senha do cliente inválida!"
        else:
            message = f"Parâmetro nulo na query! Detalhes: {err}"
        logger.warning(message)
        return "status_400"

    if err.status['status'] == '504':
        logger.warning("Servidor demorou muito para responder!")
        return "status_504"

    logger.warning("Erro inesperado no acesso a API! Detalhes: %s", str(err))
    return "not_known_yet"


def get_field_text_values(field: dict) -> str:
    """De um campo da coluna, é retornado o seu valor

    Args:
        field (Dict): O campo da tabela em questão

    Returns:
        str: Retorna o valor da coluna
    """

    values = "'"

    if field['type'] == "contact":

        for elem in field['values']:
            value = _value_or_null(elem['value']['name'])
            values += value.replace("\"", "'") + "|"

        values = values[:-1]

    elif field['type'] == "category":
        value = _value_or_null(field['values'][0]['value']['text'])
        values += value.replace("\"", "'")

    elif field['type'] == "date":

        value = _value_or_null(field['values'][0]['start'])
        values += value

    elif field['type'] == "calculation":

        value = _value_or_null(field['values'][0]['value_string'])
        values += value

    elif field['type'] == "money":

        currency = _value_or_null(field['values'][0]['currency'])
        value = _value_or_null(field['values'][0]['value'])
        values += f'{currency} {value}'

    elif field['type'] == "file":

        value = _value_or_null(field['values'][0]['value']['link'])
        values += value

    elif field['type'] == "embed":

        value = _value_or_null(field['values'][0]['embed']['url'])
        values += value

    elif field['type'] == "app":

        # Nesse caso o campo é multivalorado, então concatena-se com um pipe '|'
        for val in field['values']:
            value = _value_or_null(val['value']['title'])
            values += value.replace("\"", "'") + "|"

        values = values[:-1]

    elif field['type'] == "number" or field['type'] == "unique_id":

        value = _value_or_null(field['values'][0]['value'])
        values += str(value)

    else:

        value = _value_or_null(field['values'][0]['value'])
        values += value.replace("\"", "'")

    values += "'"
    return values


def _value_or_null(value):
    """Função auxiliar para converter valor nulo
    em string vazia

    Args:
        value (str | None): Valor a ser convertido

    Returns:
        str: String vazia
    """
    if not value:
        return ''
    return value
