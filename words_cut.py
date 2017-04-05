#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
1.使用jieba分词,将大量新闻文本分词,去掉停用词,形成词向量特征
2.对每篇文章 形成词向量
3.使用kmeans聚类分析
'''

import jieba
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.cluster import KMeans

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# 根据语料库生成词向量空间
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

# 计算单篇文章的词频向量
def vector_generate(one_news_filename, words_space_list):
    vector = [0] * len(words_space_list)
    with open('oneNews.txt', 'r') as fp:
        content = fp.read()
        seg_list = jieba.cut(content, cut_all=False)
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
    # tf-idf
    return vector

# 生成特征矩阵,传入corpus列表,每个元素代表一篇文章的string
def feature_matrix_generate(corpus):
    feature_matrix = []
    for one_news in corpus:
        feature_matrix.append(vector_generate(one_news))
    feature_matrix = np.array(feature_matrix)
    transformer = TfidfTransformer(smooth_idf=False)
    tfidf = transformer.fit_transform(feature_matrix)
    feature_matrix = tfidf.toarray()
    # 返回tf-idf计算之后的结果作为特征矩阵
    return feature_matrix




# 聚类算法
def cluster(feature_matrix):
    random_state = 170
    kmeans = KMeans(n_clusters=2, random_state=random_state).fit_predict(feature_matrix)
    print kmeans.labels_



def main():
    words_space_list = word_vector_space('stop_words.txt', 'corpus.txt')
    print 'words_space_list length is : %d' % len(words_space_list)
    # for i in range(20):
    #     print words_space_list[i]
    vector = vector_generate('oneNews.txt', words_space_list)
    print 'vector length is : %d' % len(vector)
    print vector[:1000]

    pass



if __name__ == '__main__':
    main()