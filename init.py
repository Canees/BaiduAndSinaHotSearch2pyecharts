import requests
from lxml import etree
import json
import os
import time
# import numpy as np
# import matplotlib.pyplot as plt
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.commons.utils import JsCode
# 配置ehcarts路径
from pyecharts.globals import CurrentConfig
CurrentConfig.ONLINE_HOST = "http://172.16.102.9:8087/echarts_lib/"


def requestd(url):
    # request:
    t = requests.get(url=url, headers={
        "user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
        "Cookie": "BAIDUID=B7F548F09EEC3FB817FEE54D9E4FB734:FG=1; BD_NOT_HTTPS=1; PSTM=1589783384; BIDUPSID=B7F548F09EEC3FB817FEE54D9E4FB734; BDSVRTM=10; BD_HOME=1; H_PS_PSSID=1445_31326_21081_31111_31593_31525_31464_31322_30823"
    }).text
    return t


def sina2hot(url):
    # 新浪热搜数据:
    r = requestd(url)
    html = etree.HTML(r)
    # 匹配需要的字段
    a_herfs = html.xpath('//table/tbody/tr/td[@class="td-02"]/a/@href')
    a_text = html.xpath('//table/tbody/tr/td[@class="td-02"]/a/text()')
    a_num = html.xpath('//table/tbody/tr/td[@class="td-02"]/span/text()')
    # 组装成一个list
    big_list = []
    host = 'https://s.weibo.com'
    for i, value in enumerate(a_num):
        obj = dict()
        obj['url'] = host + a_herfs[i]
        obj['name'] = a_text[i]
        obj['num'] = int(a_num[i])
        obj['type'] = '新浪热搜'
        obj['strnum'] = str(int(obj['num']/10000))+'万'
        big_list.append(obj)
    return big_list


def baidu2hot(url):
    # 百度热搜数据:
    b = requestd(url)
    html = etree.HTML(b)
    hotsearch = html.xpath('//textarea[@id="hotsearch_data"]/text()')
    big_list = []
    host = 'http://www.baidu.com/s?tn=news&wd='
    for item in hotsearch:
        josondb = json.loads(item)
        for items in josondb['hotsearch']:
            obj = dict()
            obj['url'] = host + items['pure_title']
            obj['name'] = items['pure_title']
            obj['num'] = int(items['heat_score'])
            obj['type'] = '百度热搜'
            obj['strnum'] = str(int(obj['num']/10000))+'万'
            obj['htmls'] = getnewdetails(obj['url'])
            big_list.append(obj)
    return big_list


def getnewdetails(url):
    # 获取新闻详情数据:
    t = requestd(url)
    html = etree.HTML(t)
    aherf = html.xpath('//h3[@class="c-title"]/a/@href')
    newdb = ''
    for item in aherf:
        if 'baijiahao.baidu.com' in item:
            s = requestd(item)
            htmls = etree.HTML(s)
            # # 获取元素=>转成html
            result = htmls.xpath('//*[@class="article-content"]/p')
            for i in result:
                newdb += etree.tostring(i, encoding='utf-8').decode()
            # print(newdb)
    return newdb


def save2json(file_save_path, file_db_list):
    # 数据存json文件:
    # 中文禁用ascii,采用UTF8
    if file_save_path:
        os.chdir(file_save_path)
    with open('test.json', 'w', encoding='utf-8') as F:
        json.dump(file_db_list, F, ensure_ascii=False)
    pass


def init2db(file_save_path):
    # 合并数据list:
    sinaurl = 'https://s.weibo.com/top/summary?cate=realtimehot'
    baidurl = 'http://www.baidu.com/'
    # 合并list
    all_list = sina2hot(sinaurl) + baidu2hot(baidurl)

    # 倒序=》根据浏览量排序
    new_list = sorted(all_list, key=lambda num: num['num'], reverse=True)
    # print('总共', str(len(new_list)))
    # 去重
    new_list_1 = []
    seen = []
    for d in new_list:
        t = d['name']
        if t not in seen:
            seen.append(t)
            new_list_1.append(d)
    print('去重排序后总共', str(len(new_list_1)))
    # 图表展示
    json2charts(new_list_1, file_save_path)
    save2json(file_save_path, new_list_1)
    pass


def json2charts(all_list, file_save_path):
    # 图形化:
    bar = Bar()
    # 重新处理echarts需要的数据
    for item in all_list:
        db = []
        obj = dict()
        obj['name'] = item['name']
        obj['value'] = item['num']
        db.append(obj)
        bar.add_yaxis(item['type'], db)
    nowtime = time.strftime("%Y-%m-%d")
    bar.add_xaxis([nowtime])
    bar.set_series_opts(
        label_opts=opts.LabelOpts(is_show=False),
        # label_opts=opts.LabelOpts(formatter=JsCode(
        #     "function(x){return parseInt(x.value/10000)+'万'}"
        # )),
        # 数据要传递过去
        tooltip_opts=opts.TooltipOpts(formatter=JsCode(
            "function(x){return '平台：'+ x.seriesName+'<br/>'+'事件：'+x.name+'<br/>'+'搜索量：'+ parseInt(x.value/10000) + '万' }"
        ))
    )
    bar.render(file_save_path+'/index.html')


if __name__ == "__main__":
    # 保存位置自定
    init2db('C:/Users/Canner/Desktop/BaiduAndSinaHotSearch2pyecharts')
    # 每分钟抓一次
    while True:
        time.sleep(300)
        init2db('C:/Users/Canner/Desktop/BaiduAndSinaHotSearch2pyecharts')
        pass
