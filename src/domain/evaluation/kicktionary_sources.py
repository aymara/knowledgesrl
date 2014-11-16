#!/usr/bin/env python3

import os
import glob
from xml.etree import ElementTree as ET
from hashlib import sha256
import pickle

KICKTIONARY_CORPUS = '/home/quentin/Projets/Kicktionary/corpus'


def add_www_hash(hashes, author, sentence):
    text_hash = sha256(sentence.encode('utf-8')).hexdigest()
    print('{} -> {}'.format(sentence, text_hash))
    hashes[text_hash] = ('WWW', author)

# TODO French

hashes = {}
for event in os.listdir(os.path.join(KICKTIONARY_CORPUS, 'EN', 'UEFA')):
    if not os.path.isdir(os.path.join(KICKTIONARY_CORPUS, 'EN', 'UEFA', event)):
        continue

    print()
    print()
    print(event)
    for report in glob.glob('{}/report*.xml'.format(os.path.join(KICKTIONARY_CORPUS, 'EN', 'UEFA', event))):
        print()
        print(report)
        report_xml = ET.ElementTree(file=report)
        author_xml = report_xml.find('teiHeader/author')
        if author_xml.get('first-name') == '' and author_xml.get('last-name') == '':
            author = None
        else:
            author = '{} {}'.format(author_xml.get('first-name'), author_xml.get('last-name'))

        for sentence in report_xml.findall('text/body/p/s') + report_xml.findall('text/body/head/s') + report_xml.findall('text/back/s'):
            sentence_text = ''.join(elem.text for elem in sentence).strip()
            text_hash = sha256(sentence_text.encode('utf-8')).hexdigest()
            print('{} -> {}'.format(sentence_text, text_hash))
            hashes[text_hash] = (event, author)

www_hashes = [
    {'url': 'http://en.wikipedia.org/w/index.php?title=Nwankwo_Kanu&oldid=598967785',
     'sentence': 'Thinking it to be an attacking move, he chased the throw-in down the right wing unchallenged, and centred the ball for Marc Overmars, who promptly scored to make the match 2-1.'},
    {'url': 'http://www.liverweb.org.uk/report.asp?rec_id=5977',
     'sentence': 'Davies centred the ball for Diouf who managed to hit the ball past Reina courtesy of a rebound.'},
    {'url': 'http://www.fijilive.com/soccer/',
     'sentence': 'Cristiano Ronaldo netted twice as Manchester United sent Portsmouth plummeting 3-1.'},
    {'url': 'http://www.smh.com.au/articles/2005/11/16/1132016861225.html',
     'sentence': 'Bresciano netted after a delightful move involving Tim Cahill, Mark Viduka and Harry Kewell, who had been introduced just minutes earlier as a substitute, to send a noisy crowd of more than 80,000 into raptures.'},

    {'url': 'http://www.dailymail.co.uk/pages/live/articles/sport/football.html?in_article_id=368563&in_page_id=1779/',
     'sentence': 'I was personally surprised to see Rooney dive in that game as I considered him to be one of those of those players that was beyond such behaviour.'},
    {'url': 'http://www.dailymail.co.uk/pages/live/articles/sport/football.html?in_article_id=368563&in_page_id=1779/',
     'sentence': 'Patrick Vieira claims Wayne Rooney dived to win the penalty which helped Manchester United end Arsenal\'s 49-match unbeaten league run last season.'},

    {'url': 'http://www2.club.ox.ac.uk/Football/Teams/men_mcr/',
     'sentence': 'The first goal came when Jon Brock received the ball inside the box on the right, feigned a shot then turned the ball onto his weaker left foot for a well placed strike into the right corner.'},
    {'url': 'http://www.fifa.com/en/news/feature/0,1451,104887,00.html',
     'sentence': 'He feigned a shot with his right foot, and then unleashed an awesome strike with his left that rocketed into the back of the net.'},
    {'url': 'http://news.bbc.co.uk/sport2/hi/football/eng_prem/4537460.stm',
     'sentence': 'Given was finally beaten when Crouch laid a ball into the path of a rampaging Gerrard, who wrong-footed the Newcastle defence by feigning a shot before powering home.'},
    {'url': 'http://www.sportnetwork.net/main/s378/st88765.htm',
     'sentence': 'On one occasion he feigned a pass with his left and passed with his right (or was it the other way around).'},

    {'url': 'http://thestar.com.my/',
     'sentence': 'The Stade de France crowd, which had jeered goalkeeper Fabien Barthez and Domenech before the game, booed the home team at the final whistle.'},
    {'url': 'http://observer.guardian.co.uk/sport/story/0,,1723855,00.html',
     'sentence': 'The magic went out of the game a little in the second half, replaced by more biting tackles and some aerial filth, which was duly booed by those traditionalists standing in their seats in the lower tier of the Bobby Moore Stand.'},

    {'url': 'http://news.bbc.co.uk/sport1/hi/football/league_cup/4366916.stm',
     'sentence': 'Fulham\'s reserve keeper miscontrolled a passback and Kanu pounced to dispossess him and put the visitors 2-1 ahead.'},
    {'url': 'http://newswww.bbc.net.uk/sport1/hi/football/teams/r/rangers/4058051.stm',
     'sentence': 'A great chance came Nacho Novo\'s way in the 36th minute when Barry Opdam miscontrolled to allow the Spaniard to race goalwards.'},

    {'url': 'http://www.chinadaily.com.cn/english/doc/2004-02/05/content_303281.htm',
     'sentence': 'Solari put Real ahead when he rifled the ball in from the edge of the area 10 minutes into the second half of what had been an evenly matched encounter.'},

    {'url': 'http://news.bbc.co.uk/sport1/hi/football/women/4637740.stm',
     'sentence': 'The second half was as tight as the first until England striker Kelly Smith netted Arsenal\'s third goal from a 72nd-minute penalty.'},




]

for sentence in www_hashes:
    add_www_hash(hashes, sentence['url'], sentence['sentence'])

pickle.dump(hashes, open('hashes_en.pickle', 'wb'))
