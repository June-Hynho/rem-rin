from pathlib import Path
import m3u8
from io import BytesIO
import asyncio

from rem_rin.utils import download_segment, get_m3u8_text, not_progress_bar, get_track, resolve_quality
from rem_rin.avmux import mux_to_mkv

async def download_episode(session, base, manifest, anime, episode, lang, quality = 1080, max_concurrent_segments = 48, force = False):
    folder = Path(base) / Path(anime['safe-title'])
    folder.mkdir(exist_ok = True)

    m3u8_obj = m3u8.loads(await get_m3u8_text(session, manifest['sources'][0]['file']), manifest['sources'][0]['file'])
    playlist = resolve_quality(m3u8_obj, quality)
    _, quality = playlist.stream_info.resolution

    filename = folder / Path(f"{episode['number']}-{lang}-{quality}p")
    if filename.with_suffix('.mkv').exists() and not force:
        print(f"{filename} exists, skipping...")
        return filename.with_suffix('.mkv')
    if force:
        filename.with_suffix('.mkv').unlink(missing_ok = True)

    m3u8_obj = m3u8.loads(await get_m3u8_text(session, playlist.absolute_uri), playlist.absolute_uri)
    segments_uri = [s.absolute_uri for s in m3u8_obj.segments]
    semaphore = asyncio.Semaphore(max_concurrent_segments)

    queue = asyncio.Queue()
    tasks = [download_segment(session, s, semaphore, queue) for s in segments_uri]
    progress_task = asyncio.create_task(not_progress_bar(queue, len(segments_uri)))
    segments = await asyncio.gather(*tasks)

    await progress_task

    manifest['sources'][0]['handler'] = BytesIO(b"".join(segments))

    for i, track in enumerate(manifest['tracks']):
        track['label'] += str(i)# prevent duplicate language labels

    async def fetch(track):
        track['handler'] = BytesIO(await get_track(session, track['file']))

    await asyncio.gather(*[fetch(track) for track in manifest['tracks']])

    manifest['sources'][0]['label'] = episode['title']
    
    return mux_to_mkv(manifest, filename)
