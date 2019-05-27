import urllib
import math
import itertools
import json
from ui import utils
from ui.BrowserBase import BrowserBase

class AnimepaheBrowser(BrowserBase):
    _BASE_URL = "https://animepahe.com/api"

    def _parse_anime_view(self, res):
        url = res['id']
        name = "%s Ep. %s"  % (res['anime_title'], res['episode'])
        image = res['snapshot']
        return utils.allocate_item(name, "play/" + str(url), False, image)

    def _parse_search_view(self, res):
        url = res['id']
        name = res['title']
        image = res['image']
        info = "%s - %s" % (res['type'], res['status'])
        return utils.allocate_item(name, "animes/" + str(url), True, image, info)

    def _parse_episode_view(self, res):
        url = res['id']
        name = 'Ep. %s' % res['episode']
        image = res['snapshot']
        return utils.allocate_item(name, "play/" + str(url), False, image)

    def _parse_history_view(self, res):
        name = res
        return utils.allocate_item(name, "search/" + name + "/1", True)

    def _handle_paging(self, total_pages, base_url, page):
        if page == total_pages:
            return []

        next_page = page + 1
        name = "Next Page (%d/%d)" % (next_page, total_pages)
        return [utils.allocate_item(name, base_url % next_page, True, None)]

    def _json_request(self, url, data):
        response = json.loads(self._get_request(url, data))
        return response

    def _process_anime_view(self, url, data, base_plugin_url, page):
        json_resp = self._json_request(url, data)
        results = json_resp["data"]
        total_pages = json_resp["last_page"]
        all_results = map(self._parse_anime_view, results)

        all_results += self._handle_paging(total_pages, base_plugin_url, page)
        return all_results

    def _process_search_view(self, url, data):
        json_resp = self._json_request(url, data)
        results = json_resp["data"]
        all_results = map(self._parse_search_view, results)
        return all_results

    def _process_episode_view(self, url, data, base_plugin_url, page):
        json_resp = self._json_request(url, data)
        results = json_resp["data"]
        total_pages = json_resp["last_page"]
        all_results = map(self._parse_episode_view, results)

        all_results += self._handle_paging(total_pages, base_plugin_url, page)
        return all_results

    def search_site(self, search_string, page=1):
        data = {
            "m": 'search',
            "l": 8,
            "q": search_string,
        }

        url = self._BASE_URL
        return self._process_search_view(url, data)

    def get_anime_id(self, name):
        data = {
            "m": 'search',
            "l": 8,
            "q": name,
        }
        json_resp = self._json_request(self._BASE_URL, data)
        results = json_resp.get("data")
        if not results:
            return []

        anime_id = results[0]['id']
        return self.get_anime_episodes(anime_id)
        

    # TODO: Not sure i want this here..
    def search_history(self,search_array):
    	result = map(self._parse_history_view,search_array)
    	result.insert(0,utils.allocate_item("New Search", "search", True))
    	result.insert(len(result),utils.allocate_item("Clear..", "clear_history", True))
    	return result

    def get_latest(self, page=1):
        data = {
            "m": 'airing',
            "l": 12,
            "page": page,
        }
        url = self._BASE_URL
        return self._process_anime_view(url, data, "latest/%d", page)

    def get_anime_episodes(self, anime_id, page=1):
        data = {
            "m": 'release',
            "id": anime_id,
            "sort": 'episode_desc',
            "page": page,
        }
        url = self._BASE_URL
        return self._process_episode_view(url, data, "animes_page/%s/%%d" % anime_id, page)

    def get_episode_sources(self, ep_id):
        data = {
            "m": 'embed',
            "id": ep_id,
            "p": 'kwik',
        }
        json_resp = self._json_request(self._BASE_URL, data)
        results = json_resp['data'][ep_id]
        sources = {}

        for element in results.iteritems():
            label = element[0]
            url = element[1]['url']
            sources.update({label: url})

        return sources
