from pydantic import BaseModel
from typing import List


class ReportList(BaseModel):
    files: List[str]


class ReportDownload(BaseModel):
    filename: str
