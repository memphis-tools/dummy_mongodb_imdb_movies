"""Some settings for the application"""

MONGODB_CONTAINER_NAME = "dummy_mongodb_movies"
DUMMY_MOVIES_LIST_FILE_PATH = "application_dummy_movies.json"
LOG_FILE_PATH = "/tmp/dummy_app_consumer.log"

MAX_CONCURRENT_TASKS = 10

QUERY_HEADERS = {"Accept-Language": "en-US,en;q=0.9", "User-Agent": "Mozilla/5.0"}
SEARCH_ENGINE_URL = "https://www.imdb.com/search/title/?"
ENGINE_URL = "https://www.imdb.com/"

DEFAULT_MOVIE_PICTURE_PATH = "app/movie_picture/no_image_available.jpg"
DEFAULT_MOVIES_PICTURES_PATH = "app/movies_pictures"
DEFAULT_MOVIE_RATING_IF_MISSING = 0.0
