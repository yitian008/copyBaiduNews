#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
为类百度新闻项目爬取新闻数据
目标:
1.爬取网易新闻-滚动新闻列表-http://news.163.com/latest/
2.实现定时爬取
3.实现图片爬取(选做)

数据信息格式:
1.标题
2.时间
3.tag(选做)
4.正文
'''

import requests
from selenium import webdriver
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

import time
import gzip
import re
from StringIO import StringIO
import threading # 线程
import urllib
import urllib2
import random
import socket


# 把 str 编码由 默认ascii 改为 utf8:解决此类异常
# UnicodeDecodeError: 'ascii' codec can't decode byte 0xe4 in position 0: ordinal not in range(128)
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# get_single_page的一个过滤函数
def not_has_class_and_not_has_href(tag):
    return not tag.has_attr('class') and not tag.has_attr('href')

class News163_Spider():
    def __init__(self):
        self.spider_name = "Hello! I am News 163 Spider Created By LPF!\n"

    # 获取滚动新闻列表的链接地址
    def get_news_latest(self, url="http://news.163.com/latest/"):
        browser = webdriver.Firefox()
        browser.get(url)
        # 传给bs4
        bsObj = BeautifulSoup(browser.page_source)
        browser.quit()

        # 正则匹配目标链接<a>,正则表达式:以http://news.163.com/开头,并包含.html的<a>
        news_list = bsObj.find_all(href=re.compile(r'^http://news.163.com/(.*?).html(.*?)'))
        # 匹配结果最后一个不是想要的,去掉
        news_list = news_list[:-1]
        # 转成string
        news_list = ''.join(str(x) for x in news_list)
        # 转成BeautifulSoup
        news_list = BeautifulSoup(news_list)
        lists = []
        for i in news_list.find_all('a'):
            lists.append(i.get('href'))
        print '新闻数量:', len(lists)
        # 返回滚动新闻列表的全部链接
        return lists

    # 获取单一新闻内容页面的内容
    #1.标题; 2.时间; 3.tag(暂时未做); 4.正文
    def get_single_page(self, url):
        try:
            headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'}
            r = requests.get(url, headers=headers)
            bsObj = BeautifulSoup(r.text)

            #查找标题
            title = bsObj.h1.string
            # print title

            # 查找时间
            news_time = bsObj.find('div', class_='post_time_source')
            news_time = news_time.contents[0]
            # 正则
            pattern = r'(2017)(.*)'
            pattern = re.compile(pattern)
            news_time = re.search(pattern, news_time).group()
            news_time = news_time[:19]
            # print news_time

            # 查找正文
            content = bsObj.find_all('p', class_='')
            final_content = []
            for line in content:
                line = str(line)
                flag = True
                for g in (r'!--', r'style', r'AD', r'<a', r'img', r'用微信扫码二维码', r'分享至好友和朋友圈'):
                    if g in line:
                        flag = False
                if flag:
                    final_content.append(line)
            p = ''.join(str(x) for x in final_content)
            p = ''.join(str(x) for x in final_content)
            p = p.replace('<p>', '')
            p = p.replace('</p>', '\n')
            p = p.replace('<b>', '')
            p = p.replace('</b>', '\n')
            p = p.replace('<strong>', '')
            p = p.replace('</strong>', '')
            p = p.replace('\n\n','\n')
            p = p.replace('\n\n','\n')
            p = p.replace('<font>', '')
            p = p.replace('<br/>', '\n')
            # print p
            # 以dict形式返回新闻内容
            result_dic = {}
            result_dic['title'] = title
            result_dic['time'] = news_time
            result_dic['content'] = p
            return result_dic
        except:
            print 'This news fecth failed'
            dic = {}
            return dic

    def send_email(self, email_address, send_content):
        _user = "anlulpf@sina.com"  # 发件者的邮箱，需开通SMTP功能
        _pwd = "lpf20081113vic"  # 发件者的邮箱密码
        _to = email_address  # 收件者邮箱

        # 使用MIMEText构造符合smtp协议的header及body
        # 以下分别是正文、主题、发送者、收件者
        msg = MIMEText(send_content)
        msg["Subject"] = "网易滚动新闻"
        msg["From"] = _user
        msg["To"] = _to
        try:
            s = smtplib.SMTP("smtp.sina.com", timeout=30)  # 连接smtp邮件服务器,端口默认是25
            s.login(_user, _pwd)  # 登陆服务器
            s.sendmail(_user, _to, msg.as_string())  # 发送邮件
            s.close()
            print 'Email send succeed!'
        except:
            print 'Email send failed!'

def test():
    print 'Task Starting...'
    spider = News163_Spider()
    print spider.spider_name

    # spider.get_news_latest()
    # single_url = 'http://news.163.com/17/0404/13/CH6BE3OR0001875P.html'
    # result_dic = spider.get_single_page(single_url)
    # print 'title:'
    # print result_dic['title']
    # print 'time:'
    # print result_dic['time']
    # print 'content:'
    # print result_dic['content']

    # 获取列表信息
    url_lists = spider.get_news_latest()

    email_content = []
    # 获取单条新闻内容
    count = 1 # 计数,估计时间
    for url in url_lists:
        if count == 5:
            break
        print '正在爬取第', count, '条新闻...'
        count += 1
        dic = spider.get_single_page(url)
        one_news = []
        if dic:
            one_news.append(dic['title'])
            one_news.append(dic['time'])
            one_news.append(dic['content'])
            email_content.append(one_news)


    print '您好'
    # 邮件发送
    send_content = '你好,我是李鹏飞创建的网易新闻爬虫,以下是为您爬取的5条网易新闻...\n\n'
    for news in email_content:
        send_content += '新闻标题:'
        send_content += news[0]
        send_content += '\n\n'
        send_content += '新闻时间:'
        send_content += news[1]
        send_content += '\n\n'
        send_content += news[2]
        send_content += '\n\n'

    print '开始打印...'
    print send_content
    # 保存到本地
    f = open('test.txt', 'w')
    f.write(send_content)
    f.close()

    print 'spider mission completed!\nTask stopped!'

def main():
    print 'Task Starting...'
    spider = News163_Spider()
    print spider.spider_name
    url_list = spider.get_news_latest()
    # all_news_content 代表所有的新闻列表,共40条
    all_news_content = []
    count = 1
    for url in url_list:
        if count == 5:
            break
        print '正在爬取第%d页...' % count
        count += 1
        print url
        result_dic = spider.get_single_page(url)
        one_news = []
        if result_dic:
            one_news.append(result_dic['title'])
            one_news.append(result_dic['time'])
            one_news.append(result_dic['content'])
            all_news_content.append(one_news)

    # 邮件发送
    send_content = '你好,我是李鹏飞创建的网易新闻爬虫,以下是为您爬取的5条网易新闻...\n\n'
    for news in all_news_content:
        send_content += r'新闻标题:'
        print news[0]
        send_content += news[0]
        send_content += '\n'
        send_content += r'新闻时间:'
        send_content += news[1]
        send_content += '\n\n'
        send_content += r'新闻正文:'
        send_content += news[2]
        send_content += '\n\n\n'

    # 保存到本地
    f = open('test.txt', 'w')
    f.write(send_content)
    f.close()

    print 'spider mission completed!\nTask stopped!'
    pass

if __name__ == '__main__':
    main()