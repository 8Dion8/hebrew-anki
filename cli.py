from hebrew import Hebrew
from hebrew.chars import CHARS
from googletrans import Translator
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import FirefoxOptions
from time import sleep
import genanki

from httpcore._exceptions import ReadTimeout
from selenium.common.exceptions import NoSuchElementException

running = True

TL = Translator()

opts = FirefoxOptions()
opts.add_argument("--headless")
driver = webdriver.Firefox(executable_path="geckodriver", options=opts)
driver.get("https://www.pealim.com/ru/search")

ru_words = []
hb_words = []

deck_name = input("Enter Deck Name: ")

while running:
    word_is_hebrew = False
    word = input("Enter a word: ")
    
    if word == "/":
        running = False
        break

    i = 1

    if word[0] in CHARS.keys():
        while True:
            print(f"Attempting translate #{i}")
            hebrew_word = word
            russian_word = TL.translate(hebrew_word, dest="iw")
            if russian_word is not None:
                russian_word = russian_word.__dict__()["text"]
                break
            else:
                i += 1


    else:
        while True:
            print(f"Attempting translate #{i}")
            russian_word = word
            try:
                hebrew_word = TL.translate(russian_word, dest="iw")
            except (ReadTimeout, TypeError) as e:
                i += 1
                continue
            if hebrew_word is not None:
                hebrew_word = hebrew_word.__dict__()["text"]
                break
            else:
                i += 1


    ru_words.append(russian_word)
    hb_words.append(hebrew_word)

    print(f"Found translation ({russian_word} - {hebrew_word})")

final_hb = []
final_ru = []

for word_index in range(len(hb_words)):
    hb_word = hb_words[word_index]
    
    print(f"Finding word '{hb_word}'")

    word_input = driver.find_element("id", "search-box")
    word_input.send_keys(hb_word)
    word_input.send_keys(Keys.RETURN)
    sleep(1)
    try:
        word_info = driver.find_element("xpath", "/html/body/div/div[2]/div[3]/div[2]/div[1]/div[3]").text
        word_type = word_info.split(" ")[1]
        if word_type ==  "глагол":
            driver.find_element("xpath", "/html/body/div/div[2]/div[3]/div[2]/div[1]/div[5]/a").click()
        
            hb_word_cur_form = driver.find_element("xpath", "/html/body/div/div[2]/div[3]/table/tbody/tr[1]/td[1]/div/div/div[1]/span").text
            hb_word_inf_form = driver.find_element("xpath", "/html/body/div/div[2]/div[3]/table/tbody/tr[9]/td/div/div/div[1]/span").text
            ru_word_cur_form = TL.translate(hb_word_cur_form, dest="ru")
            ru_word_inf_form = driver.find_element("xpath", "/html/body/div/div[2]/div[2]").text
        
            final_hb.extend([hb_word_inf_form, hb_word_cur_form])
            final_ru.extend([ru_word_inf_form, ru_word_cur_form])

        else:
            hb_word_final = driver.find_element("xpath", "/html/body/div/div[2]/div[3]/div[2]/div[1]/div[1]/a/div/div/span").text
            final_hb.append(hb_word_final)
            final_ru.append(ru_words[word_index])
    except NoSuchElementException:
        final_hb.append(hb_word)
        final_ru.append(ru_words[word_index])


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

deck_id = 46712933122
deck = genanki.Deck(deck_id, "hb first test")


for i in range(len(final_hb)):
    print(f"Adding note for {final_hb[i]}")
    note = genanki.Note(
        model = model,
        fields = [final_ru[i], final_hb[i]]
    )
    deck.add_note(note)

genanki.Package(deck).write_to_file(f"{deck_name}.apkg")

driver.close()
