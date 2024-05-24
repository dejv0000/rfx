import random
import time
import re
import os

import json
#import xml.etree.ElementTree as ET -> changes namespaces. so not using.
from lxml import etree as ET
from bs4 import BeautifulSoup
import requests


USER_AGENT_LIST = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'] #'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729)', 
USER_AGENT = {'User-Agent': random.choice(USER_AGENT_LIST)}


def getLastoutput():
    """get last output from xml file"""
    cwd = os.getcwd()
    infile = os.path.join(cwd, 'o/c.x')
    
    try:
        tree = ET.parse(infile)
    except:
        return None
    
    root = tree.getroot()

    return root


def getfeed():
    """get current feed from the site rss."""
    feedurl = 'https://www.chosun.com/arc/outboundfeeds/rss/category/national/?outputType=xml'

    r = Session.get(feedurl, headers=USER_AGENT)
    feedtext = r.text
    
    feedtext = re.sub(r'<\?xml.*?\?>', '', feedtext)
    #print(feedtext)
    
    root = ET.fromstring(feedtext)


    return root


def matchWithOld(curfeed, lastfeed):
    """find matching items from old feed"""

    oldItems = lastfeed.findall('.//item')
    curItems = curfeed.findall('.//item')
    
    keepList = []
    newList = []
    
    oldLinksText = []
    curLinksText = []
    
    for i in oldItems:
        oldLinksText.append(i.find('link').text)
    for j in curItems:
        curLinksText.append(j.find('link').text)
    
    
    #print('going through old items')
    for i in range(len(oldItems)): #keep existing items in old feed which are also in new feed.
        
        if oldItems[i].find('link').text in curLinksText:
            keepList.append(oldItems[i])
            #print(f"{oldItems[i].find('link').text} --->  keeping old item.")
            
        else:
            #print(f"{oldItems[i].find('link').text} --->  removing")
            pass
        
    #print('going through new items')
    for j in range(len(curItems)): #add new items in new feed which are not in old feed.
        
        if curItems[j].find('link').text not in oldLinksText:
            newList.append(curItems[j])
            #print(f"{curItems[j].find('link').text} --->  adding new item.")
        else:
            #print(f"{curItems[j].find('link').text} --->  already in old list.")
            pass
     
    return newList, keepList

def getContents(item):
    """get contents from the article page."""
    
    #print(item)
    
    url = item.find('link').text
    #print(url)
    contents = getContentsfromUrl(url)
    #print(contents)
    item.find('{http://purl.org/rss/1.0/modules/content/}encoded').text = contents
    
    return
    

def getContentsfromUrl(url):
    """get contents from the article page by url"""
    
    article_text = ''
    
    r = Session.get(url, headers=USER_AGENT)
    soup = BeautifulSoup(r.text, 'html.parser')
    sc = soup.select_one('script[id="fusion-metadata"]')
    jsonStr = re.search(r'Fusion.globalContent=({.*?});', sc.string)
    
    if jsonStr:
        #article_text = '<![CDATA['
        jsonStr = jsonStr.group(1)
        jsonStr = json.loads(jsonStr)
        content_elements = jsonStr['content_elements']
        for i in content_elements:
            if i['type'] == 'text':
                article_text = article_text + i['content'] + '<br><br>'
            elif i['type'] == 'image':
                
                try: #if img has caption
                    article_text = article_text + '<figure><img align="center" src="'+ i['url'] +'"><figcaption>' + i['caption'] + '</figcaption></figure><br><br>'
                except KeyError:                
                    article_text = article_text + '<figure><img align="center" src="'+ i['url'] +'">' + '<br><br>'
                    
        #article_text = article_text + ']]>'
    return article_text

def chMain():
    """main function"""
    lastfeed = getLastoutput()
    
    curfeed = getfeed()
    #print(curfeed)
    
    if lastfeed is not None: #lastfeed 있는 경우
        newList, keepList = matchWithOld(curfeed, lastfeed)
  
        allItems = curfeed.findall('.//item')
        #print(allItems)
        for i in allItems:
            #print(i)
            curfeed.find('channel').remove(i)
            
        # for i in newList:  #new feed 가져온 후에.. 뒤쪽에서 같이 추가하는 것으로 코드를.. element.insert(0, new_sub_element) https://stackoverflow.com/questions/12754872/insert-xml-element-as-first-child-using-elementtree-in-python
            
        #     curfeed.find('channel').append(i)
    
        for i in keepList:
            curfeed.find('channel').append(i)
    
    else: #최초 실행.
        newList = curfeed.findall('.//item')
        pass

    print(len(newList), len(keepList))
    k = 0
    for i in newList:
        if '오늘의 운세' not in i.find('title').text:
            getContents(i)
            curfeed.find('channel').insert(k, i)
            
            k = k+1
            
            time.sleep(random.uniform(5,10))
            
            
            if k == 20: break
    
    tree = ET.ElementTree(curfeed)
    outfile = os.path.join(os.getcwd(), 'o/c.x')
    tree.write(outfile, encoding='utf-8', xml_declaration=True, pretty_print=True)
    



if __name__ == "__main__":
    
    Session = requests.session()
    
    # while True:
    #     url = input('Enter url: ')
    #     print(getContentsfromUrl(url))
    
    chMain()
    
    # ll = [1,2,3,4,5]
    
    # for i in range(len(ll)):
    #     if ll[i] % 2 == 0:
    #         ll[i] = 0
            
    # print(ll)
    