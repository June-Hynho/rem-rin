from rem_rin.utils import parse_episode_list
from rem_rin.downloader import download_episode

#PARTIALLY_AI_GENERATED

# -----------------------
# COMMAND HANDLERS
# -----------------------
async def handle_search(client, query: str):
    result = await client.search(query)
    for anime in result:
        print(f"{anime['title']} | {anime['type']} | {anime['duration']} | {anime['id']}")


async def handle_download_id(client, args):
    """
    await client.download_by_id(
        args.value,
        episodes=args.episodes,
        no_confirm=args.no_confirm,
        dub=args.dub,
        quality=args.quality,
        destination=args.destination,
    )
    """
    anime = await client.get_anime(args.value)
    episodes = await client.get_episodes(anime)
    if args.dub:
        lang = 'dub'
    else:
        lang = 'sub'
    if args.episodes:
        episode_set = set(parse_episode_list(args.episodes, len(episodes)))
    for i, episode in episodes.items():
        if i not in episode_set:
            continue
        manifest = await client.get_stream(episode, lang)
        print(f"Downloading episode {i}: {episode['title']}...")
        path = await download_episode(client.session, args.destination, manifest, anime, episode, lang, args.quality)
        print(f"Saved in {path}")

async def handle_download_search(client, args):
    anime_id = await client.resolve_query(args.query)

    await client.download_by_id(
        anime_id,
        episodes=args.episodes,
        no_confirm=args.no_confirm,
        dub=args.dub,
        quality=args.quality,
        destination=args.destination,
    )


async def handle_info_id(client, value: int):
    result = await client.info_by_id(value)
    print(result)


async def handle_info_search(client, query: str):
    anime_id = await client.resolve_query(query)
    result = await client.info_by_id(anime_id)
    print(result)


async def handle_eps_id(client, args):
    result = await client.list_episodes_by_id(
        args.value,
        limit=args.limit,
        reverse=args.reverse,
    )
    print(result)


async def handle_eps_search(client, args):
    anime_id = await client.resolve_query(args.query)

    result = await client.list_episodes_by_id(
        anime_id,
        limit=args.limit,
        reverse=args.reverse,
    )
    print(result)


