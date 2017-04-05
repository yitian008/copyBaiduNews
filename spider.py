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
import jieba
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.cluster import KMeans



# 把 str 编码由 默认ascii 改为 utf8:解决此类异常
# UnicodeDecodeError: 'ascii' codec can't decode byte 0xe4 in position 0: ordinal not in range(128)
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

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
            # 过滤掉图片类新闻
            if 'photoview' in i.get('href'):
                pass
            else:
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
            p = p.replace('\n\n', '\n')
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

    # 发送邮件模块
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

#获取全部新闻语料
def get_all_corpus():
    print 'Task Starting...'
    spider = News163_Spider()
    print spider.spider_name
    url_list = spider.get_news_latest()
    # all_news_content 代表所有的新闻列表,共40条
    all_news_content = []
    count = 1
    for url in url_list:
        # if count == 6:
        #     break
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
    # 返回的语料库
    all_corpus = ' '.join(all_news_content[i][2] for i in range(0, len(all_news_content)))
    with open('corpus.txt', 'w') as fp:
        fp.write(all_corpus)
    # 返回的新闻内容list,供feature_matrix_generate使用
    all_corpus_list = []
    for i in range(0, len(all_news_content)):
        all_corpus_list.append(all_news_content[i][2])
    # 返回每篇文章的标题
    all_corpus_name_list = []
    for i in range(0, len(all_news_content)):
        all_corpus_name_list.append(all_news_content[i][0])
    return all_corpus, all_corpus_list, all_corpus_name_list

# 根据语料库生成词向量空间,返回words_space_list
def word_vector_space(stop_words_filename, corpus_filename):
    stop_words = []
    with open(stop_words_filename, 'r') as fp:
        lines = fp.readlines()
        for line in lines:
            stop_words.append(line.strip())

    word_space = set()
    with open(corpus_filename, 'r') as fp:
        content = fp.read()
        seg_list = jieba.cut(content, cut_all=False)
        for i in seg_list:
            word_space.add(i)
    # 去掉停用词
    for i in stop_words:
        if i in word_space:
            word_space.remove(i)
    # set没有顺序,不利于特征提取,转为有序的list
    words_space_list = []
    for i in word_space:
        words_space_list.append(i)
    return words_space_list

# 计算单篇文章的词频向量,函数内调用
def vector_generate(one_news_content, words_space_list):
    vector = [0] * len(words_space_list)

    seg_list = jieba.cut(one_news_content, cut_all=False)
    dic = {}
    for i in seg_list:
        if i in dic:
            dic[i] += 1
        else:
            dic[i] = 1

    keys = set()
    for i in dic.keys():
        keys.add(i)

    count = 0
    for word in words_space_list:
        if word in keys:
            vector[count] = dic[word]
        count += 1
    return vector

# 生成特征矩阵,传入all_corpus_list,每个元素代表一篇文章的string
def feature_matrix_generate(corpus, words_space_list):
    print 'corpus含有 %d 篇新闻文章' % len(corpus)
    feature_matrix = []
    for one_news in corpus:
        feature_matrix.append(vector_generate(one_news, words_space_list))
    feature_matrix = np.array(feature_matrix)
    transformer = TfidfTransformer(smooth_idf=False)
    tfidf = transformer.fit_transform(feature_matrix)
    feature_matrix = tfidf.toarray()
    # 返回tf-idf计算之后的结果作为特征矩阵
    print feature_matrix
    print '特征长度: %d' % len(feature_matrix[0])
    return feature_matrix

# 聚类算法,参数并没有给接口,待修改
def cluster(feature_matrix, n_clusters):
    random_state = 170
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state).fit(feature_matrix)
    print kmeans.labels_
    return kmeans.labels_




def mail_test():
    print 'Task Starting...'
    spider = News163_Spider()
    print spider.spider_name
    url_list = spider.get_news_latest()
    # all_news_content 代表所有的新闻列表,共40条
    all_news_content = []
    count = 1
    for url in url_list:
        # if count == 6:
        #     break
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
    send_content = '你好,我是李鹏飞创建的网易新闻爬虫,以下是为您爬取的%d条网易新闻...\n\n' % len(all_news_content)
    for news in all_news_content:
        send_content += '******************************************************\n'
        send_content += r'新闻标题:'
        send_content += news[0]
        send_content += '\n'
        send_content += r'新闻时间:'
        send_content += news[1]
        send_content += '\n\n'
        send_content += news[2]

    # 保存到本地
    f = open('test.txt', 'w')
    f.write(send_content)
    f.close()

    print 'spider mission completed!\nTask stopped!'


def main():
    all_corpus, all_corpus_list, all_corpus_name_list = get_all_corpus()
    words_space_list = word_vector_space('stop_words.txt', 'corpus.txt')
    feature_matrix = feature_matrix_generate(all_corpus_list, words_space_list)
    n_clusters = 8
    labels = cluster(feature_matrix, n_clusters)
    # 打印三类看看
    for i in range(n_clusters):
        print '第 %d 类新闻:' % (i+1)
        for j in range(len(labels)):
            if labels[j] == i:
                print all_corpus_name_list[j]
        print '**********************'


if __name__ == '__main__':
    main()