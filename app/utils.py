"""Some shared functions"""

import os
import subprocess
import docker
from docker.errors import NotFound, APIError

from application_settings import MONGODB_CONTAINER_NAME


def is_mongod_service_up():
    """Check if a systemd MongoDB service is up."""
    result = subprocess.run(
        ["systemctl", "is-active", "mongod.service"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def is_mongod_container_service_up():
    """Check if a MongoDB's container is up."""
    try:
        # Set Docker host explicitly
        os.environ["DOCKER_HOST"] = (
            "unix://var/run/docker.sock"  # Adjust path if necessary
        )

        # Create Docker client
        client = docker.from_env()
        container = client.containers.get(MONGODB_CONTAINER_NAME)

        if container:
            container.reload()
            if container.status == "running":
                ports = container.attrs["NetworkSettings"]["Ports"]
                if "27017/tcp" in ports and ports["27017/tcp"]:
                    return True
                raise RuntimeError(
                    "MongoDB container is running but not listening on port 27017"
                )
            raise RuntimeError("MongoDB container is not running")

        raise RuntimeError("MongoDB container not found")
    except NotFound as e:
        raise NotFound(f"Error: MongoDB container is not running: {e}") from e
    except APIError as e:
        raise APIError(f"Error: Docker API error - {e}") from e


def movie_decoder(movie) -> dict:
    """Converts a Movie object to a dictionary."""
    return {
        "_id": str(movie.id),
        "title": movie.title,
        "imdb_match": movie.imdb_match,
        "genres": movie.genres,
        "rating": movie.rating,
        "year": movie.year,
        "description": movie.description,
        "image_name": movie.image_name,
        "director": movie.director,
        "writer": movie.writer,
        "actors": movie.actors,
        "countries_of_origin": movie.countries_of_origin,
        "trailer_url": movie.trailer_url,
    }
