from typing import TypedDict
from plexapi.video import Movie

class Movie_Data:
    title: str
    id: int
    addedAt: str # ISO 8601 Datetime String

    def __init__(self, movie: Movie):
        self.title = movie.title
        self.id = movie.ratingKey
        self.addedAt = movie.addedAt.isoformat()

    def print_movie_data(self):
        print(f"Title: {self.title} | ID: {self.id} | Added At: {self.addedAt}")

    def to_dict(self, include_added_at: bool = True):
        return {"title": self.title, "id": self.id} if not include_added_at else {"title": self.title, "id": self.id, "addedAt": self.addedAt}

class Movie_Data_From_JSON(TypedDict):
    title: str
    id: int