# imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
from progressbar import ProgressBar
pbar = ProgressBar()
from bs4 import BeautifulSoup
from datetime import datetime as dt
import time

def barchart_scraper(browser_path, url, engine):

    # setting the chromedriver path and initializing driver
    driver = webdriver.Chrome(executable_path=browser_path)
    driver.set_page_load_timeout(100)
    driver.implicitly_wait(30)
    driver.get(url)

    expiry_box = driver.find_element(By.XPATH, '//*[@id="main-content-column"]/div/div[3]/div[1]/div/div[2]/select')
    expiry_list = [x.text for x in expiry_box.find_elements(By.TAG_NAME,"option")]
    driver.quit()
    moneyness = 'moneyness=20' #options 5,10,20,50

    # create master df to append to
    master_df = pd.DataFrame()

    for expiry in pbar(expiry_list):
        curr_url = url + '?expiration=' + expiry.replace(' (w)', '-w').replace(' (m)','-m') + '&' + moneyness
        print(curr_url)
        driver = webdriver.Chrome(executable_path=browser_path)
        driver.get(curr_url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'lxml')
        tables = soup.find_all('table')
        dfs = pd.read_html(str(tables))

        last_px_elem = driver.find_element(By.XPATH, '/html/body/main/div/div[2]/div[2]/div/div[2]/div/div/div/div[1]/div[2]/div[3]/span[1]')
        last_px = float(last_px_elem.text)

        for df in dfs:
            try:
                df['asof_date'] = dt.now().strftime("%m/%d/%Y %H:%M:%S")
                df['expiry'] = pd.to_datetime(expiry.replace(' (w)','').replace(' (m)',''))
                df.drop(columns='Links', index=1, inplace=True)
                # df.columns = df.columns.str.lower()
                df = df.iloc[:-1]
                df.rename(columns={'Strike': 'strike', 'Last': 'last', 'Theor.': 'theor', 'IV': 'iv', 'Delta': 'delta',
                                   'Gamma': 'gamma', 'Theta': 'theta', 'Vega': 'vega', 'Rho': 'rho', 'Volume': 'volume',
                                   'Open Int': 'open_int', 'Vol/OI': 'vol_oi', 'Type': 'type',
                                   'Last Trade': 'last_trade'}, inplace=True)
                num_cols = ['strike','last','theor','iv','delta','gamma','theta','vega','rho','volume','open_int','vol_oi']
                df['iv'] = df['iv'].apply(lambda x: x.strip('%'))
                df.loc[:,num_cols] = df.loc[:,num_cols].apply(pd.to_numeric, errors='coerce')
                df['iv'] = df['iv']/100
                date_cols = ['last_trade', 'asof_date']
                df[date_cols] = df[date_cols].apply(pd.to_datetime, errors='coerce')

                df['last_px_underlying'] = last_px

                df.to_sql('chains', con=engine, if_exists='append', index=False)
            except ValueError:
                print('Error')

        driver.quit()

    return master_df
