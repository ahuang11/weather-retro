import datetime

import pandas as pd
import hvplot.pandas
import holoviews as hv

pd.set_option("display.max_columns", None)


DATA_URL_FMT = (
    "https://mesonet.agron.iastate.edu/"
    "cgi-bin/request/daily.py?"
    "network={network}&stations={station}&"
    "year1=1928&month1=1&day1=1&"
    "year2={today.year}&month2={today.month}&day2={today.day}"
)

def load_data(today: datetime, network: str, station: str):
    """Load data from Iowa Environment Mesonet ASOS."""
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




def select_data(
    today: datetime,
    preprocess_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Select only the rows matching "todate" (day of year).
    """
    return preprocess_df.loc[
        (preprocess_df.index.month == today.month) &
        (preprocess_df.index.day == today.day)
    ]


def plot_data(
    today: datetime,
    select_df: pd.DataFrame,
    weather_var: str
):
    """
    Create a histogram showing the distribution of
    weather over the years, and highlight today's
    weather with a red line.
    """
    # prepare the titles and labels
    year_range = (
      f"{select_df.index.year.min()} - "
      f"{select_df.index.year.max()}"
    )
    weather_label = weather_var.replace("_", " ").title()
    title = (
      f"{network}: {station}'s {year_range} "
      f"{today:%B %d}'s {weather_label}"
    )
    climo_hist = select_df.hvplot.hist(
      weather_var,
      title=title,
      xlabel=weather_label,
      ylabel="Number of Years"
    )

    # highlight today
    weather_today = select_df.iloc[-1][weather_var]
    today_line = hv.VLine(weather_today).opts(color="red")
    today_text = hv.Text(
      weather_today, 3, f"Today"
    ).opts(text_align="right")
    weather_plot = climo_hist * today_line * today_text
    return weather_plot


if __name__ == "__main__":
    # parameters
    network = "CO_ASOS"
    station = "DEN"
    today = datetime.datetime.today()

    df = load_data(today=today, network=network, station=station)
    preprocess_df = preprocess_data(df)
    select_df = select_data(today, preprocess_df)
    weather_plot = plot_data(today, select_df, "min_temp_f")
    display(weather_plot)
