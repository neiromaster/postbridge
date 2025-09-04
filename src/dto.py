from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class PhotoSize(BaseModel):
    type: str
    url: HttpUrl
    width: int
    height: int


class Photo(BaseModel):
    id: int
    owner_id: int
    sizes: List[PhotoSize]

    @property
    def max_size_url(self) -> HttpUrl:
        if not self.sizes:
            raise ValueError("Photo has no sizes")
        return max(self.sizes, key=lambda size: size.width).url


class Video(BaseModel):
    id: int
    owner_id: int
    title: str
    description: Optional[str] = None
    duration: Optional[int] = None

    @property
    def url(self) -> str:
        return f"https://vk.com/video{self.owner_id}_{self.id}"


class Attachment(BaseModel):
    type: Literal["photo", "video", "doc", "link", "poll", "audio", "graffiti"]
    photo: Optional[Photo] = None
    video: Optional[Video] = None


class Post(BaseModel):
    id: int
    owner_id: int
    from_id: int
    date: int
    text: str
    attachments: List[Attachment] = []
    is_pinned: Optional[int] = Field(None)
