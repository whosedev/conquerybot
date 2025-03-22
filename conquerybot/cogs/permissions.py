import discord
from discord.ext import commands

class Permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="picperms")
    async def picperms(self, ctx):
        """Sprawdza uprawnienia do wysyłania zdjęć i GIFów"""
        member = ctx.author
        print(f"\nSprawdzanie uprawnień dla użytkownika: {member.name}")
        print(f"ID użytkownika: {member.id}")
        
        # Sprawdź czy użytkownik ma .gg/conquery w statusie
        has_perms = False
        
        # Debug informacji o użytkowniku
        print(f"Status: {member.status}")
        print(f"Raw status: {member.raw_status}")
        print(f"Mobile status: {member.mobile_status}")
        print(f"Desktop status: {member.desktop_status}")
        print(f"Web status: {member.web_status}")
        
        # Sprawdź aktywności
        if hasattr(member, 'activities'):
            print(f"Liczba aktywności: {len(member.activities)}")
            for activity in member.activities:
                print(f"\nAktywność typu: {type(activity)}")
                print(f"Nazwa aktywności: {activity.name if hasattr(activity, 'name') else 'Brak nazwy'}")
                print(f"Stan aktywności: {activity.state if hasattr(activity, 'state') else 'Brak stanu'}")
                print(f"Szczegóły: {activity.details if hasattr(activity, 'details') else 'Brak szczegółów'}")
                
                # Sprawdź wszystkie atrybuty aktywności
                for attr in dir(activity):
                    if not attr.startswith('_'):  # Pomijamy prywatne atrybuty
                        try:
                            value = getattr(activity, attr)
                            if isinstance(value, (str, int, bool)):
                                print(f"Atrybut {attr}: {value}")
                        except:
                            pass
                
                # Sprawdź czy zawiera .gg/conquery
                if hasattr(activity, 'name') and activity.name and ".gg/conquery" in str(activity.name).lower():
                    print("Znaleziono .gg/conquery w nazwie")
                    has_perms = True
                    break
                
                if hasattr(activity, 'state') and activity.state and ".gg/conquery" in str(activity.state).lower():
                    print("Znaleziono .gg/conquery w stanie")
                    has_perms = True
                    break
                
                if hasattr(activity, 'details') and activity.details and ".gg/conquery" in str(activity.details).lower():
                    print("Znaleziono .gg/conquery w szczegółach")
                    has_perms = True
                    break
        else:
            print("Brak dostępu do aktywności użytkownika")
        
        print(f"Czy ma uprawnienia: {has_perms}")
        
        if has_perms:
            # Nadaj uprawnienia
            try:
                role = discord.utils.get(ctx.guild.roles, name="pic perms")
                print(f"Znaleziona rola: {role}")
                
                if role:
                    await member.add_roles(role)
                    print("Rola została dodana")
                    embed = discord.Embed(
                        title="✅ Uprawnienia nadane!",
                        description="Możesz teraz wysyłać zdjęcia i GIFy na czacie!",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed)
                else:
                    print("Rola nie została znaleziona")
                    await ctx.send("❌ Rola 'pic perms' nie została znaleziona. Skontaktuj się z administracją.")
            except Exception as e:
                print(f"Błąd podczas nadawania roli: {e}")
                await ctx.send("❌ Wystąpił błąd podczas nadawania uprawnień. Skontaktuj się z administracją.")
        else:
            # Wyświetl informację jak uzyskać uprawnienia
            embed = discord.Embed(
                title="📸 Jak uzyskać uprawnienia?",
                description="Aby uzyskać uprawnienia do wysyłania zdjęć i GIFów:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Krok 1",
                value="Ustaw swój status na Discord",
                inline=False
            )
            embed.add_field(
                name="Krok 2",
                value="Dodaj `.gg/conquery` do swojego statusu",
                inline=False
            )
            embed.add_field(
                name="Krok 3",
                value="Użyj komendy `!picperms` ponownie",
                inline=False
            )
            embed.set_footer(text="Po spełnieniu wymagań, uprawnienia zostaną nadane automatycznie!")
            
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Permissions(bot)) 