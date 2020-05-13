from bs4 import BeautifulSoup
from urllib2 import Request, urlopen
import urllib2
import re
import unicodecsv as csv
from datetime import datetime
import sys
import time




def main_scrape_metacritic(month, min_score, filename):

	albums_table=[]

	#search first 2 pages for recent albums
	#page0_url='http://www.metacritic.com/browse/albums/release-date/new-releases/date/w/api.php?'
	#page1_url='http://www.metacritic.com/browse/albums/release-date/new-releases/date/w/api.php?page=1'
	page0_url='http://www.metacritic.com/browse/albums/release-date/new-releases/date'
	page1_url='http://www.metacritic.com/browse/albums/release-date/new-releases/date?page=1'

	for i, url in enumerate([page0_url, page1_url]):
		print('Scraping metacritic page {}'.format(i+1))

		req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
		#req = urllib2.Request('http://www.metacritic.com/browse/albums/release-date/new-releases/date?view=detailed', headers={'User-Agent': 'Mozilla/5.0'})
		webpage = urllib2.urlopen(req).read()

		#save html to avoid rate limits while testing/developing
		f=open('meta{}.html'.format(i), 'w')
		f.write(webpage)
		f.close()


		recent_albums_html= BeautifulSoup(webpage, 'html.parser')

		#album html objects
		a_tags= recent_albums_html.findAll(name='li', attrs={'class':re.compile('^product release_product')})


		for album_elem in a_tags:

			#will be used to generate a dataset of qualified albums to write to file
			row= {}

			#get release date of album and skip if not desired month
			date_obj= album_elem.find(name='li', attrs={'class':'stat release_date'}).find(name='span', attrs={'class':'data'})
			raw_date= date_obj.get_text().strip()
			if raw_date.split(' ')[0]!=month:
				continue
			row['release_date']= raw_date

			#get album score and skip if it doesnt meet threshold
			score_obj= album_elem.find(name='div', attrs={'class':'basic_stat product_score brief_metascore'})
			raw_score= score_obj.div.get_text().strip()
			try:
				raw_score=int(raw_score)
			except ValueError:
				raw_score=0
			if raw_score<min_score:
				continue
			row['score']=raw_score

			
			#album name
			row['album_name']= album_elem.div.div.a.get_text().strip()

			#artist name
			artist_obj= album_elem.find(name='li', attrs={'class':'stat product_artist'})
			artist_obj= artist_obj.find(name='span', attrs={'class':'data'})
			row['artist']= artist_obj.get_text().strip()

			albums_table.append(row)

		time.sleep(10)


	if len(albums_table)==0:
		print('Error: Album table is blank. Check logic and input')
		sys.exit()

	#write dataset to file	
	csvfile= open(filename, 'w')
	fieldnames = ['artist', 'album_name', 'score', 'release_date']
	writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	writer.writeheader()

	for row in albums_table:
		#print(type(row['artist']), type(row['album_name']))
		writer.writerow(row)

	csvfile.close()

if __name__ == "__main__":
	main_scrape_metacritic('May', 77, 'manual_test.csv')
