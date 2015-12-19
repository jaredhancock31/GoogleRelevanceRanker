#!/usr/bin/env python

# Author: Jared Hancock

# NOTE: if nltk.data error: enter "include nltk.download" in a python terminal

import json, re, math, nltk, string
from urllib2 import urlopen
from nltk.corpus import stopwords
from collections import Counter
from nltk import PorterStemmer


API_KEY = 'insert key here'
CX_KEY = 'insert key here'
STOPS = [word.encode('utf-8') for word in stopwords.words('english')]

class Result:
    def __init__(self, rank, title, url, snippet):
        self.rank = rank
        self.title = title
        self.url = url
        self.snippet = snippet
        self.tokens = None
        self.vector = None
        self.jaccard = 0
        self.cosine = 0


'''
    Removes punctuation, bullets, and middots from text
        @param string text: text to be edited
    @return string: text without punctuation
'''
def removePunct( text ):
    text = text.decode("utf-8").replace(u"\u2022", "").replace(u"\u00B7", "")   # get rid of bullets and middots
    return re.sub('[%s]' % re.escape(string.punctuation), '', text).encode("utf-8")

'''
    Pre-processes text by tokenizing, removing stop words, and stemming to prepare for comparison
        @param string text: text to be edited
    @return list of preprocessed string tokens
'''
def preprocess( result ):
    words = removePunct(result.title)
    words += " "
    words += removePunct(result.snippet)
    result.tokens = nltk.word_tokenize(words)
    for tok in result.tokens:
        if tok not in STOPS:
            tok = PorterStemmer().stem(tok.decode('utf-8'))
            tok = tok.lower().encode('utf-8')
    return result


'''
    Calculates jaccard coefficient between two samples of text
        @param string result: text rendered from a search result
        @param string relevant: text to test the result string against for similarity
    @return float: jaccard coefficient
'''
def jaccard( result, relevant ):
    n = len(result.intersection(relevant))
    return n / float(len(result) + len(relevant)- n)


'''
    Calculates cosine similarity based on term frequency
        @param dict vec1: dict including terms and the number of occurrences for each word
        @param dict vec2: dict including terms and the number of occurrences for each word
    @return float: cosine similarity between 2 vector params
'''
def calc_cos( vec1, vec2 ):
    intersection = set(vec1.keys()) & set(vec2.keys())  # bitwise AND
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator


'''
    Searches google for a search term
        @param string query: search term
        @param list Result resList: list of Result objects containing search results
        @param int start: Index of results to begin from (Google API only allows 10 results per request)
    @return None
'''
def googleSearch( query, resList, start):
    url = 'https://www.googleapis.com/customsearch/v1?key=AIzaSyACR0s18hhnQD52hqGGEMEMO3ESpHh65k4&start='+str(start)+'&prettyPrint=true&cx=014898526197053737379:tql4sbmedis&q='+query
    req = urlopen(url)
    data = json.load(req)

    i = start
    for item in data['items']:
        r = Result(i, item['title'].encode('utf8'), item['link'].encode('utf8'), item['snippet'].encode('utf8'))
        resList.append(r)
        i += 1


'''
    Main controller; Conducts user interface and I/O
        @param dict vec1: dict including terms and the number of occurrences for each word
        @param dict vec2: dict including terms and the number of occurrences for each word
    @return float: cosine similarity between 2 vector params
'''
def searchRank( query ):
    resList = []    # list of search result objects
    relList = []    # list of "indexes" of relevant results

    googleSearch(query, resList, 1)
    googleSearch(query, resList, 11)

    for r in resList:
        r = preprocess(r)       # initialize tokens attribute with pre-processed words
        r.vector = Counter(r.tokens)
        print r.rank
        print r.title
        print r.url
        print r.snippet
        print

    # ask user which results are relevant
    print "Choose up to 5 results that were relevant to your search."
    print "Enter a negative number to quit."
    relNum = int(input("Enter a result number: "))
    i = 0
    while relNum >= 0 and i < 5:
        if relNum not in relList:
            relList.append(relNum)
        else:
            print "Error: You already entered that result"
        i += 1
        relNum = int(input("Enter a result number ( negative to quit ): "))

    # write relevant data to file
    infile = open(query+'.txt', 'wb')
    for i in relList:
        for r in resList:
            if i == r.rank:
                infile.write(r.title + ' ')
                infile.write(r.snippet + ' ')
    infile.close()

    '''--------------------pre-process our relevance test set-------------------------'''
    readfile = open(query+'.txt', 'rb')
    relWords = readfile.read()
    relWords = removePunct(relWords)
    relTokens = nltk.word_tokenize(relWords)

    infile = open(query+'-clean.txt', 'w')

    for tok in relTokens:
        if tok not in STOPS:
            tok = PorterStemmer().stem(tok.decode('utf-8'))
            tok = tok.lower().encode('utf-8')
            infile.write(tok + ' ')

    infile.close()

    '''--------------------calculate, sort, and display----------------------------------'''
    relevanceVector = Counter(relTokens)    # get vector for relevance data to calc similarity

    print "Calculating relevancy of your search results......"
    # calculate similarity
    for r in resList:
        r.cosine = calc_cos(r.vector, relevanceVector)
        r.jaccard = jaccard(set(r.tokens), set(relTokens))
        # print "cosine:", r.cosine
        # print "jaccard:", r.jaccard

    print "Select sorting preference:"
    print "[1] Jaccard Coefficient"
    print "[2] Cosine Similarity"
    print
    sortChoice = raw_input("Enter choice here: ")

    if sortChoice.lower() in ['1', 'j', 'jaccard', 'jaccard coefficient']:
        resList.sort(key = lambda x: x.jaccard, reverse=True)
        print "Showing results based on jaccard coeffecient: "
    elif sortChoice.lower() in ['2', 'c', 'cosine','cosine similarity']:
        resList.sort(key = lambda x: x.cosine, reverse=True)
        print "Showing results based on cosine similarity: "

    for r in resList:
        print
        print r.rank
        print r.title
        print r.url
        print r.snippet
        print

if __name__=="__main__":
    q = raw_input("Query to search for: ")
    q = q.replace(' ', '+')
    searchRank(q)

