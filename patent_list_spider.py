#  encoding:utf-8

import requests
from bs4 import BeautifulSoup
import os
import sqlite3
from win32.win32crypt import CryptUnprotectData
import re
from time import sleep

public_date = '2017-12-22'
name_keyword = ['区块链', '智能合约', '共识', '工作量证明', '电子货币', '以太坊']


url = 'http://www.pss-system.gov.cn/sipopublicsearch/patentsearch/executeTableSearch0402-executeCommandSearch.shtml'
url2 = 'http://www.pss-system.gov.cn/sipopublicsearch/patentsearch/showSearchResult-startWa.shtml'
domain = 'www.pss-system.gov.cn'

keys =  '公开（公告）日>=%s AND 发明名称=(%s)' % (public_date, ' '.join(name_keyword))
vdb = "VDB:((PD>='%s' AND (TIVIEW='%s')))" % (public_date, "' or TIVIEW='".join(name_keyword))
data = {'searchCondition.searchExp': keys,
        'searchCondition.dbId': 'VDB',
        'searchCondition.searchType': 'Sino_foreign',
        'searchCondition.extendInfo[\'MODE\']': 'MODE_TABLE',
        'searchCondition.extendInfo[\'STRATEGY\']': 'STRATEGY_CALCULATE',
        'searchCondition.originalLanguage': '',
        'searchCondition.targetLanguage': '',
        'wee.bizlog.modulelevel': '0200201',
        'resultPagination.limit': 12}

start = 0
limit = 12
data2 = {'resultPagination.limit': limit,
         'resultPagination.sumLimit': 10,
         'resultPagination.start': start,
         'resultPagination.totalCount': 1563358,
         'searchCondition.searchType': 'Sino_foreign',
         'searchCondition.dbId': '',
         'searchCondition.extendInfo[\'STRATEGY\']': 'STRATEGY_CALCULATE',
         'searchCondition.strategy': '',
         'searchCondition.literatureSF': keys,
         'searchCondition.targetLanguage': '',
         'searchCondition.originalLanguage': '',
         'searchCondition.extendInfo[\'MODE\']': 'MODE_TABLE',
         'searchCondition.searchExp': keys,
         'resultPagination.sumLimit': 10,
         'searchCondition.executableSearchExp': vdb,
         'wee.bizlog.modulelevel': '0200201',
         'searchCondition.searchKeywords': '[2][ ]{0,}[0][ ]{0,}[1][ ]{0,}[7][ ]{0,}[.][ ]{0,}[1][ ]{0,}[2][ ]{0,}[.][ ]{0,}[2][ ]{0,}[2][ ]{0,}'
         }

def getcookiefromchrome(host):
    cookiepath=os.environ['LOCALAPPDATA']+r"\Google\Chrome\User Data\Default\Cookies"
    sql="select host_key,name,encrypted_value from cookies where host_key='%s'" % host
    with sqlite3.connect(cookiepath) as conn:
        cu=conn.cursor()        
        cookies={name:CryptUnprotectData(encrypted_value)[1].decode() for host_key,name,encrypted_value in cu.execute(sql).fetchall()}
#         print(cookies)
        return cookies

def patent_vector():
    return {'name' :'',
            'status' : '',
            'apply_id' : '',
            'apply_date' : '',
            'public_id' : '',
            'public_date' : '',
            'IPC' : '',
            'apply_person' : '',
            'invent_person' : '',
            'agent_person' : '',
            'agent' : '',
            }

def init_file(file):
    header = ['专利名称', '状态', '申请号', '申请日', '公开（公告）号', '公开（公告日）', 'IPC分类号', '申请（专利权）人', '发明人', '代理人', '代理机构']   
    file.write('\t'.join(header) + '\n' ) 

def deal_page(soup, file):
    patents = soup.findAll(name='div', attrs={'class':'item'})
    for item in patents:
        patent = patent_vector()
        patent['name'] = item.find(name='input', attrs={'name':'titleHidden'}).get('value').replace('<FONT>', '').replace('</FONT>', '')
        patent['status'] = item.find(name='a', attrs={'class':'btn btn-tag'}).get_text()
        
        body = item.find(name='div', attrs={'class':'item-content-body left'})
        body_p = body.findAll(name='p')
        
        patent['apply_id'] = body_p[0].get_text()[6:]
        patent['apply_date'] = body_p[1].find(name='a').get_text()
        patent['public_id'] = body_p[2].get_text().strip("\"\'")[10:]
        patent['public_date'] = body_p[3].find(name='a').get_text()
        patent['IPC'] = ';'.join([span.a.get_text().strip('\r\n\t \n') for span in body_p[4].findAll(name='span')])
        patent['apply_person'] = ';'.join([span.a.get_text().strip('\r\n\t \n') for span in body_p[5].findAll(name='span')])
        patent['invent_person'] = ';'.join([span.a.get_text().strip('\r\n\t \n') for span in body_p[6].findAll(name='span')])
        if len(body_p) > 7:
            patent['agent_person'] = body_p[7].get_text()[6:]
            patent['agent'] = body_p[8].get_text().strip('"')[7:]
        
        write(file, patent)
        
def write(file, patent):
    line = [patent['name'], 
            patent['status'],
            patent['apply_id'],
            patent['apply_date'],
            patent['public_id'],
            patent['public_date'],
            patent['IPC'],
            patent['apply_person'],
            patent['invent_person'],
            patent['agent_person'],
            patent['agent'],
            ]
#     print('\t'.join(line))
    file.write('\t'.join(line).replace('‑', '') + '\n')
    
    
        
if __name__ == '__main__':    
    file = 'res.txt'
    file = open(file, 'w')
    init_file(file)
    
    start = 0
    limit = 12
    
    response = requests.post(url, data=data, cookies=getcookiefromchrome(domain))
    sleep(1)
    content = response.content.decode('utf-8')
    soup = BeautifulSoup(content, "html.parser")
    page_info = soup.find(name='div', attrs={'class':'page_top'})
    pattern = r'共\xa0(\d*)\xa0页'
    page_count = re.search(pattern, str(page_info.contents[-1])).group(1)
    print('page_count: %s' % page_count)
    print('page 1')
    deal_page(soup, file)
    
    for i in range(1, int(page_count)):
        print('page %d' % (i+2,))
        start += limit
        data2['resultPagination.limit'] = limit
        data2['resultPagination.start'] = start
        response = requests.post(url2, data=data2, cookies=getcookiefromchrome(domain))
        sleep(1)
        content = response.content.decode('utf-8')
        soup = BeautifulSoup(content, "html.parser")
        
        deal_page(soup, file)
        
        
    print('over')

   
