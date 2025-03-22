import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from conquerybot.utils.database import init_database

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Konfiguracja intencji bota
intents = discord.Intents.all()  # Włącz wszystkie intencje
intents.message_content = True
intents.members = True
intents.presences = True  # Dodaj intencje dla statusów

# Inicjalizacja bota
bot = commands.Bot(command_prefix='!', intents=intents)

# Inicjalizacja bazy danych
init_database()

# Wyłączenie domyślnej komendy help
bot.remove_command('help')

@bot.command(name="help")
async def help(ctx):
    """Wyświetla listę dostępnych komend"""
    embed = discord.Embed(
        title="📚 Lista komend",
        description="Oto lista dostępnych komend:",
        color=discord.Color.blue()
    )

    # Kategoria: Poziom
    level_commands = """
    `!level [użytkownik]` - Sprawdź poziom użytkownika
    """
    embed.add_field(name="🎮 Poziom", value=level_commands, inline=False)

    # Kategoria: Ekonomia
    economy_commands = """
    `!work` - Pracuj aby zarobić pieniądze (CD: 15min)
    `!daily` - Odbierz dzienną nagrodę (CD: 24h)
    `!balance [użytkownik]` - Sprawdź stan konta
    `!deposit/dep [kwota/all]` - Wpłać pieniądze do banku
    `!withdraw/with [kwota/all]` - Wypłać pieniądze z banku
    `!fraud` - Spróbuj oszukać system (CD: 30min)
    `!rob [użytkownik]` - Spróbuj ukraść pieniądze (CD: 1h)
    """
    embed.add_field(name="💰 Ekonomia", value=economy_commands, inline=False)

    # Kategoria: Hazard
    gambling_commands = """
    `!roulette/ruletka <kwota> <wybór>` - Zagraj w ruletkę (CD: 5s)
    `!blackjack/bj <kwota>` - Zagraj w blackjacka (CD: 10s)
    `!dice/kostka <kwota> <wybór>` - Rzuć kością (CD: 5s)
    `!coinflip/cf <kwota> <wybór>` - Rzut monetą (CD: 3s)
    """
    embed.add_field(name="🎲 Hazard", value=gambling_commands, inline=False)

    # Kategoria: Sklep
    shop_commands = """
    `!shop` - Wyświetl sklep
    `!buy [przedmiot]` - Kup przedmiot ze sklepu
    """
    embed.add_field(name="🛍️ Sklep", value=shop_commands, inline=False)

    # Kategoria: Inne
    other_commands = """
    `!help` - Wyświetl tę listę komend
    `!gifit` - Konwertuj zdjęcie lub film na GIF (CD: 30s)
    `!picperms` - Sprawdź uprawnienia do wysyłania zdjęć i GIFów
    """
    embed.add_field(name="ℹ️ Inne", value=other_commands, inline=False)

    embed.set_footer(text="CD = Cooldown (czas oczekiwania między użyciami)")
    
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user.name}')
    print(f'ID bota: {bot.user.id}')
    print('------')
    
    # Ładowanie modułów
    await bot.load_extension('conquerybot.cogs.leveling')
    await bot.load_extension('conquerybot.cogs.economy')
    await bot.load_extension('conquerybot.cogs.gif')
    await bot.load_extension('conquerybot.cogs.permissions')
    await bot.load_extension('conquerybot.cogs.gambling')
    
    print("Bot jest gotowy do użycia!")

# Uruchomienie bota
bot.run(os.getenv('DISCORD_TOKEN')) 