from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, RootModel


class PhotoSize(BaseModel):
    type: str
    url: HttpUrl
    width: int
    height: int


class Photo(BaseModel):
    id: int
    owner_id: int
    sizes: list[PhotoSize]

    @property
    def max_size_url(self) -> HttpUrl:
        if not self.sizes:
            raise ValueError("Photo has no sizes")
        return max(self.sizes, key=lambda size: size.width).url


class Video(BaseModel):
    id: int
    owner_id: int
    title: str
    description: str | None = None
    duration: int | None = None
    access_key: str | None = None

    @property
    def url(self) -> str:
        return f"https://vk.com/video{self.owner_id}_{self.id}"


class Attachment(BaseModel):
    type: Literal["photo", "video", "doc", "link", "poll", "audio", "graffiti"]
    photo: Photo | None = None
    video: Video | None = None
    doc: dict[str, Any] | None = None
    link: dict[str, Any] | None = None
    poll: dict[str, Any] | None = None
    audio: dict[str, Any] | None = None
    graffiti: dict[str, Any] | None = None


class Post(BaseModel):
    id: int
    owner_id: int
    from_id: int
    date: int
    text: str
    attachments: list[Attachment] = []
    is_pinned: int | None = Field(None)


class WallGetResponse(BaseModel):
    items: list[Post]


class State(RootModel[dict[str, int]]):
    root: dict[str, int] = Field(default_factory=dict)
