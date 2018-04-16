import requests

API_KEY = '99ccac3e0d7fd2c7a076beea141c1057'
BASE_URL = 'https://api.themoviedb.org/3/movie/{endpoint}?language=en-US&api_key=' + API_KEY
UPCOMING_URL = {'endpoint': 'upcoming', 'params': '&page={page}'}
DETAILS_URL = {'params': '&append_to_response=videos,release_dates'}

class Scraper(object):
    def __init__(self):
        pass

    def apiGet(self, url):
        response = requests.get(url)
        return response.json()

    def getUpcoming(self):
        return self.apiGet(BASE_URL.format(endpoint=UPCOMING_URL['endpoint']) + UPCOMING_URL['params'].format(page=1))

    def getDetails(self, ID):
        return self.apiGet(BASE_URL.format(endpoint=ID) + DETAILS_URL['params'])

    def getTrailers(self):
        data = self.getUpcoming()
        trailers = []
        for trailer in data['results']:
            details = self.getDetails(trailer['id'])
            trailers.append(details)

        return trailers
