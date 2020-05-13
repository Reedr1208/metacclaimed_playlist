#main build playlist
import metacritic_scrape as mta
import spotify_playlist as spt
import unicodecsv as csv
import pandas as pd
import time
import datetime
from dateutil.relativedelta import relativedelta
from spotify_creds import refresh_token, client_id, client_secret, user_id



#wrap spotify functions in here to retry & throttle requests due to rate limiting
def try_func(sleep_time, max_retries, function, *args, **kwargs):
	function_successful=False
	retries=0
	while retries<=max_retries:

		try:
			return function(*args, **kwargs)
			function_successful=True
		except Exception:
			print('Timeout occured on server side')
			print('Trying re-attempting in {} seconds\n'.format(sleep_time))
			time.sleep(sleep_time)
			retries+=1
	print('Function continues to fail. Aborting Script')
	sys.exit()

#get last 2 months in metacritic's format
def last_2_months():
	#return like [('Apr', 2018), ('Mar', 2018)]
	cur_dt=datetime.datetime.today()

	cur_month=cur_dt.strftime('%h')
	cur_year= cur_dt.year

	last_month_dt= cur_dt + relativedelta(months=-1)
	last_month= last_month_dt.strftime('%h')
	last_month_year= last_month_dt.year

	return [(last_month, last_month_year),(cur_month, cur_year)]


#minimum metascore for album to be included in playlist
min_score=77

#number of tracks to add from each album
num_tracks=2

#how long to pause spotify requests and number of retries if rate limit is hit
timeout_pause=5
timeout_retries=2



date_info= last_2_months()

#scrape metacritic and create playlist for each month
for item in date_info:
	month= item[0]
	year= item[1]
	
	filename='recent_albums_{}_{}.csv'.format(month, str(year)[2:])
	playlist_name='metacclaimed_{}_{}'.format(month, str(year)[2:])

	print('Working on {}....'.format(month))

	#scrape metacritic for qualifying albums for desired month and write results to file
	mta.main_scrape_metacritic(month, min_score, filename)


	#authenticate & set headers
	access_token=spt.refresh_access_token(refresh_token, client_id, client_secret)
	headers= {'Authorization': 'Bearer {}'.format(access_token), 'Content-Type':'application/json'}

	#get playlist id or generate new one
	playlist_id=spt.create_playlist(headers, 
									playlist_name, 
									user_id, 
									public=True, 
									description=None, 
									replace_if_existing=True)
	
	#delete all tracks from existing playlist for a full replace
	try_func(timeout_pause, 
			timeout_retries, 
			spt.delete_pl_tracks, 
			headers, 
			playlist_id, 
			user_id)

	#load the file generated from metacritic into dataframe
	album_table= pd.read_csv(filename, encoding = 'utf8')


	#loop over each album, search for it in spotify, and add most popular tracks to playlist
	for index, row in album_table.iterrows():
		try:
			print(u'adding tracks from "{}" by "{}"'.format(unicode(row['album_name']), unicode(row['artist'])))
		except UnicodeEncodeError:
			print(u'adding tracks')

		#search spotify for an album with matching name and artist
		album_id=try_func(timeout_pause, 
						timeout_retries, 
						spt.get_album_id, 
						headers, 
						unicode(row['album_name']), 
						unicode(row['artist']))

		#if album is found, add the N most popular tracks from album to playlist
		if album_id!=None:
			try_func(timeout_pause, 
					timeout_retries, 
					spt.add_top_album_tracks_to_playlist, 
					headers, 
					user_id, 
					album_id, 
					playlist_id, 
					num_tracks=num_tracks)
			#spt.add_top_album_tracks_to_playlist(headers, user_id, album_id, playlist_id, num_tracks=num_tracks)
		else:
			print('No matching album found')