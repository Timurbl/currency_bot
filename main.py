import telebot
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TOKEN = '642513885:AAE5CoSu9JpuTO_JZSZuNwbt5h0uW8fQDhM'
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    html = 'Здравствуй, {}! Я бот, который поможет Вам узнавать курс валют и смотреть,' \
           ' сколько они стоят в других единицах.\n' \
           'Для списка доступных команд введите /commands\n' \
           'Чтобы узнать, с какими валютами мы работаем, напишите команду ' \
           '/currencies'.format(message.from_user.first_name)
    bot.send_message(message.chat.id, html)


@bot.message_handler(commands=['commands'])
def commands(message):
    text = 'У меня есть 3 команды.\n' \
           '"/currencies" - Список валют, с которыми я могу работать\n' \
           '"/rate cur" - Команда говорит курс заданной валюты cur\n' \
           '"/convert amount cur_to cur_from" - Переводит количество amount валюты cur_to в валюту cur_from'

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['currencies'])
def currencies(message):
    date = get_date()
    resp = requests.get("http://www.cbr.ru/scripts/XML_daily.asp?date_req=" + date)
    soup = BeautifulSoup(resp.content, "xml")

    arr_of_currencies = 'Список доспутных валют:\n'

    for i in soup.find_all('CharCode'):
        arr_of_currencies += str(i.text) + ' - '
        arr_of_currencies += i.find_next_sibling('Name').string + '\n'

    bot.send_message(message.chat.id, arr_of_currencies)


@bot.message_handler(commands=['rate'])
def rate(message):
    date = get_date()
    resp = requests.get("http://www.cbr.ru/scripts/XML_daily.asp?date_req=" + date)
    soup = BeautifulSoup(resp.content, "xml")

    try:
        command, currency = message.text.split()
        currency = currency.upper()

        if len(currency) != 3:
            bot.send_message(message.chat.id, 'Название валюты должно быть введено в сокращенной записи.')
        elif currency not in currencies_arr():
            bot.send_message(message.chat.id, 'Я не умею работать с такой валютой или такой валюты не существует :(')
        else:
            nominal = soup.find("CharCode", text=currency).find_next_sibling('Nominal').string
            rate_of_currency = soup.find("CharCode", text=currency).find_next_sibling('Value').string

            text = nominal + ' ' + currency + ' = ' + rate_of_currency + ' руб'

            bot.send_message(message.chat.id, text)

    except ValueError:
        bot.send_message(message.chat.id, 'Вы ввели некорректное число число данных.')


@bot.message_handler(commands=['convert'])
def convert_bot(message):

    try:
        command, amount, cur_from, cur_to = message.text.split()
        try:
            amount = float(amount)
        except ValueError:
            bot.send_message(message.chat.id, 'Вы ввели не число на месте количества валюты.')
        else:
            amount, cur_to, cur_from = float(amount), cur_to.upper(), cur_from.upper()

            arr = currencies_arr()

            if len(cur_from) != 3 and len(cur_to) != 3:
                bot.send_message(message.chat.id, 'Названия валют должны быть введены в сокращенной записи.')
            elif cur_from not in arr and cur_to not in arr:
                bot.send_message(message.chat.id, 'Я не умею работать с такими валютами'
                                                  ' или таких валют не существует :(')
            elif cur_from not in arr:
                bot.send_message(message.chat.id, 'Я не умею работать с такой валютой'
                                                  ' или такой валюты не существует :(\n'
                                                  '(Валюта, из которой происходит конвертирование)')
            elif cur_to not in arr:
                bot.send_message(message.chat.id, 'Я не умею работать с такой валютой'
                                                  ' или такой валюты не существует :(\n'
                                                  '(Валюта, в которую происходит конвертирование)')
            else:
                date = get_date()
                text = convert(amount, cur_to, cur_from, date)

                bot.send_message(message.chat.id, text)
    except ValueError:
        bot.send_message(message.chat.id, 'Вы ввели некорректное число число данных.')


def currencies_arr():
    date = get_date()
    resp = requests.get("http://www.cbr.ru/scripts/XML_daily.asp?date_req=" + date)
    soup = BeautifulSoup(resp.content, "xml")

    arr = []

    for i in soup.find_all('CharCode'):
        arr.append(str(i.text))

    return arr


def convert(amount, cur_to, cur_from, date):
    resp = requests.get("http://www.cbr.ru/scripts/XML_daily.asp?date_req=" + date)
    soup = BeautifulSoup(resp.content, "xml")

    currency = str(soup.find("CharCode", text=cur_from).find_next_sibling('Value').string)
    currency = currency.replace(',', ".")
    currency = float(currency)
    nominal = int(soup.find("CharCode", text=cur_from).find_next_sibling('Nominal').string)

    in_rub = amount * currency / nominal

    currency_new = str(soup.find("CharCode", text=cur_to).find_next_sibling('Value').string)
    currency_new = currency_new.replace(',', ".")
    currency_new = float(currency_new)
    nominal_new = int(soup.find("CharCode", text=cur_to).find_next_sibling('Nominal').string)
    in_rub_new = currency_new / nominal_new

    text = str(amount) + ' ' + cur_to + ' = ' + str(in_rub / in_rub_new) + ' ' + cur_from

    return text


def get_date():
    date = str(datetime.now())
    date = date[0:10]
    year, month, day = date[:4], date[5:7], date[8:10]
    return day + "/" + month + "/" + year


bot.polling()
