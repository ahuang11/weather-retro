import datetime

import pandas as pd
import hvplot.pandas

pd.set_option("display.max_columns", None)


DATA_URL_FMT = (
    "https://mesonet.agron.iastate.edu/"
    "cgi-bin/request/daily.py?"
    "network={network}&stations={station}&"
    "year1=1928&month1=1&day1=1&"
    "year2={today.year}&month2={today.month}&day2={today.day}"
)

def load_data(network: str = "CO_ASOS", station: str = "DEN"):
    """Load data from Iowa Environment Mesonet ASOS."""
    today = datetime.datetime.today()
    url = DATA_URL_FMT.format(network=network, station=station, today=today)
    df = pd.read_csv(url, parse_dates=True, index_col="day")
    return df


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess the data by: 
    - removing the station column
    - converting all columns to numeric,
      coercing the bad values into NaN
    - converting the types to float32 to reduce memory footprint
    """
    return (
      df
      .drop(columns=["station"])
      .apply(pd.to_numeric, errors="coerce")
      .astype("float32")
  	)


if __name__ == "__main__":
    df = load_data()
    # optionally find out what the bad value is
    # by sorting the unique values;
    # the bad values usually show up as
    # the first or last value of the list
    print(sorted(df["max_dewpoint_f"].unique()))

    preprocess_df = preprocess_data(df)

    # show that converting to float reduced the memory footprint
    # from 13125856 to 1138408 bytes
    print("Before", df.memory_usage(deep=True).sum())
    print("After", preprocess_df.memory_usage(deep=True).sum())

    # show statistics of the dataframe
    print(preprocess_df.describe())
  