import regex
import lxml.html as htmlparser
import asyncio
import json

from rem_rin.config import KAIDO

class KaidoClient:
    def __init__(self, session, cache = None):
        self.session = session
        self.cache = cache

    async def search(self, query: str) -> dict:
        url = f"{KAIDO}/search?keyword={query}"
        animes = []
        async with self.session.get(url) as resp:
            html = await resp.text()
        for details in htmlparser.fromstring(html).cssselect('.film_list-wrap')[0].cssselect('.film-detail'):
            dyn_name = details.cssselect(".dynamic-name")[0]
            infor = details.cssselect(".fd-infor")[0]
            matches = regex.findall(r"(\d+)[^a-zA-Z-]", dyn_name.get('href'))
            slug = matches[-1]
            animes.append({
                'safe-title' : dyn_name.get('href').split(slug)[0].replace('/', '')[:-1],
                'id' : slug,
                'title' : dyn_name.get('title'),
                'type' : infor.cssselect('.fdi-item:not(.fdi-duration)')[0].text,
                'duration' : infor.cssselect('.fdi-duration')[0].text
            })
        return animes

    async def get_anime(self, aid):
        url = f"{KAIDO}/ajax/movie/qtip/{aid}"
        async with self.session.get(url) as resp:
            html = await resp.text()
        airing = 'Currently Airing' in html
        html = htmlparser.fromstring(html)
        safe_title = html.cssselect('.pre-qtip-button')[0].cssselect('a')[0].get('href').split(str(aid))[0].split('/')[-1][:-1]
        title = html.cssselect('.pre-qtip-title')[0].text
        type_ = html.cssselect('.ml-2')[0].text
        jptitle = None
        for elem in html.cssselect('.pre-qtip-line'):
            if "Japanese" in elem.cssselect('.stick')[0].text:
                jptitle = elem.cssselect('.stick-text')[0].text
                break
        return {
            "safe-title" : safe_title,
            "id" : aid,
            "type" : type_,
            "title" : title,
            "jptitle" : jptitle if jptitle else None,
            "airing" : airing
        }

    async def get_server_data(self, episodes):
        async def fetch(eid):
            async with self.session.get(f"{KAIDO}/ajax/episode/servers?episodeId={eid}") as r:
                return await r.text()
        return await asyncio.gather(*(fetch(eid) for eid in episodes))

    async def get_episodes(self, anime):
        aid = anime['id']
        url = f"{KAIDO}/ajax/episode/list/{aid}"
        async with self.session.get(url) as resp:
            data = await resp.text()
        data = json.loads(data)
        html = htmlparser.fromstring(data['html'])
        ep_tags = html.cssselect(".ep-item")
        episodes = {}
        eids = []
        ep_nums = []
        for e in ep_tags:
            title = e.get('title')
            eid = e.get('data-id')
            ep_number = int(e.get('data-number'))
            episodes[ep_number] = { 'title' : title, 'number' : ep_number , 'eid' : eid}
            eids.append(eid)
            ep_nums.append(ep_number)
        datas = await self.get_server_data(eids)
        for i in range(len(datas)):
            seid = {}
            data = json.loads(datas[i])
            soup = htmlparser.fromstring(data['html'])
            for item in soup.cssselect(".server-item"):
                if item.get('data-server-id') == "4":
                    seid[item.get('data-type')] = item.get('data-id')
            episodes[ep_nums[i]]['seid'] = seid
        return episodes

    async def get_stream(self, episode, lang):
        url = f"{KAIDO}/ajax/episode/sources?id={episode['seid'][lang]}"
        async with self.session.get(url) as resp:
            data = await resp.text()
            data = json.loads(data)
        param = regex.findall(r'\/([a-zA-Z\d]+)', data["link"])[-1]
        url = f"https://rapid-cloud.co/embed-2/v2/e-1/getSources?id={param}"
        async with self.session.get(url) as resp:
            return json.loads(await resp.text())
