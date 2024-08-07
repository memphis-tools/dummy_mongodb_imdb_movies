"""Dummy main.py tests"""

import unittest
from unittest.mock import patch, Mock, mock_open
import application_settings as settings
from main import create_movies_list, format_movie_image_name
from models import Movie


class DummyMainTests(unittest.TestCase):
    def test_create_movies_list(self):
        new_movies_list = create_movies_list()
        self.assertEqual(type(new_movies_list), list)

    def test_format_movie_image_name(self):
        dummy_title = "Nothing: Else! Should & Matters, As applepie"
        new_title = format_movie_image_name(dummy_title)
        self.assertEqual(new_title, "nothing_else_should__matters_as_applepie.jpg")

    @patch("builtins.open", new_callable=mock_open)
    def test_files_not_found(self, mock_open):
        mock_open.side_effect = FileNotFoundError(f"{settings.DUMMY_MOVIES_LIST_FILE_PATH} not found")
        with self.assertRaises(FileNotFoundError):
            create_movies_list()


if __name__ == "__main__":
    unittest.main()
