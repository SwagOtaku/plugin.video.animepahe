import itertools
import requests
import json
import time
import datetime
import ast
from ui import utils

class AniListBrowser():
    _URL = "https://graphql.anilist.co"

    def _handle_paging(self, hasNextPage, base_url, page):
        if not hasNextPage:
            return []

        next_page = page + 1
        name = "Next Page (%d)" %(next_page)
        return [utils.allocate_item(name, base_url % next_page, True, None)]
    
    def get_popular(self, page=1):
        jikan = (requests.get('https://api.jikan.moe/v3/season')).json()
        season = jikan['season_name'].upper()
        year = jikan['season_year']

        query = '''
        query (
            $page: Int = 1,
            $type: MediaType,
            $isAdult: Boolean = false,
            $season: MediaSeason,
            $year: String,
            $sort: [MediaSort] = [SCORE_DESC, POPULARITY_DESC]
        ) {
            Page (page: $page, perPage: 20) {
                pageInfo {
                    hasNextPage
                }
                ANIME: media (
                    type: $type,
                    season: $season,
                    startDate_like: $year,
                    sort: $sort,
                    isAdult: $isAdult
                ) {
                    id
                    title {
                        userPreferred
                    }
                    coverImage {
                        extraLarge
                    }
                    description
                }
            }
        }
        '''

        variables = {
            'page': page,
            'type': "ANIME",
            'season': season,
            'year': str(year) + '%',
            'sort': "POPULARITY_DESC"
            }


        return self._process_anichart_view(query, variables, "anichart_popular/%d", page)

    def _process_anichart_view(self, query, variables, base_plugin_url, page):
        result = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = result.json()

        if results.has_key("errors"):
            return

        json_res = results['data']['Page']
        hasNextPage = json_res['pageInfo']['hasNextPage']

        all_results = map(self._base_anichart_view, json_res['ANIME'])
        all_results = list(itertools.chain(*all_results))

        all_results += self._handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    def _base_anichart_view(self, res):
        base = {
            "name": res['title']['userPreferred'],
            "url": "watchlist_query/%s" % (res['title']['userPreferred']),
            "image": res['coverImage']['extraLarge'],
            "plot": res['description'],
        }

        return self._parse_view(base)

    def _parse_view(self, base):
        return [
            utils.allocate_item("%s" % base["name"],
                                base["url"],
                                True,
                                base["image"],
                                base["plot"])
            ]

    def get_genres(self, genre_dialog):
        query = '''
        query {
            genres: GenreCollection,
            tags: MediaTagCollection {
                name
                isAdult
            }
        }
        '''

        result = requests.post(self._URL, json={'query': query})
        results = result.json()['data']
        genres_list = results['genres']

        del genres_list[6]

        tags_list = []
        tags = filter(lambda x: x['isAdult'] == False, results['tags'])
        for tag in tags:
            tags_list.append(tag['name'])

        genre_display_list = genres_list + tags_list
        return self._select_genres(genre_dialog, genre_display_list)

    def _select_genres(self, genre_dialog, genre_display_list):
        multiselect = genre_dialog(genre_display_list)

        if not multiselect:
            return []

        genre_list = []
        tag_list = []

        for selection in multiselect:
            if selection <= 17:
                genre_list.append(genre_display_list[selection])
                continue

            tag_list.append(genre_display_list[selection])

        return self._genres_payload(genre_list, tag_list)

    def _genres_payload (self, genre_list, tag_list, page=1):
        query = '''
        query (
            $page: Int,
            $type: MediaType,
            $isAdult: Boolean = false,
            $includedGenres: [String],
            $includedTags: [String],
            $sort: [MediaSort] = [SCORE_DESC, POPULARITY_DESC]
        ) {
            Page (page: $page, perPage: 20) {
                pageInfo {
                    hasNextPage
                }
                ANIME: media (
                    type: $type,
                    genre_in: $includedGenres,
                    tag_in: $includedTags,
                    sort: $sort,
                    isAdult: $isAdult
                ) {
                    id
                    title {
                        userPreferred
                    }
                    coverImage {
                        extraLarge
                    }
                    description
                    status
                    genres
                    isAdult
                    }
                }
            }
        '''

        variables = {
            'page': page,
            'type': "ANIME"
            }

        if genre_list:
            variables["includedGenres"] = genre_list

        if tag_list:
            variables["includedTags"] = tag_list

        return self._process_genre_view(query, variables, "anilist_genres/%s/%s/%%d" %(genre_list, tag_list), page)

    def _process_genre_view(self, query, variables, base_plugin_url, page):
        result = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = result.json()

        if results.has_key("errors"):
            return

        anime_res = results['data']['Page']['ANIME']
        hasNextPage = results['data']['Page']['pageInfo']['hasNextPage']

        all_results = map(self._base_genre_view, anime_res)
        all_results = list(itertools.chain(*all_results))

        all_results += self._handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    def _base_genre_view(self, res):
        base = {
            "name": res['title']['userPreferred'],
            "url": "watchlist_query/%s" % (res['title']['userPreferred']),
            "image": res['coverImage']['extraLarge'],
            "plot": res['description'],
        }

        return self._parse_view(base)

    def get_genres_page(self, genre_string, tag_string, page):
        return self._genres_payload(ast.literal_eval(genre_string), ast.literal_eval(tag_string), page)
