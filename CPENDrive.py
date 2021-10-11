import glob
import os
import re
import sys
import threading
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
from download import download
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

baseurl = 'https://cpentalk.com/drive/index.php'
basedir = 'd:\\▼\\CPENDrive\\'
automode = 0    # 0, 1
headless = 1    # 0, 1, 2

def requesthttp(url):
    try:
        useragent = UserAgent()
        while True:
            headers = {'User-Agent': useragent.random}
            res = requests.get(url, headers=headers)
            print(f'status code: {res.status_code}')
            if res.status_code == 200:
                return res
    except requests.exceptions.Timeout as e:
        print("Timeout Error: ", e)
    except requests.exceptions.ConnectionError as e:
        print("Connection Error: ", e)
    except requests.exceptions.HTTPError as e:
        print("Http Error: ", e)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

def getlatestctime(downloadpath):
    files = glob.glob(f'{downloadpath}\\*[!crdownload]')
    if len(files) == 0:
        return '', 0
    else:
        latestfile = max(files, key=os.path.getctime)        
        ctime = os.path.getctime(latestfile)
        return latestfile, ctime

def downloadcompleted(downloadpath, orgfile, prevctime, timeout=60):
    newctime = 0
    latestfile = ''
    while prevctime >= newctime:
        time.sleep(1)
        timeout -= 1
        if timeout == 0:
            return
        latestfile, newctime = getlatestctime(downloadpath)    
    if latestfile != orgfile:        
        os.rename(latestfile, orgfile)
        print('-' * 160 + '\n' + latestfile + '\n' + orgfile + '\n' + '-' * 160)

def downloadfile(suburl):
    global driver
    res = requesthttp(baseurl + suburl)
    soup = BeautifulSoup(res.text, 'html.parser')
    downloadpath = basedir + urllib.parse.unquote_plus(suburl[3:]).replace('/', '\\')
    for i, item in enumerate(soup.select('div.filename')):
        if str(item).find('fa fa-folder') >= 0:
            suburl = item.select_one('a')['href']
            downloadfile(suburl)
        else:                        
            if not os.path.exists(downloadpath):
                os.makedirs(downloadpath)     
            orgfilename = item.select_one('a')['title']
            filename = re.sub('[\/:*?\"<>|]', '_', orgfilename)  
            orgfile = downloadpath + '\\' + filename
            if not os.path.exists(orgfile):
                if headless == 2:
                    requesthttp(baseurl + suburl)   # alive check
                result = getlatestctime(downloadpath)
                file = item.select_one('a')['href']
                fileurl = baseurl + '?download=true' + file.replace('?p', '&p').replace('&view', '&dl')
                if headless >= 1:
                    driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
                    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': downloadpath}}
                    driver.execute("send_command", params)
                    driver.get(fileurl)
                    if headless == 2:
                        requesthttp(baseurl + suburl)   # alive check
                        t = threading.Thread(target=downloadcompleted, args=(downloadpath, orgfile, result[1]))
                        t.start()
                        t.join()                
                    print(f'{i+1:04d}. {orgfilename} downloaded.')
                else:
                    download(fileurl, orgfile, progressbar=True, replace=True, timeout=60)

def getfile(suburl):
    res = requesthttp(baseurl + suburl)
    soup = BeautifulSoup(res.text, 'html.parser')
    for item in soup.select('div.filename'):
        suburl = item.select_one('a')['href']
        if 'CPEN Drive' in soup.find('title').get_text():
            continue
        downloadfile(suburl)

if __name__ == '__main__':    
    crdownloads = glob.iglob(basedir + '**\\*.crdownload', recursive=True)
    [os.remove(f) for f in crdownloads]
    if headless >= 1:
        useragent = UserAgent()
        options = Options()
        options.add_argument('--headless')        
        options.add_argument('--log-level=3')
        options.add_argument('disable-gpu')
        options.add_argument(f'user-agent={useragent.random}')
        driver = webdriver.Chrome(executable_path='d:\\chromedriver.exe', options=options)
    res = requesthttp(baseurl + '?p')
    soup = BeautifulSoup(res.text, 'html.parser')
    items = soup.select('div.filename')
    category = [item.get_text().strip() for item in items]
    suburl = [item.find('a')['href'] for item in items]
    catlen = len(category)
    category.sort()
    suburl.sort()    
    if automode:
        for i in range(catlen):
            getfile(suburl[i])
    else:
        while True:
            for i, menu in enumerate(category, start=1):
                print(f'{i}. {menu}')
            sel = input(f'Enter your choice (1~{catlen}): ')
            if sel.isalpha():
                if sel.lower() == 'x':
                    sys.exit()
            else:                
                num = int(sel)
                if num >= 1 and num <= catlen:
                    getfile(suburl[num - 1])
    if headless >= 1:
        driver.quit()
