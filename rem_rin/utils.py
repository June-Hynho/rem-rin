from rapidfuzz import process, fuzz
from tenacity import retry, wait_fixed

import asyncio

from rem_rin.config import HEADERS

#AI_GENERATED_START
def resolve_query(query: str, items: list[dict]) -> dict:
    best = process.extractOne(
        query,
        items,
        scorer=fuzz.token_set_ratio,
        processor=lambda x: x["title"]
    )

    # best = (item, score, index)
    item, score, _ = best
    return item
#AI_GENERATED_END

@retry(wait = wait_fixed(1))
async def download_segment(session, url, semaphore, queue = None):
    async with semaphore:
        async with session.get(url, headers = HEADERS) as resp:
            if resp.status != 200:
                raise Exception
            data = await asyncio.wait_for(resp.read(), timeout=20)
            l = int(resp.headers.get('content-length', f'{len(data)}'))
            if l != len(data):
                raise Exception
    if queue:
        await queue.put(1)
    return data

@retry(wait = wait_fixed(1))
async def get_m3u8_text(session, url):
    async with session.get(url, headers = HEADERS) as resp:
        return await resp.text()

@retry(wait = wait_fixed(1))
async def get_track(session, url):
    async with session.get(url) as resp:
        return await resp.read()



#AI_GENERATED_START
def resolve_quality(m3u8_obj, quality):
    """
    Select playlist based on requested vertical resolution (e.g. 720, 1080).
    """
    playlists = []
    for pl in m3u8_obj.playlists:
        if pl.stream_info.resolution:
            _, h = pl.stream_info.resolution
            playlists.append((h, pl))
    if not playlists:
        return m3u8_obj.playlists[0]
    # sort by resolution ascending
    playlists.sort(key=lambda x: x[0])
    # 1. exact match
    for h, pl in playlists:
        if h == quality:
            return pl
    # 2. highest <= quality
    candidates = [pl for h, pl in playlists if h <= quality]
    if candidates:
        return candidates[-1]  # highest <= quality
    # 3. fallback → highest available
    return playlists[-1][1]
#AI_GENERATED_END


async def not_progress_bar(queue, total):
    completed = 0
    while completed < total:
        await queue.get()
        completed += 1
        print(f"\r[{completed}/{total}] ({100*completed/total:.2f}%)", end="", flush=True)
    print()

def get_lang_code(label):
    l = label.lower()
    key = ['eng', 'fre', 'spa', 'ita', 'ger', 'rus', 'dut', 'por']
    for k in key:
        if k in l:
            return k
    return 'und'

def get_chapters(data, duration, time_base):
    intro = data['intro']
    outro = data['outro']
    if outro['end'] == 0:
        outro['start'] = duration
        outro['end'] = duration
    pairs = [[pair[0] / time_base, pair[1] / time_base] for pair in [
        [0, intro['start']],
        [intro['start'], intro['end']],
        [intro['end'], outro['start']],
        [outro['start'], outro['end']],
        [intro['end'], duration]
    ]]
    titles = ["Pre-Intro", "Intro", "Content", "Outro", "Post-Outro"]
    chapters = []
    counter = 0
    for i, p in enumerate(pairs):
        if p[0] == p[1]:
            continue
        chapters.append({
            "id" : counter,
            "start" : int(p[0]),
            "end" : int(p[1]),
            "time_base" : time_base,
            "metadata" : {"title" : titles[i]}
        })
        counter += 1
    return chapters

def parse_episode_list(string, last):
    string = string.replace("l", str(last)).replace(" ", "")
    final = []
    for tok in string.split(','):
        if '-' in tok:
            a, b = tok.split('-')
            final.extend(range(int(a), int(b) + 1))
            continue
        final.append(int(tok))
    return sorted(list(set(final)))

