import random
import json
from datetime import datetime, timedelta
from email import utils
import time
import os

from bs4 import BeautifulSoup
import requests
import xmltodict

USER_AGENT_LIST = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'] #'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729)', 
USER_AGENT = {'User-Agent': random.choice(USER_AGENT_LIST)}

TAGS = ['title', 'link', 'description', 'pubDate', 'guid', 'category', 'dc:creator', 'media:thumbnail']

#random 함수로 시간 추가해서 접속하는 시간도 매번 다르도록..
#print(USER_AGENT)

def getIn() -> dict:
    cwd = os.getcwd()
    infile = os.path.join(cwd, 'i/in')
    
    with open(infile, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    #print(data)
    return data


def getjson(urlStr: str, soupitem: str) -> str:
    
    r = reqSession.get(urlStr, headers=USER_AGENT)
    
    soup = BeautifulSoup(r.text, 'html.parser')
    jsonStr = soup.select_one(soupitem)
    #print(jsonStr)
    
    return jsonStr.string

def find_values(id, json_repr):
    results = []

    def _decode_dict(a_dict):
        try:
            if a_dict[id]:
                results.append(a_dict[id])
        except KeyError:
            pass
        return a_dict

    json.loads(json_repr, object_hook=_decode_dict) # Return value ignored.
    return results


def buildX(settings_item, art_items):
    
    
    feedtitle = settings_item['url'][0].rsplit('/')[-1]
    
    for i in art_items:
        
        try:
            i['title'] = ((i['kind2_name'] + ' : ') if i['kind2_name'] else '') + i['title']
            i['title'] = i['title'] + ((' - ' + i['sub_title'] ) if i['sub_title'] else '') 
            
            #i.pop('sub_title')
        except KeyError:
            pass    
        
        contents = i.pop('detail', '')
        bytesString = bytes(contents, encoding='utf-8')
        #i['description'] = '<![CDATA[' + bytesString.decode(encoding='utf-8') + ']]>'
        i['title'] = i['title'].replace('\u003cbr /\u003e', '')
        i['title'] = i['title'].replace('\u003cbr\u003e', '')
        i['description'] = bytesString.decode(encoding='utf-8').replace('\n', '')
        i['description'] = i['description'].replace('&lt;', '《') #fix. \u0026lt;\u0026gt;-> &lt;&gt;
        i['description'] = i['description'].replace('&gt;', '》')
      
        #<![CDATA[ this is <b>bold</b> ]]>
        datetime_str = i.pop('make_time' ,'')
        
        #2023-11-30T18:35:29.730000
        datetime_object = datetime.strptime(datetime_str.split('.')[0], '%Y-%m-%dT%H:%M:%S') - timedelta(hours = 9)
        
        i['pubDate'] =  utils.format_datetime(datetime_object)
        
        i['category'] = feedtitle
        i['link'] = settings_item['url'][0] + '/'+ str(i.pop('news_serial', '')) ######
        i['guid'] = {'@isPermaLink':'true', '#text': i['link']}
        
        soup = BeautifulSoup(i['description'], 'html.parser')
        img = soup.select_one('img')
        
        try:
            i['media:thumbnail'] = img['src']
        except TypeError:
            pass
        
        author = i.pop('authors', '')
        if type(author) == type({}):
            #print(str(author))
            
            author = find_values("AuthorName", json.dumps(author))
        
        i['dc:creator'] = author
        
        #i['description'] = 'aa'
        
        copied = i.copy()
        
        for k, v in copied.items():
            if not(k in TAGS):
                i.pop(k)
    
    #nowdt = datetime.now() + timedelta(hours=9)
    
    
    rssxml = {"rss": {"@version":"2.0", "channel": {"title":feedtitle, "description": feedtitle, "link": settings_item['url'][0],  "language": "ko", "item": art_items}}} #"lastBuildDate": utils.format_datetime(nowdt),
    
    return rssxml


if __name__ == "__main__":
    
    settings = getIn()
    reqSession = requests.session()
    
    for key, value in settings.items():
        if len(settings[key]['url']) > 1 : #if there's more than one url.
            
            a = []
            for i in range(len(settings[key]['url'])):
                
                time.sleep(random.uniform(5,60))
                
                # with open(f'o\\{key}-{i+1}.json', 'r', encoding='utf-8') as f:
                #     data = f.read()
                
                data = getjson(settings[key]['url'][i], settings[key]["soup"]) 
                vals = find_values(settings[key]['json'], data)[0] #contents are nested in list
    
                a = a + vals
        
        else:
            a = []
            time.sleep(random.uniform(10,120))
            # with open(f'o\\{key}.json', 'r', encoding='utf-8') as f:
            #     data = f.read()

            data = getjson(settings[key]['url'][0], settings[key]["soup"]) 
                
            vals = find_values(settings[key]['json'], data)[0] #contents are nested in list
    
            a = vals
            
        #print(a)
        x =  buildX(settings[key], a)
            
        
        xmltext = xmltodict.unparse(x, pretty=True)
        cwd = os.getcwd()
        outfile = os.path.join(cwd, f'o/{key}.x')
        with open(outfile, 'w', encoding='utf8') as f:
            f.write(xmltext)
   
        
    #print(a[0][0]['title'])
    
# if False:    
#     urls = getIn()
    

#     for k, v in urls.items():
        
#         htmlStr = ""
#         for i in v["url"]:
            
#             #print(v["soup"])
#             htmlStr = htmlStr + getjson(i, v["soup"])
            
#         with open(f'o\\{k}.json', 'w', encoding='utf-8') as f:
#             f.write(htmlStr)
