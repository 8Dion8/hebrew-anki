from hebrew.chars import CHARS
import genanki
import telebot as tb
import os
from googletrans import Translator

TL = Translator()

TOKEN = os.environ.get('TOKEN')
bot = tb.TeleBot(TOKEN, parse_mode='MARKDOWN')

curPack = ""

bot.send_message(741069625, "Bot online.")

def get_pairs(id):
    with open(f"{id}.txt", "r") as f:
        file_contents = f.readlines()
    
    pairs = []

    for line in file_contents:
        if "," in line:
            pairs.append([i.strip() for i in line.split(",")])
    

    return pairs

@bot.message_handler(commands=["start", "help"])
def start(message):
    chat_id = message.chat.id

    bot.send_message(chat_id, "!שלום\nЯ бот для легкого добавления своего словарика иврита в карточки Anki. Вот что пока что можно со мной делать:")
    bot.send_message(chat_id, "• Прислать мне пару слов в формате `<слово на иврите>, <слово на русском>`\nНапример:\n`привет, שלום`\nЭто автоматически добавит эту пару слов в ваш словарик.")
    bot.send_message(chat_id, "• Также можно попробовать прислать только одно слово, либо на иврите либо на русском. В таком случае я попробую его перевести, но пока что это очень легко и быстро ломается :)")
    bot.send_message(chat_id, "• Команда `/generate` автоматически создаст вам .anki файл, который можно открыть/импортировать в вашем любимом клиенте Anki. Для Андроид, например, я советую AnkiDroid.")
    bot.send_message(chat_id, "• Команда `/dictionary` пришлет вам список всего вашего словаря. Посмотрев на него, можно использовать команду `/delete` для удаления слова из словаря.")
    bot.send_message(chat_id, "• В любое время вы можете написать /help чтобы получить эти сообщения еще раз, или открывть меню справа от клавиатуры чтобы получить краткое описание всех команд. По любым вопросам или предложениям - пишите мне в @mus1c1smysan1ty\n\n[Github](https://github.com/8Dion8/hebrew-anki)")
    

@bot.message_handler(commands=["gen", "generate"])
def generate(message):
    text = message.text
    chat_id = message.chat.id
    words = get_pairs(chat_id)

    model_id = 4607392319
    model = genanki.Model(
        model_id,
        'Main Model',
        fields=[
            {'name': 'ru_word'},
            {'name': 'hb_word'},
        ],
        templates=[
            
            {
                'name': 'Card 1',
                'qfmt': '{{hb_word}}\n\n{{type:ru_word}}',
                'afmt': '{{hb_word}}\n\n<hr id=answer>\n\n{{type:ru_word}}',
            },
            {
                'name': 'Card 2',
                'qfmt': '{{ru_word}}\n\n{{type:hb_word}}',
                'afmt': '{{ru_word}}\n\n<hr id=answer>\n\n{{type:hb_word}}',
            },
        ]
    )

    deck_id = 46712933121
    deck = genanki.Deck(deck_id, "hb test")


    for pair in words:
        if pair != [""]:
            note = genanki.Note(
                model = model,
                fields = [pair[0], pair[1]]
            )
            deck.add_note(note)

    genanki.Package(deck).write_to_file(f"{chat_id}.apkg")

    with open(f"{chat_id}.apkg", "rb") as f:
        bot.send_document(chat_id, f)

@bot.message_handler(commands=["list", "dict", "dictionary"])
def dictionary(message):
    chat_id = message.chat.id
    words = get_pairs(chat_id)

    message = ""

    for i in range(len(words)):
        pair = words[i]
        hb_word = pair[1]
        ru_word = pair[0]

        message += f"{i}. {hb_word} ({ru_word})\n"
    
    bot.send_message(chat_id, message)

@bot.message_handler(commands=["del", "delete", "remove"])
def delete(message):
    chat_id = message.chat.id
    word = " ".join(message.text.split(" ")[1:])

    dictionary = get_pairs(chat_id)

    org_len = len(dictionary)

    with open(f"{chat_id}.txt", "w") as f:

        for pair in dictionary:
            hb_word = pair[1]
            ru_word = pair[0]

            if word != hb_word and word != ru_word:
                f.write(",".join(pair)+"\n")

    new_len = len(get_pairs(chat_id))
    
    if org_len > new_len:
        bot.send_message(chat_id, f"Слово '{word}' удалено.")
    else:
        bot.send_message(chat_id, f"Слово '{word}' не найдено!")

@bot.message_handler(func=lambda msg: True)
def main_react(message):
    text = message.text.strip()
    chat_id = message.chat.id
    if "," in text:
        words = text.split(",")
        if words[0].strip()[0] in CHARS:
            hb_word = words[0].strip()
            ru_word = words[1].strip()
        elif words[1].strip()[0] in CHARS:
            hb_word = words[1].strip()
            ru_word = words[0].strip()
        else:
            bot.send_message(chat_id, "Не найдено слова на иврите!")
            return
    else:
        if text[0] in CHARS:
            og_message = bot.send_message(chat_id, "Попытка перевести на русский...\n(Эта фича до конца не протестирована и легко ломается! :p)")
            try:
                translated = TL.translate(text, dest="ru").__dict__()["text"].lower()
            except Exception as e:
                bot.send_message(chat_id, "Что-то пошло не так.")
                bot.send_message(741069625, e)
                return
            
            bot.delete_message(chat_id, og_message.message_id)
            hb_word = text.strip()
            ru_word = translated.strip()
        else:
            og_message = bot.send_message(chat_id, "Попытка перевести на иврит...\n(Эта фича до конца не протестирована и легко ломается! :p)")
            try:
                translated = TL.translate(text, dest="iw").__dict__()["text"].lower()
            except Exception as e:
                bot.send_message(chat_id, "Что-то пошло не так.")
                bot.send_message(741069625, e)
                return
            
            bot.delete_message(chat_id, og_message.message_id)
            ru_word = text.strip()
            hb_word = translated.strip()
            
        
    for pair in get_pairs(chat_id):
        if hb_word == pair[1]:
            bot.send_message(chat_id, "У вас уже есть это слово в словаре!")
            return
    
    with open(f"{chat_id}.txt", "a") as f:
        f.write(f"{ru_word},{hb_word}\n")
    
    bot.send_message(chat_id, f"Добавлена пара {ru_word} - {hb_word}")
    



bot.infinity_polling()