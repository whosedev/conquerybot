import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
from conquerybot.utils.database import get_user_data, update_user_data, get_shop_items, add_shop_item

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_cooldown = commands.CooldownMapping.from_cooldown(1, 86400, commands.BucketType.user)  # 24h cooldown
        self.work_cooldown = commands.CooldownMapping.from_cooldown(1, 900, commands.BucketType.user)  # 15min cooldown
        self.fraud_cooldown = commands.CooldownMapping.from_cooldown(1, 1800, commands.BucketType.user)  # 30min cooldown
        self.rob_cooldown = commands.CooldownMapping.from_cooldown(1, 3600, commands.BucketType.user)  # 1h cooldown
        self.daily_amount = 100
        self.work_amount_range = (50, 200)
        self.cooldowns = {}

    def check_cooldown(self, user_id: int, command: str, cooldown: int) -> bool:
        current_time = datetime.now()
        if user_id in self.cooldowns and command in self.cooldowns[user_id]:
            if current_time - self.cooldowns[user_id][command] < timedelta(seconds=cooldown):
                return False
        return True

    def set_cooldown(self, user_id: int, command: str):
        if user_id not in self.cooldowns:
            self.cooldowns[user_id] = {}
        self.cooldowns[user_id][command] = datetime.now()

    def get_remaining_cooldown(self, user_id: int, command: str, cooldown: int) -> int:
        if user_id in self.cooldowns and command in self.cooldowns[user_id]:
            remaining = cooldown - (datetime.now() - self.cooldowns[user_id][command]).total_seconds()
            return max(0, int(remaining))
        return 0

    @commands.command(name="daily")
    async def daily(self, ctx):
        """Odbierz dzienną nagrodę"""
        bucket = self.daily_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        
        if retry_after:
            hours = int(retry_after // 3600)
            minutes = int((retry_after % 3600) // 60)
            await ctx.send(f"⏰ Musisz poczekać jeszcze {hours}h {minutes}m przed kolejną nagrodą!")
            return

        user_id = str(ctx.author.id)
        user_data = get_user_data(user_id)
        
        if not user_data:
            user_data = {
                'user_id': user_id,
                'wallet': 0,
                'bank': 0,
                'last_daily': None
            }
        
        # Sprawdź czy użytkownik już odebrał dzienną nagrodę
        last_daily = user_data.get('last_daily')
        if last_daily:
            last_daily = datetime.fromisoformat(last_daily)
            if datetime.now() - last_daily < timedelta(days=1):
                remaining = timedelta(days=1) - (datetime.now() - last_daily)
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                await ctx.send(f"⏰ Musisz poczekać jeszcze {hours}h {minutes}m przed kolejną nagrodą!")
                return
        
        # Losowa kwota między 100 a 1000
        amount = random.randint(100, 1000)
        user_data['wallet'] += amount
        user_data['last_daily'] = datetime.now().isoformat()
        
        update_user_data(user_id, user_data)
        
        embed = discord.Embed(
            title="💰 Dzienna nagroda",
            description=f"Otrzymałeś {amount} monet!",
            color=discord.Color.green()
        )
        embed.add_field(name="Stan konta", value=f"Portfel: {user_data['wallet']} | Bank: {user_data['bank']}")
        await ctx.send(embed=embed)

    @commands.command(name="work")
    async def work(self, ctx):
        """Pracuj aby zarobić pieniądze"""
        if not self.check_cooldown(ctx.author.id, "work", self.work_cooldown):
            remaining = self.get_remaining_cooldown(ctx.author.id, "work", self.work_cooldown)
            await ctx.send(f"Musisz poczekać jeszcze {remaining} sekund przed kolejną pracą!")
            return

        user_data = get_user_data(ctx.author.id, ctx.guild.id)
        if not user_data:
            return

        earned = random.randint(*self.work_amount_range)
        new_wallet = user_data['wallet'] + earned
        update_user_data(ctx.author.id, ctx.guild.id, wallet=new_wallet)
        self.set_cooldown(ctx.author.id, "work")

        embed = discord.Embed(
            title="Praca",
            description=f"Pracowałeś i zarobiłeś {earned} monet!",
            color=discord.Color.green()
        )
        embed.add_field(name="Gotówka", value=f"{new_wallet} 💰")
        embed.add_field(name="Bank", value=f"{user_data['bank']} 🏦")
        
        await ctx.send(embed=embed)

    @commands.command(name="fraud")
    async def fraud(self, ctx):
        """Spróbuj oszukać system (30% szans na niepowodzenie)"""
        if not self.check_cooldown(ctx.author.id, "fraud", self.fraud_cooldown):
            remaining = self.get_remaining_cooldown(ctx.author.id, "fraud", self.fraud_cooldown)
            await ctx.send(f"Musisz poczekać jeszcze {remaining} sekund przed kolejną próbą oszustwa!")
            return

        user_data = get_user_data(ctx.author.id, ctx.guild.id)
        if not user_data:
            return

        # 30% szans na niepowodzenie
        if random.random() < 0.3:
            # Zabierz 30% balansu
            lost = int(user_data['wallet'] * 0.3)
            new_wallet = user_data['wallet'] - lost
            update_user_data(ctx.author.id, ctx.guild.id, wallet=new_wallet)
            self.set_cooldown(ctx.author.id, "fraud")

            embed = discord.Embed(
                title="Nieudane oszustwo!",
                description=f"Próba oszustwa się nie powiodła! Straciłeś {lost} monet!",
                color=discord.Color.red()
            )
            embed.add_field(name="Gotówka", value=f"{new_wallet} 💰")
            embed.add_field(name="Bank", value=f"{user_data['bank']} 🏦")
            
            await ctx.send(embed=embed)
        else:
            # 3x więcej niż z work
            earned = random.randint(*self.work_amount_range) * 3
            new_wallet = user_data['wallet'] + earned
            update_user_data(ctx.author.id, ctx.guild.id, wallet=new_wallet)
            self.set_cooldown(ctx.author.id, "fraud")

            embed = discord.Embed(
                title="Udane oszustwo!",
                description=f"Oszustwo się powiodło! Zarobiłeś {earned} monet!",
                color=discord.Color.green()
            )
            embed.add_field(name="Gotówka", value=f"{new_wallet} 💰")
            embed.add_field(name="Bank", value=f"{user_data['bank']} 🏦")
            
            await ctx.send(embed=embed)

    @commands.command(name="balance")
    async def balance(self, ctx, member: discord.Member = None):
        """Sprawdź stan konta"""
        member = member or ctx.author
        user_data = get_user_data(member.id, ctx.guild.id)
        
        if not user_data:
            await ctx.send("Nie udało się pobrać danych użytkownika.")
            return

        embed = discord.Embed(
            title=f"Stan konta {member.name}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Gotówka", value=f"{user_data['wallet']} 💰")
        embed.add_field(name="Bank", value=f"{user_data['bank']} 🏦")
        embed.add_field(name="Suma", value=f"{user_data['wallet'] + user_data['bank']} 💎")
        
        await ctx.send(embed=embed)

    @commands.command(name="deposit", aliases=["dep"])
    async def deposit(self, ctx, amount: str):
        """Wpłać pieniądze do banku"""
        user_data = get_user_data(ctx.author.id, ctx.guild.id)
        if not user_data:
            return

        if amount.lower() == "all":
            amount = user_data['wallet']
        else:
            try:
                amount = int(amount)
            except ValueError:
                await ctx.send("Podaj prawidłową kwotę lub 'all'!")
                return

        if amount <= 0:
            await ctx.send("Kwota musi być większa od 0!")
            return

        if amount > user_data['wallet']:
            await ctx.send("Nie masz wystarczająco pieniędzy w gotówce!")
            return

        new_wallet = user_data['wallet'] - amount
        new_bank = user_data['bank'] + amount
        update_user_data(ctx.author.id, ctx.guild.id, wallet=new_wallet, bank=new_bank)

        embed = discord.Embed(
            title="Wpłata do banku",
            description=f"Wpłaciłeś {amount} monet do banku!",
            color=discord.Color.green()
        )
        embed.add_field(name="Gotówka", value=f"{new_wallet} 💰")
        embed.add_field(name="Bank", value=f"{new_bank} 🏦")
        
        await ctx.send(embed=embed)

    @commands.command(name="withdraw", aliases=["with"])
    async def withdraw(self, ctx, amount: str):
        """Wypłać pieniądze z banku"""
        user_data = get_user_data(ctx.author.id, ctx.guild.id)
        if not user_data:
            return

        if amount.lower() == "all":
            amount = user_data['bank']
        else:
            try:
                amount = int(amount)
            except ValueError:
                await ctx.send("Podaj prawidłową kwotę lub 'all'!")
                return

        if amount <= 0:
            await ctx.send("Kwota musi być większa od 0!")
            return

        if amount > user_data['bank']:
            await ctx.send("Nie masz wystarczająco pieniędzy w banku!")
            return

        new_wallet = user_data['wallet'] + amount
        new_bank = user_data['bank'] - amount
        update_user_data(ctx.author.id, ctx.guild.id, wallet=new_wallet, bank=new_bank)

        embed = discord.Embed(
            title="Wypłata z banku",
            description=f"Wypłaciłeś {amount} monet z banku!",
            color=discord.Color.green()
        )
        embed.add_field(name="Gotówka", value=f"{new_wallet} 💰")
        embed.add_field(name="Bank", value=f"{new_bank} 🏦")
        
        await ctx.send(embed=embed)

    @commands.command(name="rob")
    async def rob(self, ctx, member: discord.Member):
        """Spróbuj ukraść pieniądze innemu użytkownikowi (70% szans na niepowodzenie)"""
        if member.id == ctx.author.id:
            await ctx.send("Nie możesz okraść samego siebie!")
            return

        if member.bot:
            await ctx.send("Nie możesz okraść bota!")
            return

        user_data = get_user_data(ctx.author.id, ctx.guild.id)
        target_data = get_user_data(member.id, ctx.guild.id)

        if not user_data or not target_data:
            await ctx.send("Nie udało się pobrać danych użytkowników.")
            return

        if target_data['wallet'] < 100:
            await ctx.send("Ten użytkownik nie ma wystarczająco pieniędzy w gotówce!")
            return

        # 70% szans na niepowodzenie
        if random.random() < 0.7:
            # Kara za nieudaną próbę
            fine = random.randint(100, 500)
            new_wallet = user_data['wallet'] - fine
            update_user_data(ctx.author.id, ctx.guild.id, wallet=new_wallet)

            embed = discord.Embed(
                title="Nieudana próba kradzieży!",
                description=f"Zostałeś złapany podczas próby kradzieży! Zapłaciłeś {fine} monet kary!",
                color=discord.Color.red()
            )
            embed.add_field(name="Gotówka", value=f"{new_wallet} 💰")
            embed.add_field(name="Bank", value=f"{user_data['bank']} 🏦")
            
            await ctx.send(embed=embed)
        else:
            # Sukces - zabierz do 70% gotówki
            stolen = int(target_data['wallet'] * random.uniform(0.1, 0.7))
            new_target_wallet = target_data['wallet'] - stolen
            new_robber_wallet = user_data['wallet'] + stolen

            update_user_data(member.id, ctx.guild.id, wallet=new_target_wallet)
            update_user_data(ctx.author.id, ctx.guild.id, wallet=new_robber_wallet)

            embed = discord.Embed(
                title="Udana kradzież!",
                description=f"Ukradłeś {stolen} monet od {member.name}!",
                color=discord.Color.green()
            )
            embed.add_field(name="Gotówka", value=f"{new_robber_wallet} 💰")
            embed.add_field(name="Bank", value=f"{user_data['bank']} 🏦")
            
            await ctx.send(embed=embed)

    @commands.command(name="shop")
    async def shop(self, ctx):
        """Wyświetl sklep"""
        items = get_shop_items(ctx.guild.id)
        
        if not items:
            await ctx.send("W sklepie nie ma żadnych przedmiotów!")
            return

        embed = discord.Embed(
            title="Sklep",
            color=discord.Color.blue()
        )

        for item in items:
            embed.add_field(
                name=f"{item['item_name']} - {item['price']} 💰",
                value=item['description'],
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name="buy")
    async def buy(self, ctx, item_name: str):
        """Kup przedmiot ze sklepu"""
        items = get_shop_items(ctx.guild.id)
        item = next((item for item in items if item['item_name'].lower() == item_name.lower()), None)

        if not item:
            await ctx.send("Nie znaleziono takiego przedmiotu w sklepie!")
            return

        user_data = get_user_data(ctx.author.id, ctx.guild.id)
        if not user_data:
            return

        if user_data['wallet'] < item['price']:
            await ctx.send("Nie masz wystarczająco pieniędzy w gotówce!")
            return

        new_wallet = user_data['wallet'] - item['price']
        update_user_data(ctx.author.id, ctx.guild.id, wallet=new_wallet)

        embed = discord.Embed(
            title="Zakup",
            description=f"Kupiłeś {item['item_name']} za {item['price']} monet!",
            color=discord.Color.green()
        )
        embed.add_field(name="Gotówka", value=f"{new_wallet} 💰")
        embed.add_field(name="Bank", value=f"{user_data['bank']} 🏦")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot)) 