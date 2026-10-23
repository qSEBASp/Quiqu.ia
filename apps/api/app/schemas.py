from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ProfileUpdate(BaseModel):
    riot_id: str = Field(min_length=1, max_length=32)
    tag: str = Field(min_length=1, max_length=10)
    region: str = "eu"
    provider: Literal["demo", "henrik"] = "demo"
    henrik_api_key: str | None = None

    @field_validator("riot_id", "tag")
    @classmethod
    def clean(cls, value: str) -> str:
        return value.strip().lstrip("#")
