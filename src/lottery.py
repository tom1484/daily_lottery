import os
import time
from typing import Any, Dict, List, Tuple
from operator import itemgetter

import pandas as pd
import requests
import tqdm

OLD_URL = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/4DHistoryResult"
NEW_URL = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/4DResult"
START_YEAR = 2007
NEW_START_YEAR = 2024


def fetch_month_data(year: int, month: int) -> List[Tuple[int, List[int]]]:
    query = f"period&month={year:04d}-{month:02d}&pageNum=1&pageSize=100"
    if year >= NEW_START_YEAR:
        url = f"{NEW_URL}?{query}"
        response = requests.get(url)
        data = response.json()
        content = data["content"]["lotto4DRes"]

        return [(record["period"], record["drawNumberAppear"]) for record in content]
    else:
        url = f"{OLD_URL}?{query}"
        response = requests.get(url)
        data = response.json()
        content = data["content"]["lotto4DHistoryRes"]

        return [(record["period"], record["drawNumberAppear"]) for record in content]


def append_history(
    history: Dict, year: int, month: int, period: int, numbers: List[int]
):
    history["year"].append(f"{year:04d}")
    history["month"].append(f"{month:02d}")
    history["period"].append(f"{period:09d}")
    history["number"].append("".join(map(str, numbers)))


def update_history():
    localtime = time.localtime()
    current_year = localtime.tm_year
    current_month = localtime.tm_mon

    if not os.path.exists("history.csv"):
        with open("history.csv", "w") as f:
            f.write("year,month,period,number\n")

    history = pd.read_csv(
        "history.csv", dtype={"year": int, "month": int, "period": int, "number": str}
    )

    new_history_count = 0
    new_history = {"year": [], "month": [], "period": [], "number": []}
    for year in tqdm.tqdm(range(START_YEAR, current_year + 1)):
        for month in range(1, 13):
            month_history = history[
                (history["year"] == year) & (history["month"] == month)
            ]

            if year == current_year and month == current_month:
                # Fetch new data of current month
                data = fetch_month_data(year, month)
                for period, numbers in data:
                    if (
                        month_history.shape[0] == 0
                        or period > month_history["period"].max()
                    ):
                        append_history(new_history, year, month, period, numbers)
                        new_history_count += 1
            else:
                # Fetch all if old history is empty
                if month_history.shape[0] == 0:
                    data = fetch_month_data(year, month)
                    for period, numbers in data:
                        append_history(new_history, year, month, period, numbers)
                        new_history_count += 1

    new_history = pd.DataFrame(new_history)
    history = pd.concat([history, new_history], ignore_index=True)

    history.to_csv("history.csv", index=False)

    return new_history_count


def extract_statistics(n: int = 200) -> Dict[str, Any]:
    history = pd.read_csv(
        "history.csv", dtype={"year": int, "month": int, "period": int, "number": str}
    )

    history.sort_values(by=["year", "month"], inplace=True)
    history = history.tail(n)

    statistics = {}

    # Put all records
    history_rows = [(row["period"], row["number"]) for _, row in history.iterrows()]
    history_rows.sort(key=itemgetter(0))
    records = [f"{period} {number}" for period, number in history_rows]

    statistics["records"] = records

    # Calculate two-digit missing numbers
    missings = [[], []]
    highs = set([int(row["number"][:2]) for _, row in history.iterrows()])
    lows = set([int(row["number"][2:]) for _, row in history.iterrows()])

    for i in range(100):
        if i not in highs:
            missings[0].append(i)
        if i not in lows:
            missings[1].append(i)

    statistics["missings"] = missings

    return statistics
