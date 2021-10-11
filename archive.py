import os, sys, requests, glob, re
import urllib.parse
from download import download
from bs4 import BeautifulSoup

baseurl = 'https://archive.org'
basedir = 'd:\\▼\\archive\\'
id = 'folkscanomy_computer'
workfile = 'work.txt'

def requesthttp(url):
    try:
        while True:
            res = requests.get(url)
            if res.status_code == 200:
                break
            print(f'status code: {res.status_code}')
    except requests.exceptions.Timeout as e:
        print("Timeout Error: ", e)
    except requests.exceptions.ConnectionError as e:
        print("Connection Error: ", e)
    except requests.exceptions.HTTPError as e:
        print("Http Error: ", e)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    return res

def downloadfile(sel, num):
    suburl = f'/details/{id}?and%5B%5D=languageSorter%3A%22English%22&and%5B%5D=mediatype%3A%22texts%22&and \
        %5B%5D=firstTitle%3A{sel}&sort=titleSorter&page={num}'
    res = requesthttp(baseurl + suburl)
    soup = BeautifulSoup(res.text, 'html.parser')
    if len(soup.select('div.no-results')) == 0:
        for item in soup.select('div.item-ttl'):
            suburl = item.select_one('a')['href']
            res = requesthttp(baseurl + suburl + '/page/n113/mode/2up')
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.select('div.format-group'):
                suburl = item.select_one('a')['href']
                if suburl.endswith('.pdf'):
                    i = suburl.rfind('/')
                    orgfilename = urllib.parse.unquote_plus(suburl[i+1:])
                    filename = re.sub('[\/:*?\"<>|]', '_', orgfilename)
                    filepath = downloadpath + sel.upper() + '\\' + filename
                    if not os.path.exists(filepath):
                        print(f'{num}: {orgfilename}')                        
                        download(baseurl + suburl, filepath, progressbar=True, replace=True)        
        num += 1
        with open(f'{downloadpath}{workfile}', 'w') as f:
            f.write(f'{sel}:{num}')
        downloadfile(sel, num)
    else:
        sel = chr(ord(sel) + 1)
        if(sel <= 'z'):
            num = 1
            downloadfile(sel, num)
        else:
            print('##### All downloads completed. #####')
            
if __name__ == '__main__':
    parts = glob.iglob(basedir + '**\\*.part', recursive=True)
    [os.remove(f) for f in parts]
    downloadpath = f'{basedir}{id}\\'    
    if not os.path.exists(downloadpath):
        os.makedirs(downloadpath)
        with open(downloadpath + workfile, 'w') as f:
            f.write('a:1')            
    with open(downloadpath + workfile, 'r') as f:        
        work = f.read()        
        sel = work.split(':')[0]
        num = int(work.split(':')[1])
        downloadfile(sel, num)            
