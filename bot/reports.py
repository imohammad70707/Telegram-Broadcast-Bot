import json
import os
from datetime import datetime


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

REPORTS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "reports.json"
)


def ensure_reports_file():
    os.makedirs(
        os.path.dirname(REPORTS_FILE),
        exist_ok=True
    )

    if not os.path.exists(REPORTS_FILE):

        with open(
            REPORTS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                [],
                file,
                ensure_ascii=False,
                indent=2
            )


def load_reports():
    ensure_reports_file()

    try:

        with open(
            REPORTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError
    ):

        return []


def save_reports(reports):

    ensure_reports_file()

    with open(
        REPORTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            reports,
            file,
            ensure_ascii=False,
            indent=2
        )


def create_report(
    message_text,
    total_groups,
    success,
    failed,
    results
):

    reports = load_reports()

    report_id = len(reports) + 1

    report = {
        "id": report_id,

        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "message_length": len(
            message_text
        ),

        "total_groups": total_groups,

        "success": success,

        "failed": failed,

        "message": message_text,

        "results": results,
    }

    reports.append(report)

    save_reports(reports)

    return report


def get_last_report():

    reports = load_reports()

    if not reports:
        return None

    return reports[-1]
