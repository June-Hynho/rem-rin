import av
from av.stream import Disposition
import heapq
from fractions import Fraction

from rem_rin.utils import get_lang_code, get_chapters

#AI_GENERATED_START
def interleaved_mux(containers, stream_map, output_container, duration_stream_key = (0, 0)):
    def pkt_time(pkt):
        # prefer DTS for muxing stability
        if pkt.dts is not None:
            return pkt.dts * pkt.stream.time_base
        return float("inf")


    iters = [c.demux() for c in containers]
    heap = []

    # --- seed heap ---
    for ci, it in enumerate(iters):
        try:
            pkt = next(it)
            while pkt.dts is None:
                pkt = next(it)
            heapq.heappush(heap, (pkt_time(pkt), ci, pkt))
        except StopIteration:
            pass

    last_pts = 0
    # --- main loop ---
    while heap:
        _, ci, pkt = heapq.heappop(heap)

        key = (ci, pkt.stream.index)
        out_stream = stream_map.get(key)

        if key == duration_stream_key:
            last_pts = max(last_pts, pkt.pts)

        pkt.stream = out_stream
        output_container.mux(pkt)

        # push next packet from same container
        try:
            nxt = next(iters[ci])
            while nxt.dts is None:
                nxt = next(iters[ci])
            heapq.heappush(heap, (pkt_time(nxt), ci, nxt))
        except StopIteration:
            pass
    return last_pts
#AI_GENERATED_END


def mux_to_mkv(data, file):
    file = file.with_suffix('.mkv')
    output_container = av.open(file, 'w')
    output_container.metadata["title"] = data['sources'][0]['label'] + " | Rem-rin scraper"
    stream_map = {}

    containers = []

    containers.append(av.open(data['sources'][0]['handler']))
    for stream in containers[0].streams:
        if stream.type in ("audio", "video"):
            stream_map[(0, stream.index)] = output_container.add_stream_from_template(stream)

    video_stream_key = (0, 0)

    for track in data['tracks']:
        if track['kind'] == 'captions':
            containers.append(av.open(track['handler']))
            ci = len(containers) - 1
            stream = containers[-1].streams.subtitles[0]
            out_stream = output_container.add_stream_from_template(stream)
            out_stream.metadata['language'] = get_lang_code(track['label'])
            out_stream.metadata['title'] = track['label']
            if track.get('default', False):
                out_stream.disposition = Disposition.default.value
            stream_map[(ci, stream.index)] = out_stream

    duration = interleaved_mux(containers, stream_map, output_container, video_stream_key) * stream_map[video_stream_key].time_base
    time_base = Fraction(1, 1_000_000)
    output_container.set_chapters(get_chapters(data, duration, time_base))

    for container in containers:
        container.close()
    output_container.close()
    return file
