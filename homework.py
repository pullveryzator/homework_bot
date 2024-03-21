import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler

import requests
import telegram
from dotenv import load_dotenv
from requests import RequestException
from telegram import TelegramError

from exceptions import (AccessDeniedException, AnswerTypeException,
                        KeyErrorException, ServerAccessException,
                        StatusErrorException, UnexpectedFromDateException)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


CONST_ERROR_MESSAGE = 'A required environment variable is missing: '
REQUEST_ERROR_MESSAGE = 'Server request error: '


formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Checking tokens.

    Checks the availability of environment variables
    that are necessary for the program to run.
    """
    secrets = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for key, value in secrets.items():
        if not value:
            logger.critical(f'{CONST_ERROR_MESSAGE}{key}')
            exit()


def send_message(bot, message):
    """Sending message to Telegram.

    Sends a message to Telegram chat using the TELEGRAM_CHAT_ID
    environment variable. Accepts two input parameters:
    an instance of the Bot class and text with the message text.
    Return True if sending is successfull, else: return False.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Message <<{message}>> succefully sended.')
    except TelegramError as error:
        logger.error(f'{error}')
        return False
    return True


def get_api_answer(timestamp):
    """Get API request.

    Gets a request to a single endpoint of the API service.
    A timestamp is passed as a parameter to the function.
    """
    payload = {'from_date': timestamp}
    try:
        homeworks = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except RequestException as error:
        raise ServerAccessException(
            f'{REQUEST_ERROR_MESSAGE}error: {error}.')
    status_code = homeworks.status_code
    if status_code != HTTPStatus.OK:
        raise RequestException(
            f'{REQUEST_ERROR_MESSAGE}status code: {status_code}.')
    return homeworks.json()


def check_response(response):
    """Checking API response.

    Checks the API response for compliance with the documentation
    from the API lesson of the Practicum.Domashka service.
    As a parameter, the function receives the API response
    cast to Python data types.
    """
    if not isinstance(response, dict):
        raise AnswerTypeException(response, dict)
    homework = response.get('homeworks')
    if not isinstance(homework, list):
        raise AnswerTypeException(homework, list)
    if response.get('code') == 'UnknownError':
        error = response.get('error')
        raise UnexpectedFromDateException(error)
    elif response.get('code') == 'not_authenticated':
        error = response.get('message')
        raise AccessDeniedException(error)
    return homework


def parse_status(homework):
    """Get the homework status from the homework list.

    Extracts from information about a specific household job the status
    of that job.
    The function receives only one element from the list of chores
    as a parameter.
    If successful, the function returns a string prepared for sending to
    Telegram, containing one of the verdicts of the
    HOMEWORK_VERDICTS dictionary.
    """
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyErrorException
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS or not status:
        raise StatusErrorException(status)
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """The main function of the program.
    1. Verification of tokens.
    2. Receiving a response from the API.
    3. Checking the answer.
    4. If there are changes in the status of homework,
    then send a message to Telegram.
    """
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    old_err_message = ''

    while True:
        try:
            check_tokens()
            api_answer = get_api_answer(timestamp)
            timestamp = api_answer.get('current_date')
            homework = check_response(api_answer)
            if homework:
                message = parse_status(homework[0])
                send_message(bot, message)
        except (
            AccessDeniedException,
            AnswerTypeException,
            KeyErrorException,
            RequestException,
            StatusErrorException,
            ServerAccessException,
            UnexpectedFromDateException,
            Exception,
        ) as error:
            err_message = f'Program failure: {error}'
            logger.error(f'{error}')
            if old_err_message != err_message:
                if send_message(bot, err_message):
                    old_err_message = err_message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
