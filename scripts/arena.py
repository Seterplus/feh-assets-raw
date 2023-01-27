import json
import re
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from threading import Thread

ID_DIR = 'files/assets/USEN/Message/Data'
SEASON_FILE = 'files/assets/Common/Delivery/Season.json'
BONUS_BOOK_DIR = 'files/assets/Common/Arena'
ARENA_BONUS_DIR = 'files/assets/Common/Delivery/ArenaPerson'

WEEK_SECONDS = 7 * 86400

WIKI_PAGE = 'https://feheroes.fandom.com/api.php?action=parse&prop=text&format=json&origin=*&page='
ICON_RE = re.compile(r'[^"]*_Unit_Idle_No_Wep.png/revision/latest\?[^"]*')
ICON_BACKUP_RE = re.compile(r'[^"]*_Unit_Idle.png/revision/latest\?[^"]*')


def fetch_wiki(page_name, page_contents):
    try:
        with urllib.request.urlopen(WIKI_PAGE + urllib.parse.quote(page_name)) as f:
            page_contents[page_name] = json.loads(f.read())['parse']['text']['*']
    except Exception as e:
        page_contents[page_name] = ''


def main():
    unit_names, unit_honors = {}, {}
    for data_path in Path(ID_DIR).glob('*.json'):
        with data_path.open() as f:
            for kv in json.load(f):
                key, value = kv['key'], kv['value']
                key_type = key.count('_')
                if key_type == 1 and key.startswith('MPID_'):
                    assert key[5:] not in unit_names
                    unit_names[key[5:]] = value
                elif key_type == 2 and key.startswith('MPID_HONOR_'):
                    assert key[11:] not in unit_honors
                    unit_honors[key[11:]] = value

    seasons = {}
    with open(SEASON_FILE) as f:
        for season in json.load(f):
            week = int(datetime.fromisoformat(season['start'][:-1]).timestamp()) \
                // WEEK_SECONDS
            assert week not in seasons
            seasons[week] = season

    bonus_books = {}
    for data_path in Path(BONUS_BOOK_DIR).glob('*.json'):
        with data_path.open() as f:
            for data in json.load(f):
                assert data['start'] not in bonus_books
                bonus_books[data['start']] = data['bonus_book']

    arena_data = {}
    units = set()
    with max(Path(ARENA_BONUS_DIR).glob('*.json')).open() as f:
        for data in json.load(f):
            hero_id, start = data['hero_id'], data['active']['start']
            if start not in arena_data:
                season = seasons[
                    int(datetime.fromisoformat(start[:-1]).timestamp()) // WEEK_SECONDS]
                arena_data[start] = {
                    'units': [],
                    'start': start,
                    'finish': data['active']['finish'],
                    'seasons': season['seasons'],
                    'aether_seasons': season['aether_seasons'],
                }

            assert hero_id.startswith('PID_')
            hero_id = hero_id[4:]
            hero_name = f"{unit_names[hero_id]}: {unit_honors[hero_id]}"
            arena_data[start]['units'].append({
                'hero_id': hero_id,
                'hero_name': hero_name,
            })
            units.add(hero_name)

    unit_pages = {}
    threads = [Thread(target=fetch_wiki, args=(unit, unit_pages)) for unit in units] \
        + [Thread(target=fetch_wiki, args=(unit + '/Misc', unit_pages))
           for unit in units]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for start_date in arena_data:
        units = arena_data[start_date]['units']
        for unit in units:
            hero_id, hero_name = unit['hero_id'], unit['hero_name']
            if '>PID_' + hero_id + '<' not in unit_pages[hero_name]:
                unit['icon'] = ''
                continue
            content = unit_pages[hero_name + '/Misc']
            icon = ICON_RE.search(content) or ICON_BACKUP_RE.search(content)
            unit['icon'] = icon.group(0) if icon else ''

        bonus_book = bonus_books[start_date]
        if bonus_book != 0:
            units.append({
                'hero_id': f"Book {bonus_book}",
                'hero_name': "",
                'icon': '',
            })
        assert len(units) == 10

    with open('out/arena.json', 'w') as f:
        json.dump(list(arena_data.values()), f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
