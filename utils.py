import sqlite3
import openpyxl
import pandas


class Team:
    def __init__(self, id, name):
        self.id = id
        self.name = name


def get_teams():
    teams_new = []

    try:
        connection = sqlite3.connect("bkz.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM 'teams'")
        records = cursor.fetchall()
        for team in records:
            teams_new.append(Team(team[0], team[1]))
        cursor.close()
    except sqlite3.Error:
        print("SQL error")

    return teams_new


class Participant:
    def __init__(self, tg_id, id, last_name, first_name, mid_name, birthdate, team_id):
        self.tg_id = tg_id
        self.id = id
        self.last_name = last_name
        self.first_name = first_name
        self.mid_name = mid_name
        self.birthdate = birthdate
        self.team_id = team_id


def get_participants():
    new_participants = []

    try:
        connection = sqlite3.connect("bkz.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM 'participants'")
        records = cursor.fetchall()
        for participant in records:
            new_participants.append(Participant(participant[0], participant[1], participant[2], participant[3],
                                                participant[4], participant[5], participant[6]))
        cursor.close()
    except sqlite3.Error:
        print("SQL error")

    return new_participants


def get_participant_index(tg_id, participants):
    for i, participant in enumerate(participants):
        if participant.tg_id == tg_id:
            return i

    return -10


class Games:
    def __init__(self, day, tour, teams_indexes, legionnaires):
        self.day = day
        self.tour = tour
        self.teams_indexes = teams_indexes
        self.legionnaires = legionnaires


def get_games():
    return [
        Games("Пн", "", [], []),
        Games("Вт", "", [], []),
        Games("Ср", "", [], []),
        Games("Чт", "Кубок бесконечности: IV этап (3*12)", [], []),
        Games("Пт", "", [], []),
        Games("Сб1", "", [], []),
        Games("Сб2", "", [], []),
        Games("Сб3", "какойнибудь синхрон", [], []),
        Games("Вс1", "постмодернтокин", [], []),
        Games("Вс2", "вМоГоТУ-2019", [], []),
        Games("Вс3", "", [], [])
    ]


def get_game_index(day, games):
    for i, game in enumerate(games):
        if game.day == day:
            return i


def get_team_index(name, teams):
    for i, team in enumerate(teams):
        if team.name == name:
            return i


def create_table(game_index, games, teams, participants):
    filepath = f"{games[game_index].day}.xlsx"
    wb = openpyxl.Workbook()
    wb.save(filepath)

    table = {
        'id команды': [],
        'Название': [],
        'Город': [],
        'Флаг': [],
        'id игрока': [],
        'Фамилия': [],
        'Имя': [],
        'Отчество': [],
        'Дата рождения': []
    }

    registered_teams = games[game_index].teams_indexes
    for team in registered_teams:
        team_index = team[0]
        for i, player_index in enumerate(team[1]):
            table['id команды'].append(teams[team_index].id)
            table['Название'].append(teams[team_index].name)
            table['Город'].append('Москва')
            table['Флаг'].append(get_participant_flag(i, team_index, player_index, teams, participants))  # ?
            table['id игрока'].append(participants[player_index].id)
            table['Фамилия'].append(participants[player_index].last_name)
            table['Имя'].append(participants[player_index].first_name)
            table['Отчество'].append(participants[player_index].mid_name)
            table['Дата рождения'].append(participants[player_index].birthdate)

    df = pandas.DataFrame(table)
    df.to_excel(filepath)

    return filepath


def get_participant_flag(cycle_i, team_index, player_index, teams, participants):
    if cycle_i == 0:
        return 'К'

    if teams[team_index].id == participants[player_index].team_id:
        return 'Б'

    return 'Л'
