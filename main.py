import datetime

import pandas as pd
import hvplot.pandas
import holoviews as hv
import panel as pn
from holoviews.selection import link_selections
from scipy.stats import percentileofscore

hv.extension("bokeh")
pn.extension()
pd.set_option("display.max_columns", None)
pn.config.sizing_mode = "stretch_width"
pn.param.ParamMethod.loading_indicator = True


DATA_URL_FMT = (
    "https://mesonet.agron.iastate.edu/"
    "cgi-bin/request/daily.py?"
    "network={network}&stations={station}&"
    "year1=1928&month1=1&day1=1&"
    "year2={date.year}&month2={date.month}&day2={date.day}"
)

STATES_URL = (
    "https://raw.githubusercontent.com/" "jasonong/List-of-US-States/master/states.csv"
)

NETWORK_URL_FMT = (
    "https://mesonet.agron.iastate.edu/sites/networks.php?network="
    "{network}&format=csv&nohtml=on"
)

WEATHER_VARS = [
    "max_temp_f",
    "min_temp_f",
    "max_dewpoint_f",
    "min_dewpoint_f",
    "precip_in",
    "avg_wind_speed_kts",
    "avg_wind_drct",
    "min_rh",
    "avg_rh",
    "max_rh",
    "climo_high_f",
    "climo_low_f",
    "climo_precip_in",
    "snow_in",
    "snowd_in",
    "min_feel",
    "avg_feel",
    "max_feel",
    "max_wind_speed_kts",
    "max_wind_gust_kts",
    "srad_mj",
]


@pn.cache()
def load_data(date: datetime, network: str, station: str):
    """Load data from Iowa Environment Mesonet ASOS."""
    url = DATA_URL_FMT.format(network=network, station=station, date=date)
    print(url)
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
        df.drop(columns=["station"])
        .apply(pd.to_numeric, errors="coerce")
        .astype("float32")
    )


@pn.cache()
def select_data(date: datetime, preprocess_df: pd.DataFrame) -> pd.DataFrame:
    """
    Select only the rows matching "todate" (day of year).
    """
    return preprocess_df.loc[
        (preprocess_df.index.month == date.month)
        & (preprocess_df.index.day == date.day)
    ]


def plot_data(
    date: datetime,
    network: str,
    station: str,
    select_df: pd.DataFrame,
    weather_var: str,
):
    """
    Create a histogram showing the distribution of
    weather over the years, and highlight date's
    weather with a red line.
    """
    # prepare the titles and labels
    select_df = select_df.assign(
        **{
            "score": pd.cut(select_df.index.year, bins=range(1930, 2060, 20))
        }
    ).dropna(subset=[weather_var])
    weather_label = weather_var.replace("_", " ").title()
    station_row = load_station_df(network).query(f"stid == '{station}'")
    station_label = station_row["station_name"].item().title()
    weather_df = select_df[weather_var]
    title = (
        f"{network}: {station_label}'s "
        f"{date:%B %d}'s {weather_label} ({len(weather_df)} years)"
    ).replace("_", " ")
    climo_hist = weather_df.hvplot.hist(
        weather_var, xlabel=weather_label, ylabel="Number of Years"
    )

    # highlight date
    weather_date = select_df.iloc[-1][weather_var]

    # get average
    weather_average = weather_df.mean()
    average_line = hv.VLine(weather_average).opts(color="black")
    average_text = hv.Text(weather_average + 0.5, 1, f"Average").opts(text_align="left")

    date_line = hv.VLine(weather_date).opts(color="brown")
    date_text = hv.Text(weather_date - 0.5, 3, f"{date:%Y}").opts(
        text_align="right", color="brown"
    )

    # overlay
    weather_plot = climo_hist * average_line * average_text * date_line * date_text

    # get a kde plot
    kde_plot = select_df.hvplot.kde(
        weather_var, xlabel=weather_label, by="score"
    )

    # table
    weather_table = weather_df.hvplot.table()

    # layout
    min = weather_df.min()
    min_idx = weather_df.idxmin()
    min_number = pn.widgets.Number(
        name=f"Min ({min_idx:%Y})",
        value=min,
        format="{value:.0f}",
        title_size="15pt",
        font_size="25pt",
        width=150,
    )
    max = weather_df.max()
    max_idx = weather_df.idxmax()
    max_number = pn.widgets.Number(
        name=f"Max ({max_idx:%Y})",
        value=max,
        format="{value:.0f}",
        title_size="15pt",
        font_size="25pt",
        width=150,
    )
    avg = weather_df.mean()
    avg_number = pn.widgets.Number(
        name=f"Average",
        value=avg,
        format="{value:.0f}",
        title_size="15pt",
        font_size="25pt",
        width=150,
    )
    median = weather_df.median()
    median_number = pn.widgets.Number(
        name=f"Median",
        value=median,
        format="{value:.0f}",
        title_size="15pt",
        font_size="25pt",
        width=150,
    )
    value_number = pn.widgets.Number(
        name=f"2023",
        value=weather_date,
        format="{value:.0f}",
        title_size="15pt",
        font_size="25pt",
        width=150,
    )
    percentile = percentileofscore(weather_df, weather_date, kind="strict")
    percentile_number = pn.widgets.Number(
        name=f"Percentile ({date:%Y})",
        value=percentile,
        format="{value:.0f}%",
        title_size="15pt",
        font_size="25pt",
        width=200,
    )
    stats_row = pn.Row(
        percentile_number,
        value_number,
        median_number,
        avg_number,
        min_number,
        max_number,
        align="center",
    )
    layout = (weather_plot + kde_plot + weather_table).cols(1)
    title_md = pn.pane.Markdown(f"# <center>{title}</center>")
    return pn.Column(title_md, stats_row, layout, align="center")


def update_dashboard(date, network, station, weather_var):
    """Update the dashboard with new data."""
    df = load_data(date, network, station)
    preprocess_df = preprocess_data(df)
    select_df = select_data(date, preprocess_df)
    weather_plot = plot_data(date, network, station, select_df, weather_var)
    return weather_plot


@pn.cache()
def load_station_df(network: str):
    station_df = pd.read_csv(NETWORK_URL_FMT.format(network=network))
    return station_df


def update_station(event):
    stations = load_station_df(event.new)["stid"]
    station_select.param.update(value=stations[0], options=list(stations))


# widgets
date_picker = pn.widgets.DatePicker(name="Date", value=datetime.date.today())

networks = [f"{state}_ASOS" for state in pd.read_csv(STATES_URL)["Abbreviation"]]
network_select = pn.widgets.Select(name="Network", value="CO_ASOS", options=networks)

station_select = pn.widgets.AutocompleteInput(name="Station", min_characters=1)
network_select.param.watch(update_station, "value")
network_select.param.trigger("value")

weather_var_select = pn.widgets.Select(name="Weather", options=WEATHER_VARS)

# link function to widgets
plot = pn.bind(
    update_dashboard,
    date=date_picker,
    network=network_select,
    station=station_select,
    weather_var=weather_var_select,
)

# layout
sidebar = pn.Column(date_picker, weather_var_select, network_select, station_select)
main = pn.Column(plot)
template = pn.template.FastListTemplate(
    sidebar=sidebar, main=main, title="WeatherRetro"
)
template.servable()
