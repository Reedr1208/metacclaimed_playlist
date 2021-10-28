# Metacclaimed Playlist

This is the first project which offered great value to me in my every day life. I’ve spent many hours bouncing between Metacritic and Spotify looking for new music until I decided to fully automate it.

I built an automation script to scrape album review data from Metacritic and build playlists using the Spotify API from the 2 most popular tracks from each album which scored over some user-defined threshold.

Since Metacritic did not have a publicly available API, I had to scrape HTML data using BeautifulSoup. The script was hosted on PythonAnywhere and ran daily to update the Spotify playlists for This worked perfectly for over a year, but now Metacritic has changed its website format. I plan to revisit this project in the near future to get it running again.

<b>main_build_playlist.py</b>- Main function which orchestrates the whole process

<b>metacritic_scrape.py</b>-

<b>spotify_playlist.py</b>-

<b>meta0.html, meta1.html</b>- Saved Metacritic HTML for reference

<b>recent_albums_Apr_20.csv, recent_albums_May_20.csv</b>- Saved csvs containing results of scraped metacritic data

See full projects on my [personal webpage](https://raymondreed.co/projects/automated-playlist-creation/).
