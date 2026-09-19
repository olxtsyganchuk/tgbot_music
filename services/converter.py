import re
import urllib.parse
import aiohttp
from bs4 import BeautifulSoup


def clean_text(text: str) -> str:
    """Видаляє невидимі юнікод-символи (LTR, RTL, ZWSP) та зайві пробіли."""
    if not text:
        return ""
    # Видаляємо \u200e, \u200f, \u200b-\u200d, нерозривні пробіли \xa0
    cleaned = re.sub(r'[\u200e\u200f\u200b\u200c\u200d\ufeff\xa0]', ' ', text)
    return re.sub(r'\s+', ' ', cleaned).strip()


def clean_youtube_title(title: str, author: str) -> str:
    """Очищає назву відео на YouTube від сміття та Topic-каналів."""
    # Прибираємо суфікс ' - Topic' або ' Topic'
    author = re.sub(r'\s*-\s*Topic$', '', author, flags=re.IGNORECASE).strip()

    # Прибираємо службові мітки з назви відео: (Official Video), [Audio], (Lyrics), (Remastered) тощо
    cleaned_title = re.sub(
        r'(?i)\s*[\(\[](?:official\s*(?:music\s*)?video|official\s*audio|lyrics?|audio|visualizer|hd|4k|\d+k\s*remaster(?:ed)?|remaster(?:ed)?)[\)\]]',
        '',
        title
    ).strip()

    # Якщо автор уже згадується на початку назви (наприклад: "Queen - Bohemian Rhapsody")
    if author and author.lower() in cleaned_title.lower():
        return clean_text(cleaned_title)

    return clean_text(f"{author} {cleaned_title}")


async def extract_title(url: str) -> str:
    """Витягує чисту назву треку та виконавця з посилання."""
    # Для отримання повних метаданих (OpenGraph) від Spotify та Apple Music використовуємо User-Agent бота
    headers = {
        "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # --- 1. SPOTIFY ---
        if "spotify.com" in url:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Отримуємо назву треку з og:title
                    og_title = soup.find('meta', property='og:title')
                    track_name = og_title['content'] if og_title and og_title.get('content') else ""

                    # Виконавець зазвичай міститься в og:description: "Artist · Album · Song · Year"
                    og_desc = soup.find('meta', property='og:description')
                    artist_name = ""
                    if og_desc and og_desc.get('content'):
                        parts = [p.strip() for p in og_desc['content'].split('·')]
                        for part in parts:
                            if part.lower() not in ["song", "пісня", "single", "track", "album", "альбом", "ep"]:
                                artist_name = part
                                break

                    title_tag = soup.title.string if soup.title else ""
                    title_clean = clean_text(title_tag)

                    if track_name and artist_name:
                        return clean_text(f"{artist_name} {track_name}")
                    elif " - song and lyrics by " in title_clean:
                        m = re.match(r'^(.*?)\s*-\s*song and lyrics by\s*(.*?)\s*\|\s*Spotify', title_clean, flags=re.IGNORECASE)
                        if m:
                            return clean_text(f"{m.group(2)} {m.group(1)}")
                    elif " - song by " in title_clean:
                        m = re.match(r'^(.*?)\s*-\s*song by\s*(.*?)\s*\|\s*Spotify', title_clean, flags=re.IGNORECASE)
                        if m:
                            return clean_text(f"{m.group(2)} {m.group(1)}")
                    elif track_name:
                        return clean_text(track_name)

            # Резервний варіант через oEmbed
            oembed_url = f"https://open.spotify.com/oembed?url={url}"
            async with session.get(oembed_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return clean_text(data.get('title', ''))

        # --- 2. YOUTUBE / YOUTUBE MUSIC ---
        elif "youtube.com" in url or "youtu.be" in url:
            oembed_url = f"https://www.youtube.com/oembed?url={url}"
            async with session.get(oembed_url) as response:
                if response.status == 200:
                    data = await response.json()
                    author = data.get('author_name', '')
                    title = data.get('title', '')
                    return clean_youtube_title(title, author)

        # --- 3. APPLE MUSIC ТА ІНШІ ---
        elif "apple.com" in url:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # В Apple Music найзручніший тег — og:title ("Song Name by Artist on Apple Music")
                    og_title = soup.find('meta', property='og:title')
                    if og_title and og_title.get('content'):
                        title_content = og_title['content']
                        title_content = re.sub(r'\s+on Apple\s*Music.*$', '', title_content, flags=re.IGNORECASE)
                        title_content = re.sub(r'\s+в Apple\s*Music.*$', '', title_content, flags=re.IGNORECASE)
                        if " by " in title_content:
                            song, artist = title_content.split(" by ", 1)
                            return clean_text(f"{artist} {song}")
                        return clean_text(title_content)

                    # Резервний парсинг з <title>
                    raw_title = soup.title.string if soup.title else ""
                    raw_title = clean_text(raw_title)
                    raw_title = re.sub(r'\s*-\s*Apple\s*Music.*$', '', raw_title, flags=re.IGNORECASE)
                    raw_title = re.sub(r'\s*-\s*(?:Song with Lyrics by|Song by|Пісня).*?by\s*', ' ', raw_title, flags=re.IGNORECASE)
                    return clean_text(raw_title)

    return ""


async def convert_link(url: str, target: str) -> str:
    query = await extract_title(url)

    if not query:
        return "Не вдалося розпізнати трек за цим посиланням 😔"

    print(f"🎵 Визначено трек для пошуку: '{query}'")

    # Безпечне кодування параметрів запиту (URL encoding)
    encoded_query = urllib.parse.quote_plus(query)

    if target == "youtubeMusic":
        return f"https://music.youtube.com/search?q={encoded_query}"

    elif target == "spotify":
        return f"https://open.spotify.com/search/{encoded_query}"

    elif target == "appleMusic":
        return f"https://music.apple.com/ua/search?term={encoded_query}"

    return "Ця платформа поки що не підтримується."