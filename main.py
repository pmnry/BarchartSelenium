import os
# set path to current folder
folder_loc = os.path.dirname(os.path.realpath(__file__))
os.chdir(folder_loc)
from scraper_function import barchart_scraper
from sqlalchemy import create_engine
from config import POSTGRES, BROWSER_PATH

###############################################################
# set url
###############################################################

url = "https://www.barchart.com/etfs-funds/quotes/SPY/volatility-greeks"

###############################################################
# start of script -- no need to edit below this point
###############################################################

class Config(object):
    # SQL Alchemy global vars: don't modify
    SQLALCHEMY_DATABASE_URI =  os.environ.get('DATABASE_URL') or 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
    SQLALCHEMY_TRACK_MODIFICATIONS = False

if __name__ == '__main__':

    # create SQL alchemy connection
    config = Config()
    cnx = create_engine(config.SQLALCHEMY_DATABASE_URI)

    # run scraper
    df = barchart_scraper(BROWSER_PATH, url, cnx)
