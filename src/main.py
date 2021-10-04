import re
import json
from pathlib import Path

from pyrogram import Client, filters, emoji

from slugify import slugify


GROUP_NAME = "Fiangonana Ambodirano"
BOOK_LIST = Path() / "src/book/"
app = Client('Ambodirano')


@app.on_message(filters.command("andininteny"))
async def andininteny(ctx, message):
    boky = message.command[1]
    toko = int(message.command[2].split(":")[0])
    andininy = list(map(int, message.command[2].split(":")[1].split(",")))[0]

    def book(name:str):
        book = BOOK_LIST / f"{slugify(name)}.json"
        with open(book, "r") as fp:
            loaded = json.load(fp)

        return loaded

    def chap(name:str, chapter:int):
        return book(name)[str(chapter)]

    verset = chap(boky, toko)[str(andininy)]
    order = book(boky)['meta']['order'] + 1
    URL = f"https://www.jw.org/finder?wtlocale=MG&pub=bi12&srctype=wol&bible={order:03}{toko:03}{andininy:03}&srcid=share"

    title = f"[{boky.title()} {toko}:{andininy}]({URL})"
    await message.reply(f"**{title}**\n{verset}", disable_web_page_preview=True)


# Filter in only new_chat_members updates generated in TARGET chat
@app.on_message(filters.chat(GROUP_NAME) & filters.new_chat_members)
async def welcome(client, message):
    # Build the new members list (with mentions) by using their first_name
    new_members = [u.mention for u in message.new_chat_members]

    MESSAGE = "{} Tongasoa {} ato amin'ny groupe telegram ny Fiangonana Ambodirano!"
    # Build the welcome message by using an emoji and the list we built above
    text = MESSAGE.format(emoji.SPARKLES, ", ".join(new_members))

    message.reply_text(text)

app.run()
