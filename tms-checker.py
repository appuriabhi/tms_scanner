import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm
from csv import writer,reader,DictWriter
import pyfiglet

f = pyfiglet.Figlet(font='slant')
print(f.renderText("**********"))
print(f.renderText('TMS Scanner'))
#print(pyfiglet.figlet_format("**********"))
print(f.renderText("**********"))
print("Program Started..\n")

def is_valid_url(url):
    import re
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)

# Get Values form User
start_page = str(input('\nPlease provide start_page/homepage of your site in format https//test.com or https://www.test.com >> '))
start_page = start_page.strip(' ')

if (is_valid_url(start_page) == None):
    print('\nIncorrect Format for Start Page > Please Restart Program\n')
    quit()
limit = (input('Default Scan Limit is set to 100 pages: \nSet custom scan limit (hit enter for no change)> '))
print('\nScanner Started..\n\n')

if (limit != '' and int(limit) > 0 and int(limit) < 500):
    limit = limit
else:
    limit = 100

#base domain can come form input or api call
base_domain = start_page.replace('http://','').replace('https://','').replace('www.','')
exclude_list = ['mailto:','javascript:','#']


def get_protocol(url):        
    if ('https:' in url):
        p = 'https://'
    elif ('http:' in url):
        p = 'http://'
    else:
        p = 'http://'
    return p             

gtm_snippet = 'www.googletagmanager.com/gtm.js?id='
adobe_snippet = 'assets.adobedtm.com'
master_hrefs = []

if (start_page[len(start_page)-1] == "/"):
    pass
else:
    start_page = str(start_page) + '/'

_obj = {}
_obj['page_url'] = start_page
_obj['crawlStatus'] = 'pending'
    
master_hrefs.append(_obj)

#pandas
column_names = ["Page URL", "Status Code", "Page Title","GTM Snippet","Launch/DTM Snippet"]
df = pd.DataFrame(columns = column_names)


def formatted_filename():
    t1 = time.asctime(time.localtime(time.time()))
    x = t1.split(" ")
    if x[2] != "":
        time_variable = x[3].split(":")
        time_variable = time_variable[0]+"-"+time_variable[1]+"-"+time_variable[2]
        new_format = x[2]+"_"+x[1]+"_"+x[4]+"_"+x[0]+"_("+time_variable+")"
    else:
        time_variable = x[4].split(":")
        time_variable = time_variable[0]+"-"+time_variable[1]+"-"+time_variable[2]
        new_format = x[3]+"_"+x[1]+"_"+x[5]+"_"+x[0]+"_("+time_variable+")"               
    return "tms_scanner_"+str(new_format)+".csv"

def _gtmChecker(_arr):
    if (len(_arr) > 0):
        for i, item in enumerate(_arr):
            str_item = str(item)
            if (gtm_snippet in str_item):         
                split_str_item = str_item.split(';')
                for val in split_str_item:
                    if ("GTM-" in val):
                        container_code = (val.split(',')[4]).replace("')",'').replace('\'','')
                        return (gtm_snippet+container_code)          
            elif (i == (len(_arr)-1)):
                return "GTM Snippet: Not Found"
    else:
        return 'No <script> tags on page'

def _dtm_launchChecker(_arr):
    if (len(_arr) > 0):
        for i, item in enumerate(_arr):
            str_item = str(item)
            if (adobe_snippet in str_item):         
                return item.attrs['src']
            elif (i == (len(_arr)-1)):
                return "Launch/DTM Snippet: Not Found"
    else:
        return 'No <script> tags on page'

def _indexer(_arr,current_domain):
    protocol = get_protocol(current_domain)
    current_domain = current_domain.replace('http://','').replace('https://','').replace('www.','')
    current_domain = current_domain.split('/')[0]
    if (len(_arr) > 0):
        for val in _arr:
            try:           
                _href = (val.attrs['href'])
                if ((base_domain in _href) and (_href not in str(master_hrefs)) and (_href not in exclude_list)):
                    _obj = {}
                    _obj['page_url'] = _href
                    _obj['crawlStatus'] = 'pending'
                    master_hrefs.append(_obj) 
                elif (_href[0] == '/' and (str(protocol) + (current_domain + _href).replace('//','/') not in str(master_hrefs)) and (_href not in exclude_list)):
                    _obj = {}
                    _obj['page_url'] = str(protocol) + (current_domain + _href).replace('//','/')
                    _obj['crawlStatus'] = 'pending'
                    master_hrefs.append(_obj)
            except:
                pass
                          
def _crawler(url):
    try:
        r = requests.get(url)
        statusCode = r.status_code
        
        if (statusCode == (200 or 400)):
            content = r.content
            soup = BeautifulSoup(content, 'lxml')
            allScriptsList = soup.find_all('script')
            allAnchorTags = soup.find_all('a')
            pageTitle = soup.find('title')
            pageTitle = pageTitle.string
            #indexer function will be called here on allAnchorTags
            _indexer(allAnchorTags,str(url))
            #format file
            outputArr = []
            outputArr.append(url)
            outputArr.append(statusCode)
            outputArr.append(pageTitle)
            outputArr.append(_gtmChecker(allScriptsList))
            outputArr.append(_dtm_launchChecker(allScriptsList))
            #print(outputArr)
            df_length = len(df)
            df.loc[df_length] = outputArr
    except: 
        print('Unexpected error occured\nPlease retart program')
        quit()    

def _initiator(limit):
    for _index, _val in enumerate(tqdm(master_hrefs)):
        if (_index < int(limit)):
            if (_val['crawlStatus'] == 'pending'):
                time.sleep(2)
                _crawler(_val['page_url'])
                _val['crawlStatus'] = 'done'
        else:
            return

_initiator(limit)
filename = formatted_filename()
df.to_csv(filename, index=False, encoding='utf-8')
print('\n\n')
print(f"Program Complete\nPlease refer file: {filename} for reference.")              
print('\n')