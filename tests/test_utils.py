"""Dummy utils.py tests"""

import unittest
from unittest.mock import patch, Mock
import docker
from docker.errors import NotFound, APIError
import utils


class DummyMainTests(unittest.TestCase):
    def test_is_mongod_service_up(self):
        service_state = utils.is_mongod_service_up()
        self.assertIn(service_state, {"active", "inactive"})

    @patch("docker.from_env")
    def test_container_running_and_listening(self, mock_from_env):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = "running"
        mock_container.attrs = {
            "NetworkSettings": {
                "Ports": {
                    "27017/tcp": [{}],
                }
            }
        }
        mock_client.containers.get.return_value = mock_container
        mock_from_env.return_value = mock_client
        self.assertTrue(utils.is_mongod_container_service_up())

    @patch("docker.from_env")
    def test_container_running_not_listening(self, mock_from_env):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = "running"
        mock_container.attrs = {
            "NetworkSettings": {
                "Ports": {}
            }
        }
        mock_client.containers.get.return_value = mock_container
        mock_from_env.return_value = mock_client
        with self.assertRaises(RuntimeError):
            utils.is_mongod_container_service_up()

    @patch("docker.from_env")
    def test_container_not_running(self, mock_from_env):
         mock_client = Mock()
         mock_container = Mock()
         mock_container.status = "exited"
         mock_client.containers.get.return_value = mock_container
         mock_from_env.return_value = mock_client
         with self.assertRaises(RuntimeError):
             utils.is_mongod_container_service_up()

    @patch("docker.from_env")
    def test_container_not_found(self, mock_from_env):
        mock_client = Mock()
        mock_client.containers.get.side_effect = NotFound("container not found")
        mock_from_env.return_value = mock_client
        with self.assertRaises(NotFound):
            utils.is_mongod_container_service_up()

    @patch("docker.from_env")
    def test_docker_api_error(self, mock_from_env):
        mock_client = Mock()
        mock_client.containers.get.side_effect = APIError("API error")
        mock_from_env.return_value = mock_client
        with self.assertRaises(APIError):
            utils.is_mongod_container_service_up()


if __name__ == "__main__":
    unittest.main()
