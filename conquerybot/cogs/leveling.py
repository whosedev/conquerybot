import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
from conquerybot.utils.database import get_user_data, update_user_data

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldown = 5  # sekundy między nagrodami XP
        self.xp_range = (15, 25)  # zakres XP za wiadomość
        self.last_message = {}  # słownik do przechowywania czasu ostatniej wiadomości
        self.level_up_messages = {}  # słownik do przechowywania ostatnich powiadomień o poziomie

    def check_message_cooldown(self, user_id: int) -> bool:
        current_time = datetime.now()
        if user_id in self.last_message:
            if current_time - self.last_message[user_id] < timedelta(seconds=self.xp_cooldown):
                return False
        return True

    def check_level_up_cooldown(self, user_id: int) -> bool:
        current_time = datetime.now()
        if user_id in self.level_up_messages:
            if current_time - self.level_up_messages[user_id] < timedelta(seconds=5):  # 5 sekund cooldown na powiadomienia o poziomie
                return False
        return True

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Sprawdź cooldown na wiadomości
        if not self.check_message_cooldown(message.author.id):
            return

        # Pobierz dane użytkownika
        user_data = get_user_data(message.author.id, message.guild.id)
        if not user_data:
            return

        # Dodaj losową ilość XP
        xp_gained = random.randint(*self.xp_range)
        new_xp = user_data['xp'] + xp_gained
        new_level = user_data['level']

        # Sprawdź czy użytkownik awansował na nowy poziom
        xp_needed = new_level * 100  # Prosty wzór na wymagane XP
        while new_xp >= xp_needed:
            new_xp -= xp_needed
            new_level += 1
            xp_needed = new_level * 100

            # Sprawdź cooldown na powiadomienia o poziomie
            if self.check_level_up_cooldown(message.author.id):
                # Powiadomienie o nowym poziomie
                await message.channel.send(
                    f"🎉 Gratulacje {message.author.mention}! Awansowałeś na poziom {new_level}!"
                )
                self.level_up_messages[message.author.id] = datetime.now()

        # Aktualizuj dane użytkownika
        update_user_data(message.author.id, message.guild.id, xp=new_xp, level=new_level)
        self.last_message[message.author.id] = datetime.now()

    @commands.command(name="level")
    async def show_level(self, ctx, member: discord.Member = None):
        """Pokazuje poziom użytkownika"""
        member = member or ctx.author
        user_data = get_user_data(member.id, ctx.guild.id)
        
        if not user_data:
            await ctx.send("Nie udało się pobrać danych użytkownika.")
            return

        xp_needed = user_data['level'] * 100
        progress = (user_data['xp'] / xp_needed) * 100

        embed = discord.Embed(
            title=f"Poziom {member.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Poziom", value=str(user_data['level']), inline=True)
        embed.add_field(name="XP", value=f"{user_data['xp']}/{xp_needed}", inline=True)
        embed.add_field(name="Postęp", value=f"{progress:.1f}%", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot)) 