import threading
import time

import telebot
import os
import imaplib
import email as emaillib
from email.header import decode_header


# noinspection PyUnresolvedReferences,PyTypeChecker
class MailThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.last_message_id = None

    def run(self):
        global imap, bot, logged_in_user_id
        while True:
            imap.select('INBOX')
            data = imap.search(None, 'ALL')
            mail_ids = data[1]
            id_list = mail_ids[0].split()
            latest_email_id = int(id_list[-1])
            if self.last_message_id is None:
                self.last_message_id = latest_email_id
            for i in range(self.last_message_id + 1, latest_email_id + 1, 1):
                bot.send_message(logged_in_user_id, "You have a new message.")
                try:
                    data = imap.fetch(str(i), '(RFC822)')
                    for response_part in data:
                        arr = response_part[0]
                        if isinstance(arr, tuple):
                            msg_str = str(arr[1], 'utf-8')
                            msg = emaillib.message_from_string(msg_str)
                            email_subject = msg['subject']
                            email_from = msg['from']
                            result_msg = 'From : ' + email_from + '\n'
                            result_msg += 'Subject : ' + self.decode(email_subject) + '\n'
                            if isinstance(msg.get_payload(), str):
                                email_body = msg.get_payload()
                            else:
                                email_body = msg.get_payload()[0].get_payload()
                            result_msg += 'Body: ' + self.decode(email_body) + '\n'
                            bot.send_message(logged_in_user_id, result_msg)
                except Exception as e:
                    print(e.__str__())
                    bot.send_message(logged_in_user_id, "Some problems in your email parsing.")
            self.last_message_id = latest_email_id
            time.sleep(10)

    def decode(self, s):
        b, encoding = decode_header(s)[0]
        try:
            return b.decode(encoding)
        except:
            return s


botToken = os.getenv('BOT_TOKEN')
bot = None
if botToken is None:
    with open('token.txt') as reader:
        bot = telebot.TeleBot(reader.readline())
else:
    bot = telebot.TeleBot(botToken)
chat_id = os.getenv('CHAT_ID')
chat_ids = [chat_id]
for i in chat_ids:
    bot.send_message(i, "Bot is started.")
waitForLogin = False
email = ''
imap = None
logged_in_user_id = None

bot.set_webhook()

@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.send_message(message.from_user.id, f'Hi, {message.from_user.first_name}')
    bot.send_message(message.from_user.id, 'Use ''/login'' command to add an email.')


@bot.message_handler(commands=['login'])
def login(message):
    global waitForLogin
    bot.send_message(message.from_user.id, 'Enter your email and password through a space.')
    waitForLogin = True


@bot.message_handler(content_types=['text'])
def text_message(message):
    global email, imap, waitForLogin, logged_in_user_id
    if waitForLogin:
        email = message.text.split()[0]
        password = message.text.split()[1]
        if email is None or password is None:
            bot.send_message(message.from_user.id, 'Wrong format.')
        else:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            try:
                imap.login(email, password)
            except:
                bot.send_message(message.from_user.id, 'Invalid credentials or another error.')
                return

            logged_in_user_id = message.from_user.id
            if __name__ == '__main__':
                mail_thread = MailThread()
                mail_thread.start()
            bot.send_message(message.from_user.id, 'Login is successful.')


while True:
    try:
        bot.polling(none_stop=True)
    except:
        print('Error in polling.')
