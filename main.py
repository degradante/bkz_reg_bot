from bot_token import BOT_TOKEN
from utils import *

from aiogram import types, Dispatcher, Bot, executor
import vk

team_index = day_index = -1

''' 
    TODO: @me
    повторяются номера
    vk parse
    otpis'ka
    auto delete games after timeend
'''

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    await message.delete()
    text = \
        "Бот для регистрации на игры в БКЗ.\n" \
        "Команды:\n" \
        "/help - выводит это сообщение\n" \
        "/games - список игр\n" \
        "/we - список членов БКЗ\n" \
        "/me - информация обо мне\n"
    await message.answer(text)


@dp.message_handler(commands=['me'])
async def print_user_info(message):
    await message.delete()
    text = "Вас нет в списке членов БКЗ"
    i = get_participant_index(message.from_user.id)
    if i >= 0:
        text = f"ФИО: {participants[i].last_name} {participants[i].first_name} {participants[i].mid_name}\n" \
               f"id: {participants[i].id}\n"
    '''
        if participants[i].team_id:
         #   j = get_team_index()
          #  text += f"В базовом составе команды \"{}\""
        else:'''

    await message.answer(text)


@dp.message_handler(commands=['we'])
async def print_bkz_members(message):
    await message.delete()
    text = ""
    for i, participant in enumerate(participants):
        text += f"{i + 1}. {participant.last_name} {participant.first_name} {participant.mid_name}\n" \
            # f"\tid: {participant[i].id}\n"

    await message.answer(text)


@dp.message_handler(commands=['games'])
async def print_games_list(message):
    await message.delete()
    games_list = ""
    for game in games:
        if game.tour:
            games_list += f"\n{game.day} — {game.tour}"

            if game.registered_teams:
                games_list += f"\n\tЗаявленные команды: "
                for team in game.registered_teams:
                    games_list += f"\n{teams[team.index].name}("
                    for j in team.players:
                        games_list += f"{participants[j].last_name} {participants[j].first_name[0]}., "
                    games_list = games_list[:-2] + ")\n"

            if game.legionnaires:
                games_list += f"\nСписок желающих: "
                for i in game.legionnaires:
                    games_list += f" {participants[i].last_name} {participants[i].first_name[0]}.,"
                games_list = games_list[:-1]

    if games_list == "":
        await message.answer("Нет доступных турниров")
    else:
        await message.answer(f"Список турниров:\n{games_list}")
        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = []
        for game_index, game in enumerate(games):
            if game.tour:
                buttons.append(types.InlineKeyboardButton(text=game.day, callback_data=str(game_index)))
        markup.add(*buttons)

        await message.answer("Выберите игру:", reply_markup=markup)


async def register_player(message, day_ind, looking_for_team):
    markup = types.InlineKeyboardMarkup()
    for i, team in enumerate(teams):
        check = True
        for indexes in games[day_ind].registered_teams:
            if indexes[0] == i:
                check = False
                break
        if check:
            markup.add(types.InlineKeyboardButton(text=f"Заявить команду\n{team.name}", callback_data=f"МГТУ${i}${day_ind}"))
    if looking_for_team:
        markup.add(types.InlineKeyboardButton(text="Ищу команду", callback_data=f"legionnaire${day_ind}"))

    await message.answer("Выберите команду, в которой хотите играть:", reply_markup=markup)


@dp.callback_query_handler()
async def callback_inline(call: types.CallbackQuery):
    try:
        if call.data.startswith("МГТУ"):
            global team_index, day_index

            rubbish = call.data.split('$')
            team_index = int(rubbish[1])
            day_index = int(rubbish[2])
            print(teams[team_index].name, games[day_index].day)

            await call.message.delete()
            await print_participants(call.message)

        elif call.data.startswith("legionnaire"):
            rubbish, i = call.data.split('$')
            i = int(i)
            j = get_participant_index(call.from_user.id)
            games[i].legionnaires.append(j)

            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        text=f"Вы добавлены в список желающих на {games[i].day}")

        else:
            print(call.data)
            game_index = int(call.data)
            participant_index = get_participant_index(call.from_user.id)
            if participant_index in games[game_index].legionnaires:
                await register_player(call.message, game_index, looking_for_team=False)
            else:
                await register_player(call.message, game_index, looking_for_team=True)
            await call.message.delete()
    except:
        print("Callback error")


@dp.message_handler(content_types='text')
async def register_team(message):
    global day_index, team_index

    if day_index != -1 and team_index != -1:
        sending_message = ""
        error = False
        registered_team = RegisteredTeam(team_index, [])
        try:
            positions = set(map(int, message.text.split()))
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
                        registered_team.players.append(position - 1)
        except:
            error = True
            sending_message = "Сообщение должно содержать только числа и знаки пробела. Попробуйте еще раз.\n"

        if not error:
            for player in registered_team.players:
                if player in games[day_index].legionnaires:
                    games[day_index].legionnaires.remove(player)

            games[day_index].registered_teams.append(registered_team)

            excel_table = create_table(day_index, games)
            doc = open(excel_table, 'rb')
            await bot.send_document(message.from_user.id, doc)

            sending_message = f"Вы успешно зарегистрировали команду {teams[team_index].name} на {games[day_index].day}"
            day_index = team_index = -1

        await message.answer(sending_message)

    if message.text.lower() == "старт" or message.text.lower() == "помощь":
        await send_welcome(message)
    # elif message.text == ""


async def print_participants(message):
    text = ""
    for participant_index, participant in enumerate(participants):
        if participant_index not in games[day_index].legionnaires and not is_registered_in_team(participant_index):
            text += f"{participant_index + 1}. {participant.last_name} {participant.first_name}\n"

    await message.answer(text)
    await message.answer("Отправьте через пробел номера игроков (кол-во - до 6)")


async def on_startup(_):
    print('Я запустился!')


def vk_parser():
    vk


def is_registered_in_team(player_ind):
    for i in range(len(games[day_index].registered_team)):
        if player_ind == games[day_index].registered_teams[i].players: # ??
            return True

    return False


if __name__ == "__main__":
    games = get_games()

    while True:
        try:
            executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
        except Exception as e:
            print(e)

'''
def date_is_correct(date):
    now = datetime.datetime.now()
    if date["year"] < now.year or date["month"] < now.month or date["day"] < now.day:
        return False
    return True
'''
