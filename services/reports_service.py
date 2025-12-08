import os
from typing import List


REPORTS_DIR = "reports"


def list_reports() -> List[str]:
    """
    Lista relatórios ZIP da pasta /reports
    """
    try:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".zip")]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(REPORTS_DIR, x)), reverse=True)
        return files
    except Exception as e:
        print("Erro list_reports:", e)
        return []
