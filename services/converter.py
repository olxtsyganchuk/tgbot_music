import aiohttp
from bs4 import BeautifulSoup


async def extract_title(url: str) -> str:
    """Витягує назву треку через офіційні віджети oEmbed або класичний парсинг."""
    async with aiohttp.ClientSession() as session:
        # Для Spotify
        if "spotify.com" in url:
            oembed_url = f"https://open.spotify.com/oembed?url={url}"
            async with session.get(oembed_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return f"{data.get('author_name', '')} {data.get('title', '')}".strip()

        # Для YouTube Music / YouTube
        elif "youtube.com" in url or "youtu.be" in url:
            oembed_url = f"https://www.youtube.com/oembed?url={url}"
            async with session.get(oembed_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return f"{data.get('author_name', '')} {data.get('title', '')}".strip()

        # Для Apple Music та інших
        else:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with session.get(url, headers=headers) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                title = soup.title.string if soup.title else ""
                return title.split('|')[0].replace("on Apple Music", "").strip()

    return ""


async def convert_link(url: str, target: str) -> str:
    query = await extract_title(url)

    if not query:
        return "Не вдалося розпізнати трек за цим посиланням 😔"

    print(f"🎵 Визначено трек: {query}")

    # Генеруємо надійні посилання на сторінки пошуку для всіх платформ
    if target == "youtubeMusic":
        return f"https://music.youtube.com/search?q={query.replace(' ', '+')}"

    elif target == "spotify":
        return f"https://open.spotify.com/search/{query.replace(' ', '%20')}"

    elif target == "appleMusic":
        return f"https://music.apple.com/ua/search?term={query.replace(' ', '%20')}"

    return "Ця платформа поки що не підтримується."