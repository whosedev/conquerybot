import discord
from discord.ext import commands
import os
import aiohttp
import tempfile
from PIL import Image
from moviepy.editor import VideoFileClip
import asyncio

class Gif(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gif_cooldown = commands.CooldownMapping.from_cooldown(1, 30, commands.BucketType.user)  # 30s cooldown

    async def download_attachment(self, attachment):
        """Pobiera załącznik do pliku tymczasowego"""
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as response:
                if response.status == 200:
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    temp_file.write(await response.read())
                    temp_file.close()
                    return temp_file.name
        return None

    async def convert_to_gif(self, file_path, is_video=False):
        """Konwertuje plik na GIF"""
        try:
            if is_video:
                # Konwersja wideo na GIF
                video = VideoFileClip(file_path)
                # Przycinamy wideo do 10 sekund jeśli jest dłuższe
                if video.duration > 10:
                    video = video.subclip(0, 10)
                # Konwertujemy na GIF
                gif_path = file_path + '.gif'
                video.write_gif(gif_path, fps=15)
                video.close()
            else:
                # Konwersja obrazu na GIF
                img = Image.open(file_path)
                gif_path = file_path + '.gif'
                img.save(gif_path, 'GIF')
                img.close()
            return gif_path
        except Exception as e:
            print(f"Błąd podczas konwersji: {e}")
            return None

    @commands.command(name="gifit")
    async def gifit(self, ctx):
        """Konwertuje załącznik na GIF"""
        # Sprawdź cooldown
        bucket = self.gif_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        
        if retry_after:
            await ctx.send(f"⏰ Musisz poczekać jeszcze {int(retry_after)}s przed kolejną konwersją!")
            return

        # Sprawdź czy wiadomość ma załącznik
        if not ctx.message.attachments:
            # Sprawdź czy wiadomość jest odpowiedzią na inną wiadomość
            if not ctx.message.reference:
                await ctx.send("❌ Musisz załączyć plik lub odpowiedzieć na wiadomość z plikiem!")
                return
            
            # Pobierz oryginalną wiadomość
            try:
                original_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                if not original_message.attachments:
                    await ctx.send("❌ Oryginalna wiadomość nie zawiera pliku!")
                    return
                attachment = original_message.attachments[0]
            except:
                await ctx.send("❌ Nie udało się pobrać oryginalnej wiadomości!")
                return
        else:
            attachment = ctx.message.attachments[0]

        # Sprawdź czy plik jest obrazem lub wideo
        content_type = attachment.content_type
        if not (content_type.startswith('image/') or content_type.startswith('video/')):
            await ctx.send("❌ Plik musi być obrazem lub wideo!")
            return

        # Wyślij wiadomość o rozpoczęciu konwersji
        processing_msg = await ctx.send("🔄 Przetwarzanie...")

        # Pobierz plik
        file_path = await self.download_attachment(attachment)
        if not file_path:
            await processing_msg.edit(content="❌ Nie udało się pobrać pliku!")
            return

        try:
            # Konwertuj na GIF
            is_video = content_type.startswith('video/')
            gif_path = await self.convert_to_gif(file_path, is_video)
            
            if not gif_path:
                await processing_msg.edit(content="❌ Nie udało się skonwertować pliku na GIF!")
                return

            # Wyślij GIF
            await ctx.send(file=discord.File(gif_path))
            await processing_msg.delete()

        except Exception as e:
            await processing_msg.edit(content=f"❌ Wystąpił błąd: {str(e)}")
        finally:
            # Wyczyść pliki tymczasowe
            try:
                os.unlink(file_path)
                if gif_path and os.path.exists(gif_path):
                    os.unlink(gif_path)
            except:
                pass

async def setup(bot):
    await bot.add_cog(Gif(bot)) 