from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, RootModel


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
    access_key: Optional[str] = None

    @property
    def url(self) -> str:
        return f"https://vk.com/video{self.owner_id}_{self.id}"


class Attachment(BaseModel):
    type: Literal["photo", "video", "doc", "link", "poll", "audio", "graffiti"]
    photo: Optional[Photo] = None
    video: Optional[Video] = None
    doc: Optional[Dict[str, Any]] = None
    link: Optional[Dict[str, Any]] = None
    poll: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    graffiti: Optional[Dict[str, Any]] = None


class Post(BaseModel):
    id: int
    owner_id: int
    from_id: int
    date: int
    text: str
    attachments: List[Attachment] = []
    is_pinned: Optional[int] = Field(None)


class WallGetResponse(BaseModel):
    items: List[Post]


class State(RootModel[Dict[str, int]]):
    root: Dict[str, int] = Field(default_factory=dict)
