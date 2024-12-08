"""Calculate the HVCs for the recent data."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

VOLUME_THRESHOLD = 3
MINIMUM_VOLUME = 300000
MINIMUM_PRICE = 5.00


def filter_columns(df):
    """Filter the columns of the DataFrame."""
    df = df[["timestamp", "ticker", "volume", "close"]]
    return df


def filter_by_price(df):
    """Filter the DataFrame by price."""
    df = df[df["close"] > MINIMUM_PRICE]
    return df


def calculate_ma(df):
    """Calculate the moving average of the DataFrame."""
    for i in [20, 50, 150, 200]:
        df[f"{i}MA"] = (
            df.groupby("ticker")["close"]
            .rolling(window=i)
            .mean()
            .reset_index(level=0, drop=True)
        )
    return df


def calculate_hvcs(df):
    """Add HVC columns to the DataFrame."""
    df["20d_vol_ma"] = (
        df.groupby("ticker")["volume"]
        .rolling(window=20)
        .mean()
        .reset_index(level=0, drop=True)
    )
    df["rel_vol"] = df["volume"] / df["20d_vol_ma"]
    df["hvc"] = df["volume"] > (VOLUME_THRESHOLD * df["20d_vol_ma"])
    df = df[df["20d_vol_ma"] > MINIMUM_VOLUME].copy(deep=True)
    return df[df["hvc"]]


def run():
    df = pd.read_parquet("flatfiles.parquet")
    df = filter_columns(df)
    df = filter_by_price(df)
    df = calculate_ma(df)
    df = calculate_hvcs(df)
    df = df.sort_values(by=["timestamp", "ticker"], ascending=[False, True])
    return df


if __name__ == "__main__":
    print(run())