"""The main function"""

import os
import logging
import time
import json
from pathlib import Path
import urllib.parse
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from rich.progress import Progress

import application_settings as settings
from models import Movie
from mongodb_engine import collection
from utils import is_mongod_service_up, is_mongod_container_service_up, movie_decoder

semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TASKS)
logger = logging.getLogger(__name__)
logging.basicConfig(filename=settings.LOG_FILE_PATH, level=logging.ERROR)


def format_movie_image_name(movie_title):
    """A dummy method to adapt the movie picture file name."""
    movie_title = movie_title.lower()
    movie_title = movie_title.replace(" ", "_")
    movie_title = movie_title.replace(":", "")
    movie_title = movie_title.replace("!", "")
    movie_title = movie_title.replace("&", "")
    movie_title = movie_title.replace(",", "")
    movie_title = movie_title.replace("+", "")
    return f"{movie_title}.jpg"


async def get_movie_picture(session, movie, movie_image_url, movie_image_name):
    """Download a movie illustration image and save it into a dedicated folder"""
    try:
        async with session.get(
            movie_image_url, headers=settings.QUERY_HEADERS
        ) as response:
            if response.status == 200:
                image_content = await response.read()
                with open(f"{settings.DEFAULT_MOVIES_PICTURES_PATH}/{movie_image_name}", "wb") as file:
                    file.write(image_content)
            else:
                # to resolve W1203: Use lazy % formatting in logging functions
                logging.error("Failed to download image for %s: HTTP %s", movie.title, response.status)
    except Exception as e:
        # to resolve W1203: Use lazy % formatting in logging functions
        logging.error("Error downloading image for %s - %s", movie.title, e)


async def get_movie_details(session, movie, movie_url):
    """
    Get more details from the movie found in IMDb.
    Returns the updated movie instance.
    """
    try:
        search_query = movie_url
        url = f"{settings.ENGINE_URL}{search_query}"
        async with session.get(url, headers=settings.QUERY_HEADERS) as response:
            movie_details = await response.text()
            soup = BeautifulSoup(movie_details, "html.parser")
            movie_rating_block = soup.find("div", class_="sc-eb51e184-0")
            movie_rating = (
                movie_rating_block.find("div", class_="sc-eb51e184-2")
                .getText()
                .split("/")[0]
            )
            movie.rating = float(movie_rating)
            movie_genres = soup.find("div", class_="ipc-chip-list__scroller")
            movie_genres_list = [
                span.get_text(strip=True)
                for span in movie_genres.find_all("span", class_="ipc-chip__text")
            ]
            movie.genres = movie_genres_list
            movie_description = soup.find(
                "span", class_="sc-2d37a7c7-2 ggeRnl"
            ).getText(strip=True)
            movie.description = movie_description
            movie_year_block = soup.find("div", class_="sc-1f50b7c-0")
            movie_year = movie_year_block.find(
                "li", class_="ipc-inline-list__item"
            ).getText()
            movie.year = movie_year

            details_block = soup.find_all("a", class_="ipc-metadata-list-item__list-content-item")

            movie.director = details_block[0].text
            movie.writer = details_block[1].text

            movie_actors_list = []
            actors_list = soup.find("div", class_="ipc-sub-grid ipc-sub-grid--page-span-2 ipc-sub-grid--wraps-at-above-l ipc-shoveler__grid")
            for actor_block in actors_list:
                actor = actor_block.find("a", class_="sc-bfec09a1-1 KeEFX")
                movie_actors_list.append(actor.text)
            movie.actors = movie_actors_list

            various_ul_block = soup.find("ul", class_="ipc-metadata-list ipc-metadata-list--dividers-all ipc-metadata-list--base")
            various_block = various_ul_block.find_all("li", class_="ipc-metadata-list__item")

            countries_list = []
            for country_block in various_block[1]:
                try:
                    countries = country_block.find("ul", {})
                    for countrie in countries:
                        countries_list.append(countrie.text)
                except Exception:
                    countries_list.append(country_block.text)
            countries_list.pop(0)
            movie.countries_of_origin = countries_list

            movie_image_url = soup.find("img", class_="ipc-image").get("src")
            movie.image_name = format_movie_image_name(movie.title)

            trailer_url = soup.find_all("a", class_="ipc-lockup-overlay ipc-focusable")
            movie.trailer_url = f'https://www.imdb.com{trailer_url[1].get("href")}'

            await get_movie_picture(session, movie, movie_image_url, movie.image_name)
            return movie
    except AttributeError as e:
        # to resolve W1203: Use lazy % formatting in logging functions
        logging.error("Error fetching details for %s - %s", movie.title, e)
        return movie


async def search_movie(session, movie, progress, progressbar_task_id):
    """
    The asyncio task which search a movie on IMDb through his title.
    If a movie is found we look for more details and download the illustration picture.
    Then the movie instance is stored in MongoDB, with default values or the IMDb ones.
    Each time a movie is stored we update the rich progress bar.
    """
    async with semaphore:
        encoded_title = urllib.parse.quote(movie.title)
        # &title_type=feature: on ne veut que les films de Cinéma (pas les séries télé)
        search_query = (
            f"title={encoded_title}&genres={movie.genres[0]}&title_type=feature"
        )
        url = f"{settings.SEARCH_ENGINE_URL}{search_query}"
        async with session.get(url, headers=settings.QUERY_HEADERS) as response:
            content = await response.text()
            movie.imdb_match = False
            soup = BeautifulSoup(content, "html.parser")
            movie_wrapper = soup.find_all(
                "a", {"class": "ipc-title-link-wrapper"}, limit=5
            )
            for wrapper in movie_wrapper:
                title_text = wrapper.find("h3", {"class": "ipc-title__text"}).getText()[
                    3:
                ]
                if movie.title == title_text:
                    movie.imdb_match = True
                    href = wrapper.get("href")
                    movie = await get_movie_details(session, movie, href)
            collection.insert_one(movie_decoder(movie))
            progress.advance(progressbar_task_id)


async def search_movies(a_movies_list):
    """The asyncio tasks pool. Foreach movie instance in the movies list we execute a task."""
    async with aiohttp.ClientSession() as session:
        with Progress() as progress:
            progressbar_task_id = progress.add_task(
                "[cyan]Processing movies...", total=len(a_movies_list)
            )
            tasks = []
            for movie in a_movies_list:
                task = asyncio.create_task(
                    search_movie(session, movie, progress, progressbar_task_id)
                )
                tasks.append(task)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    # to resolve W1203: Use lazy % formatting in logging functions
                    logging.error("[search_movies] Exception %s", result)


def create_movies_list():
    """
    Read a JSON file which consist of a list of dictionnaries.
    We instantiate a "Movie" instance from each dictionnary.
    We create a list in which we add all movies instances.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, settings.DUMMY_MOVIES_LIST_FILE_PATH)
    if not json_file_path:
        raise FileNotFoundError(f"{json_file_path} not found")
    with open(json_file_path, "r", encoding="utf-8") as fd:
        dummy_json_movies = json.load(fd)

    a_movies_list = [Movie(**movie) for movie in dummy_json_movies]
    return a_movies_list


if __name__ == "__main__":
    if not is_mongod_service_up() == "active" and not is_mongod_container_service_up():
        raise ConnectionError("[-] Sir, Mongod service is not active")
    movies_list = create_movies_list()
    start_time = time.time()
    asyncio.get_event_loop().run_until_complete(search_movies(movies_list))
    duration = time.time() - start_time
    formated_duration = f"{int(duration//60)} minute(s) {int(duration%60)} seconde(s)"
    print(f"Script ended in {formated_duration}")
    print(f"Movies list has: {len(movies_list)} movies.")
    print(f"We have stored: {collection.count_documents({})} movies.")
    pictures_folder = Path(settings.DEFAULT_MOVIES_PICTURES_PATH)
    total_pictures = sum(1 for _ in pictures_folder.iterdir() if _.is_file())
    print(f"We have downloaded: {total_pictures} movie pictures.")
