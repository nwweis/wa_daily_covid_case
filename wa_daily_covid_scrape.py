import bs4 as bs
import sqlite3
import urllib.request
import re
import time
import datetime
import logging

# Config
logging.basicConfig(level=logging.DEBUG)
logging.disable(logging.CRITICAL)

## WA Health media release webpage
wahealth = 'https://ww2.health.wa.gov.au/News/Media-releases-listing-page'

## Search for todays date 
current_date = datetime.datetime.now()
re_covid_update = r'((COVID[-\s]?19)\s(update)\s%s\s%s\s%s)'% (current_date.day, current_date.strftime('%B'), current_date.year) # Change date as required (currently limited to 2022 above due to sentence structure)
logging.debug(re_covid_update)

## Regex search for date of news post
re_date = r'(\d+)\s(\w+)\s(\d+)'

## Regex search for local case string (Add regex as required)
re_local_case = r'(\d+|\w+)\s(were|are|new)?\s?(local\s)(COVID-19\s)?(cases*)'
re_local = re.compile('(%s)' 
           % (re_local_case))

## Regex search for interstate or overseas case string (Add regex as required)
re_travel_related   = r'(\d+|\w+)\s(are|interstate)?\s?(travel|travel-related)\s?(cases*|related*)?'
re_travel_related_2 = r'(\d+|\w+)\s(returning)\s(\w+\s)*(interstate)'
re_travel_related_3 = r'(\d+|\w+)\s(new\s)?(cases*\s)?(from|related)\s(to\s)?(are|interstate)?\s?(travel|travel-related)?\s?(cases*|related*)?'
re_travel = re.compile('(%s|%s|%s)' 
            % (re_travel_related, re_travel_related_2, re_travel_related_3))

## Dicttionary for num string to integer
nDict={"no":0, "nil":0, "zero":0, "one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9}

# Database connection (Replace as required)
def dbconn(date, local, travel):
    con = sqlite3.connect('covid_daily.db')
    cur = con.cursor()
    
    ## Create table to store daily cases if table does not exist
    cur.execute('''CREATE TABLE IF NOT EXISTS covid_daily
                   (date TEXT PRIMARY KEY, local_cases INT, travel_cases INT)''')
    
    ## Insert a row of data from scrape
    args = (date, local, travel)
    query = ('''INSERT OR IGNORE INTO covid_daily 
                VALUES (?, ?, ?)''')
    
    cur.execute(query, args)
    
    con.commit()
    con.close()

# Request wa health page
def request_page(wahealth):
    try:
        source = urllib.request.urlopen(wahealth)
        soup = bs.BeautifulSoup(source, 'lxml')
        media_release = soup.find("div", {"class": "threeCol-accordian"})
        day_media_release = media_release.findAll('li')
        return day_media_release

    except Exception as e:
        print(f'Error in requesting page: {e}')

# Scrape the daily media post
def search_post(day_media_release):
    for line in day_media_release:
        line_string = line.get_text()
        covid_update = re.search(re_covid_update, line_string)
        
        if covid_update:
            for a in line.find_all('a', href=True):
                time.sleep(1)
        
                try:
                    source = urllib.request.urlopen('https://ww2.health.wa.gov.au' + a['href'])
                except Exception as e:
                    print(e)
                    break
                
                case_soup = bs.BeautifulSoup(source, 'lxml')
                case_soup_day = case_soup.find_all("div", {"id": "contentArea"})
                
                for line in case_soup_day:
                    line_string = line.get_text()
                    
                    date = re.search(re_date, line_string).group()
                    print(f'########\n{date}')
                    
                    try:
                        local_case_search = (re.search(re_local, line_string)).group().split(' ')
                        if local_case_search[0].isdigit():
                            local_to_db = int(local_case_search[0])
                        else:
                            local_to_db = nDict[local_case_search[0].lower()]
                    except:
                        local_case_search = False
                    logging.debug(local_case_search)
                    
                    try: 
                        travel_case_search = (re.search(re_travel, line_string)).group().split(' ')
                        if travel_case_search[0].isdigit():
                            travel_to_db = int(travel_case_search[0])
                        else:
                            travel_to_db = nDict[travel_case_search[0].lower()]
                    except:
                        travel_case_search = False
                    logging.debug(travel_case_search)
                    
                    print(f"Local Case: {local_to_db}\nTravel Case: {travel_to_db}\n########")
                    
                    if local_case_search != False or travel_case_search != False:
                        dbconn(date, local_to_db, travel_to_db)
                        print('DB updated')

def main():
    day_media_release = request_page(wahealth)
    search_post(day_media_release)
            
if __name__ == '__main__':
    main()