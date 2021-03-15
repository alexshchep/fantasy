#from lxml import html
import requests
import datetime as dt
import csv
import random
import time
import os.path
from bs4 import BeautifulSoup
from docutils.nodes import section
from fake_useragent import UserAgent

if __name__ == '__main__':
	startdate = dt.datetime(2017, 11, 21)
	quote = "\""
	double_quote = quote + quote
	url = 'http://www.hockey-reference.com/leagues/NHL_2018_games.html'
	base_url = 'http://www.hockey-reference.com'
	ua = UserAgent()
	myheader = {'User-Agent': ua.ff} 
	page = requests.get(url, headers = myheader)
	soup = BeautifulSoup(page.content, "lxml")
	#get game links
	mylinks = soup.find_all("a")
	gamelinks = []
	for link in mylinks:
		text = link.text
		try:
			linkdate = dt.datetime.strptime(text, "%Y-%m-%d")
			if linkdate <= startdate:
				continue
		except ValueError:
			continue
		gamelinks.append(link.get('href'))
	useragentlist = [ua.firefox, ua.ff]
	# go through game links
	for idx,url in enumerate(gamelinks):
                print(url)
		# check if file already exists
		filename = 'data/2018/new/nhl' + url.replace('/', '_')
		if os.path.isfile(filename):
			print('file {} already exists, skipping...'.format(filename))			
			continue
		archivefile = 'data/2018/archive/nhl' + url.replace('/', '_')
		if os.path.isfile(archivefile):
			print('file {} already exists in archives, skipping...'.format(archivefile))
			continue
		myua = random.choice(useragentlist)
		print('downloading {} as {}'.format(url, myua))
		myheader = {'User-Agent': myua}
		randomsec = random.randint(30,120)
		print('waiting for {} seconds'.format(randomsec))
		time.sleep(randomsec)
                try: 
                    page = requests.get(base_url+url, headers = myheader)
                except requests.exceptions.ConnectionError:
                    print('caught a connection error.. waiting 2 minutes')
                    time.sleep(120)
                    page = requests.get(base_url+url, headers = myheader)
                soup = BeautifulSoup(page.content, 'lxml')
		# write soup to csv

		with open(filename, 'w+') as f:
			print('writing to {}'.format(f))
			#csvwriter = csv.writer(f)
			lines = list(soup)
			for line in lines:
				f.write(str(line))
			#lines = [str(line).replace( double_quote, quote) for line in lines]

	print('done')
