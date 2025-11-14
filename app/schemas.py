from typing import Annotated, Optional, List
from annotated_types import Ge, Le
from pydantic import BaseModel, EmailStr, Field, StringConstraints, ConfigDict

NameStr = Annotated[str, StringConstraints(min_length = 1, max_length = 100)]
YearStartedInt = Annotated[int, Ge(1900), Le(2100)]
TitleStr = Annotated[str, StringConstraints(min_length = 1, max_length = 255)]
PagesInt = Annotated[int, Ge(1), Le(10000)]

class AuthorCreate(BaseModel):
    name: NameStr
    email: EmailStr
    year_started: YearStartedInt

class AuthorRead(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    id: int
    name: NameStr
    email: EmailStr
    year_started: YearStartedInt

class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    id: int
    title: TitleStr
    pages: PagesInt
    author_id: int

class BookCreate(BaseModel):
    title: TitleStr
    pages: PagesInt
    author_id: int

class AuthorReadWithBooks(AuthorRead):
    books: List[BookRead] = []

class BookReadWithAuthor(BookRead):
    author: Optional["AuthorRead"] = None