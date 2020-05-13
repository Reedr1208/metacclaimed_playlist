import sys
import requests
import json
import urllib
import base64
import time

#scopes
#playlist-modify-private
#playlist-read-priva
#playlist-modify-public

#get new auth code
#https://accounts.spotify.com/en/authorize?client_id=ad7db8a311f246c982f7fb36df2b58a3&response_type=code&redirect_uri=http:%2F%2Fwww.google.com&scope=playlist-modify-private+playlist-modify-public+playlist-read-private


def get_token_for_new_code(client_id, client_secret, redirect_uri, code):
	payload= {'client_id':client_id, 'client_secret':client_secret, 'grant_type':'authorization_code', 'redirect_uri':redirect_uri, 'code':code}
	response=requests.post('https://accounts.spotify.com/api/token', data=payload)
	if not 200 <= response.status_code <= 299:
		print(response.content)
	else:
		response=response.json()
		print('access_token="{}"'.format(response['access_token']))
		print('refresh_token="{}"'.format(response['refresh_token']))

	print('\n\n\n')
	print(json.dumps(response))
	sys.exit()


def refresh_access_token(refresh_token, client_id, client_secret):
	payload= {'grant_type':'refresh_token', 'refresh_token':refresh_token}
	encoded = base64.b64encode('{}:{}'.format(client_id, client_secret))
	headers= {'Authorization':'Basic {}'.format(encoded)}
	response=requests.post('https://accounts.spotify.com/api/token', headers=headers, data=payload)
	if not 200 <= response.status_code <= 299:
		print(response.content)
		raise Exception('Raising error due to invalid status code')
	else:
		response=response.json()
		#print('access_token={}'.format(response['access_token']))
		access_token=response['access_token']
	return access_token



#get_token_for_new_code(client_id, client_secret, redirect_uri, code)
#access_token=refresh_access_token(refresh_token, client_id, client_secret)


def get_playlist_id(headers, user_id, playlist_name):
	#find playlist 
	pl_id=None
	next_page= 'https://api.spotify.com/v1/users/{}/playlists'.format(user_id)

	while next_page!=None:
		response= requests.get(next_page, headers=headers)
		
		if not 200 <= response.status_code <= 299:
			print('Error: status code {}'.format(response.status_code))
			print('url: {}'.format(response.url))
			print(response.content)
			raise Exception('Raising error due to invalid status code')

		pl_obj=response.json()
		pl_list= pl_obj['items']

		next_page=pl_obj['next']

		for pl in pl_list:
			if pl['name']==playlist_name:
				pl_id=pl['id']
				next_page=None
				break
	return pl_id


def delete_pl_tracks(headers, playlist_id, user_id):
	print('Clearning existing tracks from playlist...')
	playlist_json=requests.get('https://api.spotify.com/v1/users/{}/playlists/{}'.format(user_id, playlist_id), headers=headers, params={'fields':'tracks.items.track.uri'}).json()
	remaining_tracks= playlist_json['tracks']['items']
	

	while len(remaining_tracks)>0:
		payload=json.dumps({'tracks':[{'uri':i['track']['uri']} for i in remaining_tracks]})
		response=requests.delete('https://api.spotify.com/v1/users/{}/playlists/{}/tracks'.format(user_id, playlist_id), headers=headers, data=payload)
		if not 200 <= response.status_code <= 299:
			print('Error: status code {}'.format(response.status_code))
			print('url: {}'.format(response.url))
			print(response.content)
			raise Exception('Raising error due to invalid status code')

		playlist_json=requests.get('https://api.spotify.com/v1/users/{}/playlists/{}'.format(user_id, playlist_id), headers=headers, params={'fields':'tracks.items.track.uri'}).json()
		remaining_tracks= playlist_json['tracks']['items']


def create_playlist(headers, playlist_name, user_id, public=True, description=None, replace_if_existing=True):
	existing_pl_id= get_playlist_id(headers, user_id, playlist_name)
	
	if existing_pl_id:
		return existing_pl_id

	else:
		#create playlist
		headers['Content-Type']= 'application/json'
		params= {'name':playlist_name, 'public':public, 'description':description}
		response= requests.post('https://api.spotify.com/v1/users/{}/playlists'.format(user_id), headers=headers, json=params)
		if not 200 <= response.status_code <= 299:
			print('Error: status code {}'.format(response.status_code))
			print('url: {}'.format(response.url))
			print(response.content)
			raise Exception('Raising error due to invalid status code')
		else:
			print('playlist "{}" created successfully'.format(playlist_name))
			return response.json()['id']





#uses spotify search endpont to search for album name
#only returns ID if album name and artist ID matches the metacritic values
def get_album_id(headers, album_name, artist_name):

	target_album_name= album_name
	target_artist= artist_name

	payload={'q':album_name, 'type':'album'}
	response= requests.get('https://api.spotify.com/v1/search', headers=headers, params=payload)

	if not 200 <= response.status_code <= 299:
		print('Error: status code {}'.format(response.status_code))
		print('url: {}'.format(response.url))
		print(response.content)
		raise Exception('Raising error due to invalid status code')

	src_obj= response.json()

	src_list= src_obj['albums']['items']

	matched_album_id=None

	for album in src_list:
		if album['name'].upper()== target_album_name.upper() and any(i['name'].upper()==target_artist.upper() for i in album['artists']):
			matched_album_id= album['id']
			break
	
	return matched_album_id

def add_top_album_tracks_to_playlist(headers, user_id, album_id, playlist_id, num_tracks=3):
	#get all tracks from album and their stats
	response=requests.get('https://api.spotify.com/v1/albums/{}/tracks'.format(album_id), headers=headers)
	if not 200 <= response.status_code <= 299:
		print('Error: status code {}'.format(response.status_code))
		print('url: {}'.format(response.url))
		print(response.content)
		raise Exception('Raising error due to invalid status code')
	
	alb_tracks_obj= response.json()
	track_ids= [i['id'] for i in alb_tracks_obj['items']]
	track_ids= track_ids[:50]
	track_ids= ','.join(track_ids)
	response=requests.get('https://api.spotify.com/v1/tracks', headers=headers, params={'ids':track_ids})
	
	if not 200 <= response.status_code <= 299:
		print('Error: status code {}'.format(response.status_code))
		print('url: {}'.format(response.url))
		print(response.content)
		raise Exception('Raising error due to invalid status code')
	potential_tracks= response.json()
	potential_tracks= potential_tracks['tracks']
	
	#sort by popularity and grab the N most popular ones
	potential_tracks= sorted(potential_tracks, key=lambda track: track['popularity'], reverse=True)
	uris_to_add= [i['uri'] for i in potential_tracks[:num_tracks]]
	uris_to_add= ','.join(uris_to_add)

	#add tracks to playlist
	params= {'uris':uris_to_add}
	response= requests.post('https://api.spotify.com/v1/users/{}/playlists/{}/tracks'.format(user_id, playlist_id), headers=headers, params=params)
	if not 200 <= response.status_code <= 299:
		print('Error: status code {}'.format(response.status_code))
		print('url: {}'.format(response.url))
		print(response.content)
		raise Exception('Raising error due to invalid status code')
	return




