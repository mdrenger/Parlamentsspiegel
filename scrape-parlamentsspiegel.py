#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# scrapeNRW - Scraping the state parliament information system.
# Copyright (C) 2015 Markus Drenger

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import requests
import json
import locale
import datetime
from bs4 import BeautifulSoup

try:
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
except locale.Error:
    print("Setting the required german locale failed. Please install!")
    raise

def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""

def getURLSofPages(soup):
    results = int(soup.find('p',{'class':'paging-register'}).text.split(' ')[-1])
    print(results)
    urls = []
    i = 1
    #while int(results / 50) >= i:
    while i*50 < results+49:
        print("next")
        urls.append("http://www.parlamentsspiegel.de/ps/suche/Suchergebnisse_Parlamentsspiegel.jsp?m={}1&w=1%3D1&order=&maxRows=50&view=kurz&db=psakt".format(5*i))
        i = i + 1
    return urls


def getDetailsLinks(soup):
    dds = soup.findAll('dd',{'class':'link'})
    links = []
    for dd in dds:
        links.append('http://www.parlamentsspiegel.de'+dd.a['href'])
    return links


def setDB():

 
 conn = sqlite3.connect("parlamentsspiegel.sqlite3")
 #print "Opened database successfully";
 conn.execute('''create table if not exists Links
       (
       Link           TEXT    ,
       scraped INTEGER
      
       );''')
 r = requests.get("http://www.parlamentsspiegel.de/ps/suche/Suchergebnisse_Parlamentsspiegel.jsp?w=&order=&fm=&db=psakt").text
 soup = BeautifulSoup(r)

 detaillinks = []

 for url in getURLSofPages(soup):
  print(url)
  conn.execute("insert links (links,scraped) values ("+url+",0")
 conn.commit()
 conn.close()

def getNext():
 conn = sqlite3.connect("parlamentsspiegel.sqlite3")
 #print "Opened database successfully";
 conn.execute('select link from links where scraped=0 Limit 100')
 r = requests.get("http://www.parlamentsspiegel.de/ps/suche/Suchergebnisse_Parlamentsspiegel.jsp?w=&order=&fm=&db=psakt").text
 soup = BeautifulSoup(r)

 detaillinks = []

 for url in getURLSofPages(soup):
  print(url)
  conn.execute("insert links (links,scraped) values ("+url+",0")
 conn.commit()
 conn.close()

def parseDetailspage(soup,url):
    print(url)
    detail = {}
    detail['url']=url
    table = soup.find('table')
    detail['title']= table.tr.a.strong.text
    detail['basisdoklink'] = 'http://www.parlamentsspiegel.de'+table.tr.a['href']
    detail['textblock'] = table.select('tr')[1].select('td')[1].text
    detail['systematik'] = list(map(str.strip, find_between(detail['textblock'], 'Systematik:', '\n').split('*')))
    detail['schlagworte'] = list(map(str.strip, find_between(detail['textblock'], 'Schlagworte:', '\n').split('*')))
    detail['suchworte'] = list(map(str.strip, find_between(detail['textblock'], 'Suchworte:', '\n').split('*')))
    detail['region'] = list(map(str.strip, find_between(detail['textblock'], 'Region:', '\n').split('*')))
    if len(table.findAll('tr'))>=3:
        if table.select('tr')[2].select('td')[0].find('a') is not None:
            detail['doclink']=table.select('tr')[2].select('td')[0].a['href']
        if table.select('tr')[2].select('td')[1].find('a') is not None:
            detail['doc_meta_link']=table.select('tr')[2].select('td')[1].a['href']

    return detail

def parseBasisDok(soup):
    basisdok={}
    table = soup.find('table')
    for tr in table.findAll('tr'):
        basisdok[tr.select('td')[0].text.strip()]=tr.select('td')[1].text.strip()
    return basisdok


testurl = 'http://www.parlamentsspiegel.de/ps/suche/Suchergebnisse_Parlamentsspiegel.jsp?w=native%28%27%28BEGRIFF_IX+phrase+like+%27%27Gemini%27%27%29%27%29&order=&fm=&db=psakt'
#r = requests.get(testurl).text
r = requests.get("http://www.parlamentsspiegel.de/ps/suche/Suchergebnisse_Parlamentsspiegel.jsp?w=&order=&fm=&db=psakt").text
soup = BeautifulSoup(r)

detaillinks = []

for url in getURLSofPages(soup):
    print(url)
    detaillinks.extend(getDetailsLinks(BeautifulSoup(requests.get(url).text)))


json.dump(detaillinks, open("parlamentsspiegel-detaillinks.json", "w", -1, "UTF8"))

details = []
for link in detaillinks:
    details.append(parseDetailspage(BeautifulSoup(requests.get(link).text),link))


json.dump(details, open("parlamentsspiegel-details.json", "w", -1, "UTF8"))


basisdoks = []
for link in details:
    basisdoks.append(parseBasisDok(BeautifulSoup(requests.get(link['basisdoklink']).text)))


json.dump(basisdoks, open("parlamentsspiegel-basisdoks.json", "w", -1, "UTF8"))

metadata = []
for detailsdata in details:
    if "doc_meta_link" in detailsdata.keys():
        metadata.append(parseBasisDok(BeautifulSoup(requests.get(detailsdata['basisdoklink']).text)))


json.dump(metadata, open("parlamentsspiegel-meta.json", "w", -1, "UTF8"))
