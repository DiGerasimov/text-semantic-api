import asyncio
from datetime import datetime
from typing import List

import requests
from application.models import ConvertedText, Output
from requests.exceptions import ConnectionError

running_jobs: List[ConvertedText] = []

try:
    from neuron import summarize_with_return
except Exception:  # NOQA
    from time import sleep

    def summarize_with_return(text: str) -> str:
        sleep(1)
        return f'Converted: {text}'


def _convert_text(task: ConvertedText):
    converted_text = summarize_with_return(task.initial_text)

    data = Output(
        task_id=str(task.id),
        initial_text=task.initial_text,
        converted_text=converted_text
    )

    requests.post(task.url_to_send_text, data=data.json())

    return converted_text


def start_text_conversion(task: ConvertedText) -> None:
    try:
        converted_text = _convert_text(task)
        task.converted_text = converted_text
        task.date_of_sending = datetime.utcnow()
        asyncio.run(task.save())
    except ConnectionError:
        pass

    if running_jobs:
        del running_jobs[0]

    if running_jobs:
        start_text_conversion(running_jobs[0])
