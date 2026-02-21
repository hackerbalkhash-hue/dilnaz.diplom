# -*- coding: utf-8 -*-
"""Add new entries to vocabulary_extended.json"""
import json
from pathlib import Path

EXTRA = [
    {"word_kz": "абайлау", "translation_ru": "осторожность"},
    {"word_kz": "абыржу", "translation_ru": "волнение"},
    {"word_kz": "ада", "translation_ru": "имя"},
    {"word_kz": "айдар", "translation_ru": "чуб"},
    {"word_kz": "айналдыру", "translation_ru": "вращать"},
    {"word_kz": "ақтау", "translation_ru": "оправдывать"},
    {"word_kz": "ақшақар", "translation_ru": "барс"},
    {"word_kz": "алаңдау", "translation_ru": "волноваться"},
    {"word_kz": "алыпсатар", "translation_ru": "переводчик"},
    {"word_kz": "андат", "translation_ru": "заказ"},
    {"word_kz": "аңызшыл", "translation_ru": "сказочник"},
    {"word_kz": "арыз", "translation_ru": "заявление"},
    {"word_kz": "аса", "translation_ru": "переваливать"},
    {"word_kz": "асатаяқ", "translation_ru": "хромой"},
    {"word_kz": "асқақ", "translation_ru": "гордый"},
    {"word_kz": "ауаша", "translation_ru": "легко"},
    {"word_kz": "ауру", "translation_ru": "болезнь"},
    {"word_kz": "аурухана", "translation_ru": "больница"},
    {"word_kz": "аша", "translation_ru": "открывать"},
    {"word_kz": "ашулы", "translation_ru": "сердитый"},
    {"word_kz": "бағдарлау", "translation_ru": "программировать"},
    {"word_kz": "байыту", "translation_ru": "обогащать"},
    {"word_kz": "балапан", "translation_ru": "птенец"},
    {"word_kz": "басқару", "translation_ru": "управление"},
    {"word_kz": "басқарма", "translation_ru": "управление"},
    {"word_kz": "батырлық", "translation_ru": "героизм"},
    {"word_kz": "батыс", "translation_ru": "запад"},
    {"word_kz": "батыстық", "translation_ru": "западный"},
    {"word_kz": "баяндама", "translation_ru": "доклад"},
    {"word_kz": "белгілеу", "translation_ru": "отмечать"},
    {"word_kz": "белдеу", "translation_ru": "пояс"},
    {"word_kz": "бетпе-бет", "translation_ru": "лицом к лицу"},
    {"word_kz": "бітеу", "translation_ru": "глухой"},
    {"word_kz": "бүгінге дейін", "translation_ru": "до сегодня"},
    {"word_kz": "буырыл", "translation_ru": "закрыто"},
    {"word_kz": "бұрынғы", "translation_ru": "прежний"},
    {"word_kz": "дәуір", "translation_ru": "эпоха"},
    {"word_kz": "елеулі", "translation_ru": "существенный"},
    {"word_kz": "еліктеу", "translation_ru": "подражать"},
    {"word_kz": "ен", "translation_ru": "ширина"},
    {"word_kz": "епті", "translation_ru": "ловкий"},
    {"word_kz": "еркін", "translation_ru": "свободный"},
    {"word_kz": "жабық", "translation_ru": "закрытый"},
    {"word_kz": "жағымды", "translation_ru": "приятный"},
    {"word_kz": "жазық", "translation_ru": "вина"},
    {"word_kz": "жайлылық", "translation_ru": "удобство"},
    {"word_kz": "жақында", "translation_ru": "недавно"},
    {"word_kz": "жарақат", "translation_ru": "рана"},
    {"word_kz": "жарасымды", "translation_ru": "гармоничный"},
    {"word_kz": "жат", "translation_ru": "чужой"},
    {"word_kz": "жауапкершілік", "translation_ru": "ответственность"},
    {"word_kz": "жауапсыз", "translation_ru": "безответственный"},
    {"word_kz": "жеделдету", "translation_ru": "ускорить"},
    {"word_kz": "желтоқсан", "translation_ru": "декабрь"},
    {"word_kz": "жетекшілік", "translation_ru": "руководство"},
    {"word_kz": "жобалау", "translation_ru": "проектирование"},
    {"word_kz": "жұмсақ", "translation_ru": "мягкий"},
    {"word_kz": "жүрек", "translation_ru": "сердце"},
    {"word_kz": "зілзала", "translation_ru": "землетрясение"},
    {"word_kz": "ишара", "translation_ru": "знак"},
    {"word_kz": "кана", "translation_ru": "лишь бы"},
    {"word_kz": "қайнар", "translation_ru": "источник"},
    {"word_kz": "қайта құру", "translation_ru": "перестройка"},
    {"word_kz": "қалалық", "translation_ru": "городской"},
    {"word_kz": "қалып", "translation_ru": "форма"},
    {"word_kz": "қанағаттандыру", "translation_ru": "удовлетворять"},
    {"word_kz": "қарау", "translation_ru": "смотреть"},
    {"word_kz": "қасиетті", "translation_ru": "святой"},
    {"word_kz": "қатер", "translation_ru": "опасность"},
    {"word_kz": "қатты", "translation_ru": "твёрдый"},
    {"word_kz": "қауіпсіздік", "translation_ru": "безопасность"},
    {"word_kz": "қимылдау", "translation_ru": "двигаться"},
    {"word_kz": "қоғамдас", "translation_ru": "согражданин"},
    {"word_kz": "құжаттасу", "translation_ru": "документирование"},
    {"word_kz": "құлақ", "translation_ru": "ухо"},
    {"word_kz": "құмар", "translation_ru": "страстный"},
    {"word_kz": "құрбы", "translation_ru": "товарищ"},
    {"word_kz": "қызмет атқару", "translation_ru": "служить"},
    {"word_kz": "қысқаша", "translation_ru": "кратко"},
    {"word_kz": "қыстау", "translation_ru": "зимовать"},
    {"word_kz": "мазмұн", "translation_ru": "содержание"},
    {"word_kz": "мақтау", "translation_ru": "хвалить"},
    {"word_kz": "мәтіні", "translation_ru": "текстовый"},
    {"word_kz": "нарықтық", "translation_ru": "рыночный"},
    {"word_kz": "нәтижелілік", "translation_ru": "результативность"},
    {"word_kz": "нұсқа", "translation_ru": "вариант"},
    {"word_kz": "ойдан", "translation_ru": "мысленно"},
    {"word_kz": "ойыншы", "translation_ru": "игрок"},
    {"word_kz": "ойшыл", "translation_ru": "мыслитель"},
    {"word_kz": "орам", "translation_ru": "улица"},
    {"word_kz": "отырыс", "translation_ru": "заседание"},
    {"word_kz": "өзгермелі", "translation_ru": "изменчивый"},
    {"word_kz": "өлшем", "translation_ru": "размер"},
    {"word_kz": "өндірістік", "translation_ru": "производственный"},
    {"word_kz": "пайымдау", "translation_ru": "рассуждать"},
    {"word_kz": "салалық", "translation_ru": "отраслевой"},
    {"word_kz": "санаға", "translation_ru": "на память"},
    {"word_kz": "сапасы", "translation_ru": "по качеству"},
    {"word_kz": "серпін", "translation_ru": "импульс"},
    {"word_kz": "сұраным", "translation_ru": "запрос"},
    {"word_kz": "сұраныс", "translation_ru": "спрос"},
    {"word_kz": "сыншы", "translation_ru": "критик"},
    {"word_kz": "табыс", "translation_ru": "успех"},
    {"word_kz": "тағдыр", "translation_ru": "судьба"},
    {"word_kz": "таймас", "translation_ru": "неутомимый"},
    {"word_kz": "талдауыш", "translation_ru": "аналитик"},
    {"word_kz": "танымалдық", "translation_ru": "известность"},
    {"word_kz": "тартымды", "translation_ru": "привлекательный"},
    {"word_kz": "тәуір", "translation_ru": "привычный"},
    {"word_kz": "тілтаныс", "translation_ru": "языковед"},
    {"word_kz": "ұйым", "translation_ru": "организация"},
    {"word_kz": "ұқсас", "translation_ru": "похожий"},
    {"word_kz": "ұлттық болмыс", "translation_ru": "национальное бытие"},
    {"word_kz": "ұран", "translation_ru": "лозунг"},
    {"word_kz": "шығыстық", "translation_ru": "восточный"},
    {"word_kz": "шынайылық", "translation_ru": "истина"},
    {"word_kz": "эстетика", "translation_ru": "эстетика"},
    {"word_kz": "абыр","translation_ru":"затмение"},{"word_kz":"ағаш","translation_ru":"дерево"},{"word_kz":"ажар","translation_ru":"вид"},{"word_kz":"ай","translation_ru":"луна"},{"word_kz":"алақан","translation_ru":"ладонь"},{"word_kz":"ауа","translation_ru":"воздух"},{"word_kz":"балшық","translation_ru":"грязь"},{"word_kz":"бет","translation_ru":"лицо"},{"word_kz":"бұршақ","translation_ru":"горох"},{"word_kz":"ғарыш","translation_ru":"космос"},{"word_kz":"ғибадат","translation_ru":"поклонение"},{"word_kz":"дәл","translation_ru":"точно"},{"word_kz":"дәру","translation_ru":"лекарство"},{"word_kz":"есік","translation_ru":"дверь"},{"word_kz":"жан","translation_ru":"душа"},{"word_kz":"жар","translation_ru":"берег"},{"word_kz":"жау","translation_ru":"враг"},{"word_kz":"жем","translation_ru":"корм"},{"word_kz":"жол","translation_ru":"дорога"},{"word_kz":"жұлдыз","translation_ru":"звезда"},{"word_kz":"жүз","translation_ru":"сто"},{"word_kz":"заң","translation_ru":"закон"},{"word_kz":"ибадат","translation_ru":"молитва"},{"word_kz":"иіс","translation_ru":"запах"},{"word_kz":"көк","translation_ru":"небо"},{"word_kz":"күл","translation_ru":"пепел"},{"word_kz":"қабырға","translation_ru":"ребро"},{"word_kz":"қан","translation_ru":"кровь"},{"word_kz":"қар","translation_ru":"снег"},{"word_kz":"қауын","translation_ru":"дыня"},{"word_kz":"қол","translation_ru":"рука"},{"word_kz":"құм","translation_ru":"песок"},{"word_kz":"қызыл","translation_ru":"красный"},{"word_kz":"май","translation_ru":"масло"},{"word_kz":"мәрте","translation_ru":"раз"},{"word_kz":"мұз","translation_ru":"лёд"},{"word_kz":"өзен","translation_ru":"река"},{"word_kz":"сағат","translation_ru":"часы"},{"word_kz":"су","translation_ru":"вода"},{"word_kz":"тау","translation_ru":"гора"},{"word_kz":"темір","translation_ru":"железо"},{"word_kz":"түс","translation_ru":"цвет"},{"word_kz":"түн","translation_ru":"ночь"},{"word_kz":"ұл","translation_ru":"сын"},{"word_kz":"шам","translation_ru":"свеча"},{"word_kz":"шығыс","translation_ru":"восток"},{"word_kz":"адамзат","translation_ru":"человечество"},{"word_kz":"адалдық","translation_ru":"честность"},{"word_kz":"айналма","translation_ru":"круг"},{"word_kz":"ала","translation_ru":"пёстрый"},{"word_kz":"алғаш","translation_ru":"впервые"},{"word_kz":"атау","translation_ru":"название"},{"word_kz":"ашық","translation_ru":"открытый"},{"word_kz":"байлық","translation_ru":"богатство"},{"word_kz":"бейсенбі","translation_ru":"четверг"},{"word_kz":"бейтарап","translation_ru":"нейтральный"},{"word_kz":"болашақ","translation_ru":"будущее"},{"word_kz":"бүркіт","translation_ru":"орёл"},{"word_kz":"гүл","translation_ru":"цветок"},{"word_kz":"дәм","translation_ru":"вкус"},{"word_kz":"жанды","translation_ru":"живой"},{"word_kz":"жай","translation_ru":"лето"},{"word_kz":"жаңа","translation_ru":"новый"},{"word_kz":"жеңіс","translation_ru":"победа"},{"word_kz":"жер","translation_ru":"земля"},{"word_kz":"жыл","translation_ru":"год"},{"word_kz":"жылу","translation_ru":"тепло"},{"word_kz":"зауыт","translation_ru":"завод"},{"word_kz":"күн","translation_ru":"день"},{"word_kz":"күш","translation_ru":"сила"},{"word_kz":"қарға","translation_ru":"ворона"},{"word_kz":"қашан","translation_ru":"когда"},{"word_kz":"қонақ","translation_ru":"гость"},{"word_kz":"қорқыныш","translation_ru":"страх"},{"word_kz":"қыс","translation_ru":"зима"},{"word_kz":"мәңгі","translation_ru":"вечный"},{"word_kz":"өмір","translation_ru":"жизнь"},{"word_kz":"сән","translation_ru":"красота"},{"word_kz":"сөз","translation_ru":"слово"},{"word_kz":"тауар","translation_ru":"товар"},{"word_kz":"түйе","translation_ru":"верблюд"},{"word_kz":"ұшқын","translation_ru":"искра"},{"word_kz":"шақ","translation_ru":"момент"},{"word_kz":"шырақ","translation_ru":"светильник"},
    {"word_kz":"адамгершілік","translation_ru":"гуманность"},{"word_kz":"айналмалы","translation_ru":"круговой"},{"word_kz":"ақылды","translation_ru":"умный"},{"word_kz":"бейнелеу","translation_ru":"изображать"},{"word_kz":"беру","translation_ru":"давать"},{"word_kz":"білім","translation_ru":"знание"},{"word_kz":"бөлме","translation_ru":"комната"},{"word_kz":"дәстүр","translation_ru":"традиция"},{"word_kz":"жазу","translation_ru":"писать"},{"word_kz":"жатқызу","translation_ru":"записывать"},{"word_kz":"жылы","translation_ru":"тёплый"},{"word_kz":"зат","translation_ru":"вещь"},{"word_kz":"зерек","translation_ru":"осторожный"},{"word_kz":"кеңес","translation_ru":"совет"},{"word_kz":"керек","translation_ru":"нужно"},{"word_kz":"кітап","translation_ru":"книга"},{"word_kz":"қазақша","translation_ru":"по-казахски"},{"word_kz":"қайда","translation_ru":"где"},{"word_kz":"қалай","translation_ru":"как"},{"word_kz":"қалыпты","translation_ru":"нормальный"},{"word_kz":"қанша","translation_ru":"сколько"},{"word_kz":"қиын","translation_ru":"трудный"},{"word_kz":"қонақ үй","translation_ru":"гостиница"},{"word_kz":"құрылыс","translation_ru":"строительство"},{"word_kz":"маңызды","translation_ru":"важный"},{"word_kz":"мектеп","translation_ru":"школа"},{"word_kz":"мемлекет","translation_ru":"государство"},{"word_kz":"міндет","translation_ru":"обязанность"},{"word_kz":"мұғалім","translation_ru":"учитель"},{"word_kz":"ой","translation_ru":"мысль"},{"word_kz":"өз","translation_ru":"сам"},{"word_kz":"өнер","translation_ru":"искусство"},{"word_kz":"сабақ","translation_ru":"урок"},{"word_kz":"сана","translation_ru":"сознание"},{"word_kz":"сауда","translation_ru":"торговля"},{"word_kz":"сұрақ","translation_ru":"вопрос"},{"word_kz":"сыр","translation_ru":"секрет"},{"word_kz":"тарих","translation_ru":"история"},{"word_kz":"тіл","translation_ru":"язык"},{"word_kz":"ұлт","translation_ru":"нация"},{"word_kz":"шығарма","translation_ru":"произведение"},{"word_kz":"экран","translation_ru":"экран"},{"word_kz":"ашу","translation_ru":"открытие"},{"word_kz":"байқау","translation_ru":"наблюдать"},{"word_kz":"білу","translation_ru":"знать"},{"word_kz":"болу","translation_ru":"быть"},{"word_kz":"жасау","translation_ru":"делать"},{"word_kz":"жайлау","translation_ru":"летнее пастбище"},{"word_kz":"жату","translation_ru":"лежать"},{"word_kz":"жету","translation_ru":"достигать"},{"word_kz":"жүру","translation_ru":"идти"},{"word_kz":"келу","translation_ru":"приходить"},{"word_kz":"кету","translation_ru":"уходить"},{"word_kz":"қою","translation_ru":"ставить"},{"word_kz":"оқу","translation_ru":"читать"},{"word_kz":"отыру","translation_ru":"сидеть"},{"word_kz":"сөйлеу","translation_ru":"говорить"},{"word_kz":"тігу","translation_ru":"шить"},{"word_kz":"тұру","translation_ru":"стоять"},{"word_kz":"ұстау","translation_ru":"держать"},{"word_kz":"шығу","translation_ru":"выходить"},{"word_kz":"аң","translation_ru":"зверь"},{"word_kz":"арман","translation_ru":"мечта"},{"word_kz":"бақ","translation_ru":"сад"},{"word_kz":"дәптер","translation_ru":"тетрадь"},{"word_kz":"жылқы","translation_ru":"лошадь"},{"word_kz":"қарым-қатынас","translation_ru":"отношения"},{"word_kz":"қонақжайлы","translation_ru":"гостеприимный"},{"word_kz":"мәдениет","translation_ru":"культура"},{"word_kz":"өлең","translation_ru":"стихотворение"},{"word_kz":"сәлем","translation_ru":"привет"},{"word_kz":"ұшқыш","translation_ru":"лётчик"},
]

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "vocabulary_extended.json"


def main():
    with open(PATH, encoding="utf-8") as f:
        data = json.load(f)
    seen = {x["word_kz"] for x in data}
    added = 0
    for e in EXTRA:
        if e["word_kz"] not in seen:
            data.append(e)
            seen.add(e["word_kz"])
            added += 1
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"Добавлено {added} записей, всего: {len(data)}")


if __name__ == "__main__":
    main()
