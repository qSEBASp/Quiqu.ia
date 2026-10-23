from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ProfileUpdate(BaseModel):
    riot_id: str = Field(min_length=1, max_length=32)
    tag: str = Field(min_length=1, max_length=10)
    region: str = "eu"
    provider: Literal["demo", "henrik"] = "demo"
    henrik_api_key: str | None = Field(default=None, max_length=256)

    @field_validator("riot_id", "tag")
    @classmethod
    def clean(cls, value: str) -> str:
        return value.strip().lstrip("#")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    detail: str = Field(default="", max_length=2000)
    rule_id: str | None = Field(default=None, max_length=64)
    target: str = Field(default="", max_length=160)


class GoalUpdate(BaseModel):
    status: Literal["active", "done"] | None = None
