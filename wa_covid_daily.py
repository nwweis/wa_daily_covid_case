import bs4 as bs
import datetime
import sqlite3
import urllib.request
import re

# Config
wahealth = 'https://ww2.health.wa.gov.au/News'
today = datetime.datetime.now()

re_date = r'\d+\s(\w+)\s\d+'
re_local_case = r'(\d+\s)(new\s)?(local\s)(COVID-19\s)?(cases)'
re_travel_related = r'\d+\stravel-related\scases'

def dbconn(date, local, travel):
    con = sqlite3.connect('covid_daily.db')
    cur = con.cursor()

    # Create table
    cur.execute('''CREATE TABLE IF NOT EXISTS covid_daily
                   (date TEXT PRIMARY KEY, local_cases INT, travel_cases INT)''')

    # Insert a row of data
    args = (date, local, travel)
    query = ('''INSERT OR IGNORE INTO covid_daily 
                VALUES (?, ?, ?)''')

    cur.execute(query, args)

    con.commit()
    con.close()
    print('Database updated')

def request_page(wahealth):
    try:
        source = urllib.request.urlopen(wahealth)
    except Exception as e:
        print(e)

    return source

def parse_release(source):
    soup = bs.BeautifulSoup(source, 'lxml')

    media_release = soup.find("div", {"id": "MediaNewsListing"})
    day_media_release = media_release.findAll('li')

    for line in day_media_release:
        line_string = line.get_text()

        try:
            local_case_search = (
                re.search(re_local_case, line_string)).group().split(' ')
            travel_case_search = (
                re.search(re_travel_related, line_string)).group().split(' ')
            date = re.search(re_date, line_string).group()

            dbconn(date, local_case_search[0], travel_case_search[0])

        except Exception as e:
            print(f'Error in text scrape: {e}')

def main():
    page = request_page(wahealth)
    parse_release(page)
    print('Complete')

if __name__ == '__main__':
    main()
