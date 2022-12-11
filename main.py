from utils import *
import telebot
#import aiogram
import vk
from telebot import types


team_global = day_global = ''

''' 
    TODO: @me
    vk parse
    otpis'ka
    auto delete games after timeend
'''


def read_file(file_name):
    with open(file_name, 'r') as file:
        return file.read()


bot = telebot.TeleBot(read_file('token.ini'))


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    text = \
        "Бот для регистрации на игры в БКЗ.\n" \
        "Команды:\n" \
        "/help - выводит это сообщение\n" \
        "/games - список игр\n" \
        "/we - список членов БКЗ\n" \
        "/me - информация обо мне\n"

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['me'])
def print_user_info(message):
    text = "Вас нет в списке членов БКЗ"
    i = get_participant_index(message.from_user.id, participants)
    if i >= 0:
        text = f"ФИО: {participants[i].last_name} {participants[i].first_name} {participants[i].mid_name}\n" \
               f"id: {participants[i].id}\n"
    '''
        if participants[i].team_id:
         #   j = get_team_index()
          #  text += f"В базовом составе команды \"{}\""
        else:'''

    bot.send_message(message.chat.id, text=text)


@bot.message_handler(commands=['we'])
def print_bkz_members(message):
    text = ""
    for i, participant in enumerate(participants):
        text += f"{i + 1}. {participant.last_name} {participant.first_name} {participant.mid_name}\n" \
            # f"\tid: {participant[i].id}\n"

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['games'])
def print_games_list(message):
    games_list = ""
    for game in games:
        if game.tour:
            games_list += f"\n{game.day} — {game.tour}"

            if game.teams_indexes:
                games_list += f"\n\tЗаявленные команды: "
                for team in game.teams_indexes:
                    games_list += f"\n{teams[team[0]].name}("
                    for j in team[1]:
                        games_list += f"{participants[j].last_name} {participants[j].first_name[0]}., "
                    games_list = games_list[:-2] + ")\n"

            if game.legionnaires:
                games_list += f"\nСписок желающих: "
                for i in game.legionnaires:
                    games_list += f" {participants[i].last_name} {participants[i].first_name[0]}.,"
                games_list = games_list[:-1]

    if games_list == "":
        bot.send_message(message.chat.id, "Нет доступных турниров")
    else:
        bot.send_message(message.chat.id, f"Список турниров:\n{games_list}")
        markup = types.InlineKeyboardMarkup(row_width=3)
        btns = []
        for game in games:
            if game.tour:
                btns.append(types.InlineKeyboardButton(text=game.day, callback_data=game.day))
        markup.add(*btns)

        bot.send_message(message.chat.id, "Выберите игру:", reply_markup=markup)


def register_player(message, day):
    markup = types.InlineKeyboardMarkup()
    for team in teams:
        markup.add(types.InlineKeyboardButton(text=f"Заявить команду\n{team.name}", callback_data=f"{team.name}${day}"))
    markup.add(types.InlineKeyboardButton(text="Ищу команду", callback_data=f"legionnaire${day}"))

    bot.send_message(message.chat.id, "Выберите команду, в которой хотите играть:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.data.startswith("МГТУ"):
            global team_global, day_global
            team_global, day_global = call.data.split('$')
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f"smth\n{call.data}")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            print_bkz_members(call.message)
            bot.send_message(call.message.chat.id, "Отправьте через пробел номера игроков (кол-во - до 6)")

        elif call.data.startswith("legionnaire"):
            callback, day = call.data.split('$')
            i = get_game_index(day, games)
            j = get_participant_index(call.from_user.id, participants)
            games[i].legionnaires.append(j)

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f"Вы добавлены в список желающих на {day}")

        else:
            i = get_game_index(call.data, games)
            j = get_participant_index(call.from_user.id, participants)
            if j in games[i].legionnaires:
                bot.send_message(call.from_user.id, text="Вы уже зарегистровованы на этот турнир")
            else:
                register_player(call.message, games[i].day)
            # bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="rr")
            bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        print("Callback error")


@bot.message_handler(content_types='text')
def message_reply(message):
    global day_global, team_global

    if day_global and team_global:
        sending_message = ""
        error = False
        ind_team = get_team_index(team_global, teams)
        ind_day = get_game_index(day_global, games)
        array = [ind_team, []]
        try:
            positions = list(map(int, message.text.split()))
            bkz_len = len(participants)
            if len(positions) < 4 or len(positions) > 6:
                error = True
                sending_message = "Количество игроков должно быть от 4 до 6. Попробуйте еще раз.\n"
            else:
                for position in positions:
                    if position - 1 < 0 or position > bkz_len:
                        error = True
                        sending_message = f"В БКЗ только {bkz_len} участников. Попробуйте еще раз.\n"
                        break
                    else:
                        array[1].append(position - 1)
        except:
            error = True
            sending_message = "Сообщение должно содержать только числа и знаки пробела. Попробуйте еще раз.\n"

        if not error:
            games[ind_day].teams_indexes.append(array)

            excel_table = create_table(ind_day, games, teams, participants)
            doc = open(excel_table, 'rb')
            bot.send_document(message.from_user.id, doc)

            sending_message = f"Вы успешно зарегистрировали команду {teams[ind_team].name} на {day_global}"
            day_global = team_global = ''

        bot.send_message(message.from_user.id, sending_message)

    if message.text.lower() == "старт" or message.text.lower() == "помощь":
        send_welcome(message)
    # elif message.text == ""



def vk_parser():
    vk


if __name__ == "__main__":
    teams = get_teams()
    participants = get_participants()
    games = get_games()

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)

'''
def date_is_correct(date):
    now = datetime.datetime.now()
    if date["year"] < now.year or date["month"] < now.month or date["day"] < now.day:
        return False
    return True
'''
