import datetime

import pandas as pd

pd.set_option("display.max_columns", None)


DATA_URL_FMT = (
    "https://mesonet.agron.iastate.edu/"
    "cgi-bin/request/daily.py?"
    "network={network}&stations={station}&"
    "year1=1928&month1=1&day1=1&"
    "year2={today.year}&month2={today.month}&day2={today.day}"
)

def load_data(network: str = "CO_ASOS", station: str = "DEN") -> pd.DataFrame:
    """Load data from Iowa Environment Mesonet ASOS."""
    today = datetime.datetime.today()
    url = DATA_URL_FMT.format(network=network, station=station, today=today)
    df = pd.read_csv(url, parse_dates=True, index_col="day")
    return df


if __name__ == "__main__":
    df = load_data()
    print(df.dtypes)
    print(df.describe())
