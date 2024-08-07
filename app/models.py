"""application class models"""

from uuid import uuid4
from datetime import datetime

import application_settings as settings


class Movie:
    """A dummy movie data model Class"""

    def __init__(self, **kw):
        """Constructor for the Movie class"""
        try:
            self.id = str(uuid4())
            self.imdb_match = False
            self.title = str(kw["title"])
            self.year = int(kw.get("year", datetime.utcnow().year))
            self.genres = kw.get("genres", [""])
            self.rating = float(kw.get("rating", settings.DEFAULT_MOVIE_RATING_IF_MISSING))
            self.description = str(kw.get("description", ""))
            self.image_name = settings.DEFAULT_MOVIE_PICTURE_PATH
            self.director = kw.get("director", "")
            self.writer = kw.get("writer", "")
            self.countries_of_origin = kw.get("countries_of_origin", [""])
            self.actors = kw.get("actors", [""])
            self.trailer_url = kw.get("trailer_url", "")
        except KeyError as e:
            raise ValueError(f"Missing required key '{e.args[0]}' in movie data") from e
        except ValueError as e:
            raise ValueError(f"Invalid value type: {e}") from e

        if len(self.title) < 2 or len(self.title) > 125:
            raise ValueError(f"The title {self.title} must be a string from 2 to 125 characters")

        if self.year < 1900 or self.year > 2100:
            raise ValueError("Year must be between 1900 and 2100")

        if not 0.0 <= self.rating <= 10.0:
            raise ValueError("Rating must be between 0.0 and 10.0")

    def __str__(self) -> str:
        """What a print will print by default
        Returns:
            str: the movie title
        """
        return self.title

    def _get_dict(self) -> dict:
        """Get the movie class attributes as a dictionary
        Returns:
            dict: the movie class attributes as a dictionary
        """
        return {
            "title": self.title,
            "imdb_match": self.imdb_match,
            "genres": self.genres,
            "year": self.year,
            "rating": self.rating,
            "description": self.description,
            "image_name": self.image_name,
        }
