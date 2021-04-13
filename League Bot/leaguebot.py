import discord
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv(".env")

riot_api = "https://euw1.api.riotgames.com/"

def get_times_played(champ):
    return champ.get('times_played')

def find_champion_name(champ_no):
    get_champs = requests.get('http://ddragon.leagueoflegends.com/cdn/11.7.1/data/en_US/champion.json')
    champion_list = json.loads(get_champs.content)
    champ_dict = {}

    for key in champion_list['data']:
        row = champion_list['data'][key]
        champ_dict[row['key']] = row['id']

    return champ_dict[str(champ_no)]

def get_matches(acc_id):
    get_match_info = requests.get(riot_api + 'lol/match/v4/matchlists/by-account/' + acc_id +'?api_key='+ os.getenv('RIOTTOKEN'))
    json_data = json.loads(get_match_info.content)
    all_champs_played = []
    times_played_list = []

    for match in json_data['matches']:
        if match['queue'] == 420:
            all_champs_played.append(match['champion'])
        else:
            continue
    
    individual_champs_played = list(set(all_champs_played))

    for champ in individual_champs_played:
        times_played = all_champs_played.count(champ)
        champ_name = find_champion_name(champ)
        times_played_list.append({'champ_name': champ_name ,'times_played': times_played})

    return times_played_list


def get_stats(summoner_name):
    get_id = requests.get(riot_api + 'lol/summoner/v4/summoners/by-name/'+ summoner_name +'?api_key='+ os.getenv('RIOTTOKEN'))
    json_data = json.loads(get_id.content)
    summ_id = json_data["id"]
    acc_id = json_data["accountId"]
    champs_played_in_last_100 = get_matches(acc_id)
    get_info = requests.get(riot_api + '/lol/league/v4/entries/by-summoner/'+ summ_id +'?api_key='+ os.getenv('RIOTTOKEN'))
    json_data = json.loads(get_info.content)
    summoner_data = json_data
    summoner_data.append(champs_played_in_last_100)

    return summoner_data

client = discord.Client()

@client.event
async def on_ready():
    print('RankBot is here {0.user}'.format(client))

@client.event
async def on_message(message):
    msg = message.content

    if message.author == client.user: 
        return
    if msg.startswith('$ranked'):
        summoner_name = msg.split("$ranked", 1)[1]
        summoner_data = get_stats(summoner_name)

        if len(summoner_data) == 0:
            await message.channel.send('This user has no ranked info, finish your placements and try again')
        else:
            total_games = summoner_data[0]['wins'] + summoner_data[0]['losses']
            win_rate = (summoner_data[0]['wins'] / total_games) * 100
            name = summoner_name
            tier = summoner_data[0]['tier']
            rank = summoner_data[0]['rank']
            lp = summoner_data[0]['leaguePoints']
            win_rate = "{:.2f}".format(win_rate)
            hot_streak = summoner_data[0]['hotStreak']
            
            if hot_streak:
                response = name + ' is on a hot streak in' + tier + ' ' + rank + ': ' + str(lp) + ' LP with a win rate of ' + str(win_rate) + '% in ' + str(total_games) + ' games\n'
            else:
                response = name + ' is ' + tier + ' ' + rank + ': ' + str(lp) + ' LP with a win rate of ' + str(win_rate) + '% in ' + str(total_games) + ' games\n'
                summoner_data[1].sort(key=get_times_played, reverse=True)
                top_five_champs = []
                if summoner_data[1][0]:
                    top_five_champs.append(summoner_data[1][0])
                if summoner_data[1][1]:
                    top_five_champs.append(summoner_data[1][1])
                if summoner_data[1][2]:
                    top_five_champs.append(summoner_data[1][2])
                if summoner_data[1][3]:
                    top_five_champs.append(summoner_data[1][3])
                if summoner_data[1][4]:
                    top_five_champs.append(summoner_data[1][4])
                for champ in top_five_champs:
                    response += 'In the last 100 games' + name + "'" + 's top' + str(len(summoner_data[1])) + 'most played champs are:\n' + champ['champ_name'] + ' ' + str(champ['times_played']) + ' times\n'

            await message.channel.send(response)

client.run(os.getenv('TOKEN'))