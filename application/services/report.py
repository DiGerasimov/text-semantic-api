from datetime import datetime
from typing import Optional

from models import ConvertedText
from xlwt import Workbook, Worksheet
from xlwt.CompoundDoc import XlsDoc

REPORT_TIME_FORMAT = '%m/%d/%Y, %H:%M:%S'
REPORT_FILE_TIME_FORMAT = '%m-%d-%Y %H-%M-%S'


class _CustomXlsDoc(XlsDoc):
    def __init__(self,
                 book: Optional[Workbook] = None,
                 stream: Optional[bytes] = None):
        super().__init__()

        self.stream = stream or book.get_biff_data()  # type: ignore

        # Copied from original class
        self.padding = b'\x00' * (0x1000 - (len(self.stream) % 0x1000))
        self.book_stream_len = len(self.stream) + len(self.padding)

        self._build_directory()
        self._build_sat()
        self._build_header()

    def get_virtual_document(self) -> bytes:
        # Copied from `save` method
        bytes_ = bytes()

        bytes_ += self.header
        bytes_ += self.packed_MSAT_1st
        bytes_ += self.stream
        bytes_ += self.padding
        bytes_ += self.packed_MSAT_2nd
        bytes_ += self.packed_SAT
        bytes_ += self.dir_stream

        return bytes_


def _generate_report_title(sheet: Worksheet,
                           column: int = 0,
                           start_row: int = 0):
    sheet.write(column, start_row, 'UUID')
    sheet.write(column, start_row + 1, 'Изначальный текст')
    sheet.write(column, start_row + 2, 'Конвертированный текст')
    sheet.write(column, start_row + 3, 'Время получения')
    sheet.write(column, start_row + 4, 'Время отправления')


def generate_report_file_name() -> str:
    return f'Report from {datetime.now().strftime(REPORT_FILE_TIME_FORMAT)}.xlsx'


async def generate_report_content(offset: int = 0, limit: int = 1000) -> bytes:
    converted_texts = await ConvertedText.all().offset(offset).limit(limit)

    book = Workbook()
    sheet: Worksheet = book.add_sheet('Report')

    _generate_report_title(sheet)

    current_row = 1

    for converted_text in converted_texts:
        sheet.write(current_row, 0, str(converted_text.id))
        sheet.write(current_row, 1, converted_text.initial_text)
        sheet.write(current_row, 2, converted_text.converted_text)
        sheet.write(current_row, 3, converted_text.date_of_receipt.strftime(REPORT_TIME_FORMAT))
        sheet.write(current_row, 4, converted_text.date_of_sending.strftime(REPORT_TIME_FORMAT))

        current_row += 1

    doc = _CustomXlsDoc(book=book)

    return doc.get_virtual_document()
