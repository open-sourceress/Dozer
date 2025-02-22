"""Initializes the bot and deals with the configuration file"""

import asyncio
import json
import os
import sys

import discord
import sentry_sdk

from .db import db_init, db_migrate

config = {
    'prefix': '&', 'developers': [],
    'cache_size': 20000,
    'tba': {
        'key': 'Put TBA API key here'
    },
    'toa': {
        'key': 'Put TOA API key here',
        'app_name': 'Dozer',
    },
    'db_url': 'postgres://dozer_user:simplepass@postgres_ip',
    'gmaps_key': "PUT GOOGLE MAPS API KEY HERE",
    'discord_token': "Put Discord API Token here.",
    'news': {
        'check_interval': 5.0,
        'twitch': {
            'client_id': "Put Twitch Client ID here",
            'client_secret': "Put Twitch Secret Here"
        },
        'reddit': {
            'client_id': "Put Reddit Client ID here",
            'client_secret': "Put Reddit Secret Here"
        },

    },
    'lavalink': {
        'enabled': False,
        'host': '127.0.0.1',
        'port': 2333,
        'password': 'youshallnotpass',
        'identifier': 'MAIN',
        'region': 'us_central'
    },
    'debug': False,
    'presences_intents': False,
    'is_backup': False,
    'invite_override': "",
    "sentry_url": ""
}
config_file = 'config.json'

if os.path.isfile(config_file):
    with open(config_file) as f:
        config.update(json.load(f))

with open('config.json', 'w') as f:
    json.dump(config, f, indent='\t')

if config['sentry_url'] != "":
    sentry_sdk.init(  # pylint: disable=abstract-class-instantiated  # noqa: E0110
        str(config['sentry_url']),
        traces_sample_rate=1.0,
    )

asyncio.get_event_loop().run_until_complete(db_init(config['db_url']))

if 'discord_token' not in config:
    sys.exit('Discord token must be supplied in configuration')

if sys.version_info < (3, 6):
    sys.exit('Dozer requires Python 3.6 or higher to run. This is version %s.' % '.'.join(sys.version_info[:3]))

from . import Dozer  # After version check

intents = discord.Intents.default()
intents.members = True
intents.presences = bool(config['presences_intents'])

bot = Dozer(config, intents=intents, max_messages=config['cache_size'])

for ext in os.listdir('dozer/cogs'):
    if not ext.startswith(('_', '.')):
        bot.load_extension('dozer.cogs.' + ext[:-3])  # Remove '.py'

asyncio.get_event_loop().run_until_complete(db_migrate())

bot.run()

# restart the bot if the bot flagged itself to do so
if bot._restarting:
    script = sys.argv[0]
    if script.startswith(os.getcwd()):
        script = script[len(os.getcwd()):].lstrip(os.sep)

    if script.endswith('__main__.py'):
        args = [sys.executable, '-m', script[:-len('__main__.py')].rstrip(os.sep).replace(os.sep, '.')]
    else:
        args = [sys.executable, script]
    os.execv(sys.executable, args + sys.argv[1:])
