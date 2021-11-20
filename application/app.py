from datetime import datetime
from http import HTTPStatus
from os import getenv

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response
from tortoise.contrib.fastapi import register_tortoise

from application.models import ConvertedText, Input, Output, Task
from application.services.report import generate_report_content, generate_report_file_name
from application.services.text_converter import running_jobs, start_text_conversion


app = FastAPI(title="TextSemantic API")


@app.post("/convert_text/",
          status_code=HTTPStatus.ACCEPTED,
          response_model=Task)
def create_convert_text_task(input_data: Input, background_tasks: BackgroundTasks):
    if len(input_data.text) <= 80:
        raise HTTPException(406, detail="Input text too small (<= 80)")

    new_task = ConvertedText(
        initial_text=input_data.text,
        date_of_receipt=datetime.utcnow(),
        url_to_send_text=input_data.url_to_send_converted_text
    )

    running_jobs.append(new_task)
    if len(running_jobs) == 1:
        background_tasks.add_task(start_text_conversion, new_task)

    return Task(
        id=new_task.id,
        status="in_progress" if len(running_jobs) == 1 else "waiting_for_execution",
        queue_position=len(running_jobs) - 1
    )


@app.get("/report")
async def get_report(offset: int = 0, limit: int = 1000):
    return Response(
        content=await generate_report_content(offset=offset, limit=limit),
        headers={
            'content-disposition':
                'attachment; '
                f'filename={generate_report_file_name()}',
        },
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.post("/receive_data", include_in_schema=False)
def receive_data(data: Output):
    print(f"{data = }")


@app.on_event("startup")
def startup_event():
    load_dotenv()

    raw_white_list = getenv('ALLOWED_HOSTS', '127.0.0.1')
    white_list = raw_white_list.strip().split(',')

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=white_list
    )

    register_tortoise(
        app=app,
        db_url=getenv('DB_URL'),
        modules={"models": ["application.models"]},
        generate_schemas=True,
        add_exception_handlers=False,
    )


@app.on_event("shutdown")
def on_shutdown():
    pass
