## Scraping option chains data from barchart.com using Selenium

### Introduction 

Option chains are lists of available contracts on a given security, typically a matrix of different expiries and strikes. However, free and clean option data is usually hard to come by. With this script (aimed at being ran automatically at specified intervals) we scrap the website barchart.com for SPY option chains. \\
We use two packages for this project:
- Selenium. A package that allows to automate browser tasks.
- BeautifulSoup. Another package that parses html, xml, css in order to extract all available information from web pages.

Let's start with a look at the barchart page for SPY options. There are two available views of option chains:

- a stacked view (https://www.barchart.com/etfs-funds/quotes/SPY/volatility-greeks)

![alt text](https://github.com/pmnry/BarchartSelenium/blob/master/stacked_view.png?raw=true)




- a side-by-side view (https://www.barchart.com/etfs-funds/quotes/SPY/volatility-greeks?view=sbs)

![alt text](https://github.com/pmnry/BarchartSelenium/blob/master/sidebyside.png?raw=true)


It turns out that the stacked view is much simpler to parse. We will see this in a minute.

### Setting up Selenium to scrap the page

The Selenium documentation explains in details how to install and get started: https://selenium-python.readthedocs.io/

Just know that in you need to download a web browser executable and provide its path as "executable_path" parameter when creating a WebDriver object.


```python
### We start by opening the default SPY options page: closest expiry

from selenium import webdriver
from selenium.webdriver.common.by import By

url = "https://www.barchart.com/etfs-funds/quotes/SPY/volatility-greeks"

driver = webdriver.Chrome(executable_path=BROWSER_PATH)
driver.set_page_load_timeout(100)
driver.implicitly_wait(30)
driver.get(url)
```

The code snippet above will provide us with the view above. We see that the website only displays the shortest expiry, however it allows to select other expiries (as well as the number of strikes) in a dropdown menu at the top of the table.\\
We would like to either:
- be able to click on that dropdown and go through each expiry
- get all expiries and find a way to crawl through their urls

Although Selenium allows to choose the first option (actions such as clicking are possible) it turns out the second option is much easier.

First let's have a look at which expiries are available:

![alt text](https://github.com/pmnry/BarchartSelenium/blob/master/dropdown.png?raw=true)

If we click the 03-12 option we get to the following URL: https://www.barchart.com/etfs-funds/quotes/SPY/volatility-greeks?expiration=2021-12-03-w

We immediately notice that provided we can extract the list of available expiries, we can then reach the URL of each of page displaying the option chains for those.

One final element is the number of strikes. The website displays +/- 5 strikes around the money. By playing with the options of the number of strikes dropdown menu, we find out that the URL also contains the option chosen by the user.

https://www.barchart.com/etfs-funds/quotes/SPY/volatility-greeks?expiration=2021-12-03-w&moneyness=20

The "moneyness" argument can take values 5, 10, 20, 50. It seems that 50 shows a lot of options with very little liquidity so we pick 20.

### Scraping dropdown options

By right-clicking on the dropdown menu in Chrome we can inspect the HTML code of the page. The Chrome code editor opens up as a right pane and hovering on the code highlights the elements of the page that are implemented at that line.

![alt text](https://github.com/pmnry/BarchartSelenium/blob/master/inspect_dropdown.png?raw=true)

We can then leverage a useful feature to locate a specific element which its XPATH. This article gives a great introduction to XPATH: http://plasmasturm.org/log/xpath101/ 

For now all we need to know is that Selenium allows to find elements by a number of ways including their XPATH. By right-clicking on the line of code that corresponds to the dropdown menu we can copy its XPATH. We get the somewhat abstruse string of characters: //*[@id="main-content-column"]/div/div[3]/div[1]/div/div[2]/select

The code snippet below shows how to select and extract the data by providing the XPATH of an element.


```python
from selenium.webdriver.common.by import By

### First we get the element by its XPATH

expiry_box = driver.find_element(By.XPATH, '//*[@id="main-content-column"]/div/div[3]/div[1]/div/div[2]/select')

### Then within the dropdown menu, each option has a tag "option" which we can get again by using the By object 
### of the element class

expiry_list = [x.text for x in expiry_box.find_elements(By.TAG_NAME,"option")]

driver.quit()
print(expiry_list)
```

    ['2021-12-01 (w)', '2021-12-03 (w)', '2021-12-06 (w)', '2021-12-08 (w)', '2021-12-10 (w)', '2021-12-13 (w)', '2021-12-15 (w)', '2021-12-17 (m)', '2021-12-20 (w)', '2021-12-22 (w)', '2021-12-23 (w)', '2021-12-27 (w)', '2021-12-29 (w)', '2021-12-31 (w)', '2022-01-03 (w)', '2022-01-05 (w)', '2022-01-07 (w)', '2022-01-21 (m)', '2022-02-18 (m)', '2022-03-18 (m)', '2022-03-31 (w)', '2022-04-14 (m)', '2022-05-20 (m)', '2022-06-17 (m)', '2022-06-30 (w)', '2022-09-16 (m)', '2022-09-30 (w)', '2022-12-16 (m)', '2023-01-20 (m)', '2023-03-17 (m)', '2023-06-16 (m)', '2023-12-15 (m)', '2024-01-19 (m)']
    

If we refer to the URL format we found above, we can loop through this list to get the web page display the option chains for each expiry.


```python
for expiry in expiry_list:
    
    ### We see that the string with the expiry contains either "(w)" or "(m)" which need to be replaced by a version
    ### without brackets
    
    curr_url = url + '?expiration=' + expiry.replace(' (w)', '-w').replace(' (m)','-m') + '&' + moneyness
    print(curr_url)
    
    ### We open a new webdriver
    
    driver = webdriver.Chrome(executable_path=browser_path)
    driver.get(curr_url)
    
    ### The tables in each page can take a few seconds to load. To be safe we pause the script here.
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'lxml')
    tables = soup.find_all('table')
    dfs = pd.read_html(str(tables))

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
            df.loc[:,num_cols] = df.loc[:,num_cols].apply(pd.to_numeric, errors='coerce')

            date_cols = ['last_trade', 'asof_date']
            df[date_cols] = df[date_cols].apply(pd.to_datetime, errors='coerce')

            df.to_sql('chains', con=engine, if_exists='append', index=False)
        except ValueError:
            print('Error')

    driver.quit()
```

### Potential improvements

Currently we scrap +/- 20 strikes around the money. These will change as the spot change. We might want to always get fixed strikes in order to allow comparison across time. However liquidity is low for strikes deep OTM and ITM which alters the information we can extract from those.

W
