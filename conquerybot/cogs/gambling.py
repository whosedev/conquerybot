import discord
from discord.ext import commands
import random
from conquerybot.utils.database import get_user_data, update_user_data
from discord.ui import Button, View

class BlackjackView(View):
    def __init__(self, game_instance, ctx):
        super().__init__(timeout=60)  # 60 sekund na ruch
        self.game_instance = game_instance
        self.ctx = ctx
        self.message = None

    @discord.ui.button(label="Hit 🎯", style=discord.ButtonStyle.primary)
    async def hit_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("To nie twoja gra!", ephemeral=True)
            return

        await interaction.response.defer()
        await self.game_instance.hit_action(self.ctx, self, interaction)

    @discord.ui.button(label="Stand 🛑", style=discord.ButtonStyle.danger)
    async def stand_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("To nie twoja gra!", ephemeral=True)
            return

        await interaction.response.defer()
        await self.game_instance.stand_action(self.ctx, self, interaction)

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)
            await self.ctx.send("⏰ Czas na ruch minął! Gra zakończona.")
            if self.ctx.author.id in self.game_instance.blackjack_games:
                game = self.game_instance.blackjack_games[self.ctx.author.id]
                await self.game_instance.update_balance(str(self.ctx.author.id), -game['bet'])
                del self.game_instance.blackjack_games[self.ctx.author.id]

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blackjack_games = {}

    def get_balance(self, user_id):
        """Pobiera stan konta użytkownika"""
        user_data = get_user_data(user_id)
        if not user_data:
            return 0
        return user_data.get('wallet', 0)

    async def update_balance(self, user_id, amount):
        """Aktualizuje stan konta użytkownika"""
        user_data = get_user_data(user_id)
        if not user_data:
            user_data = {'user_id': user_id, 'wallet': 0, 'bank': 0}
        user_data['wallet'] = max(0, user_data['wallet'] + amount)
        update_user_data(user_id, user_data)
        return user_data['wallet']

    @commands.command(name="roulette", aliases=["ruletka"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def roulette(self, ctx, bet: int, choice: str):
        """Zagraj w ruletkę
        Użyj: !roulette <kwota> <wybór>
        Wybory:
        - red/black (2x)
        - even/odd (2x)
        - high/low (2x)
        - number 0-36 (35x)"""
        
        if bet <= 0:
            await ctx.send("❌ Minimalna stawka to 1 moneta!")
            return

        balance = self.get_balance(str(ctx.author.id))
        if balance < bet:
            await ctx.send("❌ Nie masz wystarczająco monet w portfelu!")
            return

        # Wylosuj numer
        number = random.randint(0, 36)
        color = "red" if number in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36] else "black" if number != 0 else "green"
        is_even = number % 2 == 0 and number != 0
        is_high = number >= 19 and number != 0

        # Sprawdź wygraną
        won = False
        multiplier = 0
        if choice.lower() in ["red", "black", "czerwone", "czarne"]:
            if (choice.lower() in ["red", "czerwone"] and color == "red") or \
               (choice.lower() in ["black", "czarne"] and color == "black"):
                won = True
                multiplier = 2
        elif choice.lower() in ["even", "odd", "parzyste", "nieparzyste"]:
            if (choice.lower() in ["even", "parzyste"] and is_even) or \
               (choice.lower() in ["odd", "nieparzyste"] and not is_even):
                won = True
                multiplier = 2
        elif choice.lower() in ["high", "low", "wysokie", "niskie"]:
            if (choice.lower() in ["high", "wysokie"] and is_high) or \
               (choice.lower() in ["low", "niskie"] and not is_high):
                won = True
                multiplier = 2
        elif choice.isdigit() and 0 <= int(choice) <= 36:
            if number == int(choice):
                won = True
                multiplier = 35

        # Aktualizuj saldo
        if won:
            winnings = bet * multiplier
            await self.update_balance(str(ctx.author.id), winnings - bet)
            embed = discord.Embed(
                title="🎰 Ruletka - WYGRANA!",
                description=f"Wypadło: {number} ({color})\nWygrałeś {winnings} monet!",
                color=discord.Color.green()
            )
        else:
            await self.update_balance(str(ctx.author.id), -bet)
            embed = discord.Embed(
                title="🎰 Ruletka - Przegrana",
                description=f"Wypadło: {number} ({color})\nPrzegrałeś {bet} monet.",
                color=discord.Color.red()
            )

        new_balance = self.get_balance(str(ctx.author.id))
        embed.add_field(name="Stan konta", value=f"Portfel: {new_balance}")
        await ctx.send(embed=embed)

    @commands.command(name="dice", aliases=["kostka"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dice(self, ctx, bet: int, choice: str):
        """Zagraj w kości
        Użyj: !dice <kwota> <wybór>
        Wybory: high (4-6) / low (1-3)"""
        
        if bet <= 0:
            await ctx.send("❌ Minimalna stawka to 1 moneta!")
            return

        balance = self.get_balance(str(ctx.author.id))
        if balance < bet:
            await ctx.send("❌ Nie masz wystarczająco monet w portfelu!")
            return

        if choice.lower() not in ["high", "low", "wysokie", "niskie"]:
            await ctx.send("❌ Wybierz 'high/wysokie' (4-6) lub 'low/niskie' (1-3)!")
            return

        # Rzut kością
        roll = random.randint(1, 6)
        is_high = roll >= 4

        # Sprawdź wygraną
        won = False
        if (choice.lower() in ["high", "wysokie"] and is_high) or \
           (choice.lower() in ["low", "niskie"] and not is_high):
            won = True

        # Aktualizuj saldo
        if won:
            await self.update_balance(str(ctx.author.id), bet)
            embed = discord.Embed(
                title="🎲 Kości - WYGRANA!",
                description=f"Wypadło: {roll}\nWygrałeś {bet} monet!",
                color=discord.Color.green()
            )
        else:
            await self.update_balance(str(ctx.author.id), -bet)
            embed = discord.Embed(
                title="🎲 Kości - Przegrana",
                description=f"Wypadło: {roll}\nPrzegrałeś {bet} monet.",
                color=discord.Color.red()
            )

        new_balance = self.get_balance(str(ctx.author.id))
        embed.add_field(name="Stan konta", value=f"Portfel: {new_balance}")
        await ctx.send(embed=embed)

    @commands.command(name="blackjack", aliases=["bj"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def blackjack(self, ctx, bet: int):
        """Zagraj w blackjacka
        Użyj: !blackjack <kwota>"""
        
        if bet <= 0:
            await ctx.send("❌ Minimalna stawka to 1 moneta!")
            return

        balance = self.get_balance(str(ctx.author.id))
        if balance < bet:
            await ctx.send("❌ Nie masz wystarczająco monet w portfelu!")
            return

        # Jeśli gracz już gra
        if ctx.author.id in self.blackjack_games:
            await ctx.send("❌ Już grasz w blackjacka!")
            return

        # Przygotuj talię
        deck = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'] * 4
        random.shuffle(deck)

        # Rozdaj karty
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        # Zapisz stan gry
        self.blackjack_games[ctx.author.id] = {
            'deck': deck,
            'player_hand': player_hand,
            'dealer_hand': dealer_hand,
            'bet': bet,
            'status': 'playing'
        }

        # Pokaż karty
        embed = discord.Embed(
            title="🃏 Blackjack",
            description="Twoje karty: " + " ".join(player_hand) + f" (Suma: {self.calculate_hand(player_hand)})\n" +
                      "Karta krupiera: " + dealer_hand[0] + " [?]",
            color=discord.Color.blue()
        )
        embed.add_field(name="Stawka", value=f"{bet} monet")
        
        # Stwórz widok z przyciskami
        view = BlackjackView(self, ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    def calculate_hand(self, hand):
        """Oblicza sumę kart w ręce"""
        value = 0
        aces = 0
        for card in hand:
            if card in ['J', 'Q', 'K']:
                value += 10
            elif card == 'A':
                aces += 1
            else:
                value += int(card)
        
        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
        
        return value

    async def hit_action(self, ctx, view: BlackjackView, interaction: discord.Interaction):
        """Akcja po wciśnięciu przycisku Hit"""
        game = self.blackjack_games[ctx.author.id]
        
        # Dobierz kartę
        game['player_hand'].append(game['deck'].pop())
        player_value = self.calculate_hand(game['player_hand'])

        # Sprawdź czy gracz przegrał
        if player_value > 21:
            await self.update_balance(str(ctx.author.id), -game['bet'])
            embed = discord.Embed(
                title="🃏 Blackjack - Przegrana!",
                description=f"Twoje karty: {' '.join(game['player_hand'])} (Suma: {player_value})\n" +
                          f"Karty krupiera: {' '.join(game['dealer_hand'])} (Suma: {self.calculate_hand(game['dealer_hand'])})",
                color=discord.Color.red()
            )
            embed.add_field(name="Wynik", value=f"Przegrałeś {game['bet']} monet!")
            
            # Wyłącz przyciski
            for item in view.children:
                item.disabled = True
            await interaction.message.edit(embed=embed, view=view)
            
            del self.blackjack_games[ctx.author.id]
        else:
            embed = discord.Embed(
                title="🃏 Blackjack",
                description=f"Twoje karty: {' '.join(game['player_hand'])} (Suma: {player_value})\n" +
                          f"Karta krupiera: {game['dealer_hand'][0]} [?]",
                color=discord.Color.blue()
            )
            embed.add_field(name="Stawka", value=f"{game['bet']} monet")
            await interaction.message.edit(embed=embed, view=view)

    async def stand_action(self, ctx, view: BlackjackView, interaction: discord.Interaction):
        """Akcja po wciśnięciu przycisku Stand"""
        game = self.blackjack_games[ctx.author.id]
        
        # Krupier dobiera karty
        dealer_value = self.calculate_hand(game['dealer_hand'])
        while dealer_value < 17:
            game['dealer_hand'].append(game['deck'].pop())
            dealer_value = self.calculate_hand(game['dealer_hand'])

        # Sprawdź wynik
        player_value = self.calculate_hand(game['player_hand'])
        
        if dealer_value > 21 or player_value > dealer_value:
            # Wygrana gracza
            await self.update_balance(str(ctx.author.id), game['bet'])
            embed = discord.Embed(
                title="🃏 Blackjack - WYGRANA!",
                description=f"Twoje karty: {' '.join(game['player_hand'])} (Suma: {player_value})\n" +
                          f"Karty krupiera: {' '.join(game['dealer_hand'])} (Suma: {dealer_value})",
                color=discord.Color.green()
            )
            embed.add_field(name="Wynik", value=f"Wygrałeś {game['bet']} monet!")
        elif player_value < dealer_value:
            # Wygrana krupiera
            await self.update_balance(str(ctx.author.id), -game['bet'])
            embed = discord.Embed(
                title="🃏 Blackjack - Przegrana",
                description=f"Twoje karty: {' '.join(game['player_hand'])} (Suma: {player_value})\n" +
                          f"Karty krupiera: {' '.join(game['dealer_hand'])} (Suma: {dealer_value})",
                color=discord.Color.red()
            )
            embed.add_field(name="Wynik", value=f"Przegrałeś {game['bet']} monet!")
        else:
            # Remis
            embed = discord.Embed(
                title="🃏 Blackjack - Remis",
                description=f"Twoje karty: {' '.join(game['player_hand'])} (Suma: {player_value})\n" +
                          f"Karty krupiera: {' '.join(game['dealer_hand'])} (Suma: {dealer_value})",
                color=discord.Color.blue()
            )
            embed.add_field(name="Wynik", value="Remis! Odzyskujesz swoją stawkę.")

        # Wyłącz przyciski
        for item in view.children:
            item.disabled = True
        await interaction.message.edit(embed=embed, view=view)
        
        del self.blackjack_games[ctx.author.id]

    @commands.command(name="coinflip", aliases=["cf", "moneta"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def coinflip(self, ctx, bet: int, choice: str):
        """Rzut monetą
        Użyj: !coinflip <kwota> <wybór>
        Wybory: heads/tails (orzeł/reszka)"""
        
        if bet <= 0:
            await ctx.send("❌ Minimalna stawka to 1 moneta!")
            return

        balance = self.get_balance(str(ctx.author.id))
        if balance < bet:
            await ctx.send("❌ Nie masz wystarczająco monet w portfelu!")
            return

        if choice.lower() not in ["heads", "tails", "orzeł", "reszka"]:
            await ctx.send("❌ Wybierz 'heads/orzeł' lub 'tails/reszka'!")
            return

        # Rzut monetą
        result = random.choice(["heads", "tails"])
        won = (choice.lower() in ["heads", "orzeł"] and result == "heads") or \
              (choice.lower() in ["tails", "reszka"] and result == "tails")

        # Aktualizuj saldo
        if won:
            await self.update_balance(str(ctx.author.id), bet)
            embed = discord.Embed(
                title="🪙 Moneta - WYGRANA!",
                description=f"Wypadło: {'orzeł' if result == 'heads' else 'reszka'}\nWygrałeś {bet} monet!",
                color=discord.Color.green()
            )
        else:
            await self.update_balance(str(ctx.author.id), -bet)
            embed = discord.Embed(
                title="🪙 Moneta - Przegrana",
                description=f"Wypadło: {'orzeł' if result == 'heads' else 'reszka'}\nPrzegrałeś {bet} monet.",
                color=discord.Color.red()
            )

        new_balance = self.get_balance(str(ctx.author.id))
        embed.add_field(name="Stan konta", value=f"Portfel: {new_balance}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Gambling(bot)) 