import sqlite3
from lxml import html
from selenium import webdriver
import datetime
import time


conn = sqlite3.connect('app.db')
c = conn.cursor()


def scrape(type, url):
    print()
    print("Scraping", url, flush=True)
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    # This option is necessary to avoid an error when running as a service
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(url)
    tree = html.fromstring(driver.page_source)
    date_old = False
    if type == 0:
        date_xpath = '//*[@id="overviewQuickstatsDiv"]/table/tbody/tr[2]/td[1]/span/text()'
        vl_xpath = '//*[@id="overviewQuickstatsDiv"]/table/tbody/tr[2]/td[3]/text()'
    if type == 1:
        date_xpath = '//*[@id="curr_table"]/tbody/tr[1]/td[1]/text()'
        vl_xpath = '//*[@id="curr_table"]/tbody/tr[1]/td[2]/text()'
        date_xpath_old = '//*[@id="curr_table"]/tbody/tr[2]/td[1]/text()'
        vl_xpath_old = '//*[@id="curr_table"]/tbody/tr[2]/td[2]/text()'
        date_old = tree.xpath(date_xpath_old)
        VL_old = tree.xpath(vl_xpath_old)
    if type == 2:
        date_xpath = '//*[@id="tabla_datos_generales"]/tbody/tr[4]/th/text()'
        vl_xpath = '//*[@id="tabla_datos_generales"]/tbody/tr[4]/td/text()'
    date = tree.xpath(date_xpath)
    VL = tree.xpath(vl_xpath)
    driver.quit()
    if len(date) == 0 or len(VL) == 0:
        print('No data', flush=True)
        return -1, -1
    if date_old:
        return date[0], VL[0], date_old[0], VL_old[0]
    else:
        return date[0], VL[0]


def look_for_data():
    t = "1"
    candidates = []
    for row in c.execute("SELECT * FROM activo WHERE descargar =?", t):
        # 0: Id, 3:tipo, 4:url
        element = [row[0], row[3], row[4]]
        candidates.append(element)
    n = 0
    print('****************************************************************', flush=True)
    while len(candidates) > 0 and n < 4:
        print('Candidates pending:', len(candidates), flush=True)
        remove = []
        for index, e in enumerate(candidates):
            if e[1] == 0:
                date, VL = scrape(0, e[2])
                if date == -1:
                    continue
                day = int(date[0:2])
                month = int(date[3:5])
                year = int(date[6:])
                t = datetime.date(year, month, day)
                VL = VL[4:]
                VL = VL.replace(",", ".")
            elif e[1] == 1 or e[1] == 3:
                try:
                    date, VL, date_old, VL_old = scrape(1, e[2])
                except ValueError as e:
                    print("Algo a fallado:", e, flush=True)
                    continue
                if date == -1:
                    continue
                day = int(date[0:2])
                month = int(date[3:5])
                year = int(date[6:])
                t = datetime.date(year, month, day)
                VL = VL.replace(",", ".")
                day_old = int(date_old[0:2])
                month_old = int(date_old[3:5])
                year_old = int(date_old[6:])
                t_old = datetime.date(year_old, month_old, day_old)
                VL_old = VL_old.replace(",", ".")
                print(t_old, VL_old, flush=True)
                c.execute("INSERT OR REPLACE INTO cotizacion (fecha, VL, activo_id) VALUES (?, ?, ?)", (t_old, VL_old, e[0],))
            elif e[1] == 2:
                date, VL = scrape(2, e[2])
                if date == -1:
                    continue
                date = date[42:52]
                day = int(date[0:2])
                month = int(date[3:5])
                year = int(date[6:])
                t = datetime.date(year, month, day)
                VL = VL[:11]
                VL = VL.replace(",", ".")
            print(t, VL, flush=True)
            c.execute("INSERT OR REPLACE INTO cotizacion (fecha, VL, activo_id) VALUES (?, ?, ?)", (t, VL, e[0],))
            remove.append(index)
        conn.commit()
        remove.sort(reverse=True)
        for e in remove:
            del candidates[e]
        if len(candidates) > 0:
            print('***********************************************', flush=True)
            print('The following candidates failed:', flush=True)
            for e in candidates:
                print(e[2], flush=True)
            n = n + 1
            if n > 3:
                print('Too many retries. Aborting', flush=True)
            else:
                time.sleep(60)
                print('Retry number', n, flush=True)
        else:
            print('Scrape finished', flush=True)


if __name__ == "__main__":
    while True:
        look_for_data()
        time.sleep(6590)
