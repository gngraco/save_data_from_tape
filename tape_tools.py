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

    final_values = "'"

    if field['type'] == "contact":

        for elem in field['values']:
            value = elem.get('value', {}).get('name', '')
            final_values += value.replace("'", "") + "|"

        final_values = final_values[:-1]

    elif field['type'] == "category":

        for elem in field['values']:
            value = elem.get('value', {}).get('text', '')
            final_values += value.replace("'", "") + "|"

        final_values = final_values[:-1]

    elif field['type'] == "date":

        values = field['values']
        # `next` obtém o primeiro valor
        value = next(iter(values), {}).get('start', '')

        final_values += value

    elif field['type'] == "calculation":

        values = field['values']
        # `next` obtém o primeiro valor
        value = next(iter(values), {}).get('value_string', '')

        final_values += value

    elif field['type'] == "money":

        values = field['values']

        currency = next(iter(values), {}).get('currency', '')
        value = next(iter(values), {}).get('value', '')

        final_values += f'{currency} {value}'

    elif field['type'] == "file":

        values = field['values']

        value = next(iter(values), {}).get('value', {}).get('link', '')

        final_values += value

    elif field['type'] == "embed":

        values = field['values']

        value = next(iter(values), {}).get('embed', {}).get('url', '')

        final_values += value

    elif field['type'] == "app":

        # Nesse caso o campo é multivalorado, então concatena-se com um pipe '|'
        for val in field['values']:

            value = val.get('value', {}).get('title', '')
            final_values += value.replace("'", "") + "|"

        final_values = final_values[:-1]

    else:

        values = field['values']
        value = next(iter(values), {}).get('value')

        final_values += str(value).replace("'", "")

    final_values += "'"

    return final_values


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
