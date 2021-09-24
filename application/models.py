from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl
from tortoise import fields, models


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    status: Literal["in_progress", "waiting_for_execution"] = "in_progress"
    queue_position: int


class Input(BaseModel):
    text: str
    url_to_send_converted_text: HttpUrl


class Output(BaseModel):
    task_id: str
    initial_text: str
    converted_text: str

    class Config:
        title = "Data to be sent to the specified URL"


class ConvertedText(models.Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    initial_text = fields.TextField()
    converted_text = fields.TextField(null=True)
    url_to_send_text = fields.CharField(1000)

    date_of_receipt = fields.DatetimeField(auto_now_add=True,
                                           description="Время получения задачи")
    date_of_sending = fields.DatetimeField(description="Время отправки задачи")

    class Meta:
        table = "converted_text"
