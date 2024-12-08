"""Download flatfiles from polygon."""

import logging
import os
from datetime import datetime, timedelta
from glob import glob

import boto3
import pandas as pd
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = "flatfiles"
DAYS_TO_GET = 250

# Initialize a session using your credentials
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

s3 = session.client(
    "s3",
    endpoint_url="https://files.polygon.io",
    config=Config(signature_version="s3v4"),
)
paginator = s3.get_paginator("list_objects_v2")
prefix = "us_stocks_sip"


def build_file_list():
    """Build a list of files needed from polygon."""
    today = datetime.today()

    files_to_get = []
    for i in range(DAYS_TO_GET):
        year = (today - timedelta(days=i)).strftime("%Y")
        month = (today - timedelta(days=i)).strftime("%m")
        day = (today - timedelta(days=i)).strftime("%d")

        path = f"us_stocks_sip/day_aggs_v1/{year}/{month}/{year}-{month}-{day}.csv.gz"
        files_to_get.append(path)

    return files_to_get


def check_file_exists(path):
    """Check if a file exists in an S3 bucket."""
    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=path)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ["403", "404"]:
            return False
        else:
            raise


def download_flatfiles():
    """Download flatfiles from polygon."""
    files_to_get = build_file_list()

    downloaded_files = []
    for index, path in enumerate(files_to_get):
        dest = f"flatfiles/{path.split('/')[-1]}"

        if not os.path.isfile(dest):
            if not check_file_exists(path):
                logger.info(f"File {path} does not exist")
                continue
            logger.info(f"Downloading {path} to {dest}")
            s3.download_file("flatfiles", path, dest)
            downloaded_files.append(dest)
        else:
            logger.info(f"File {dest} already exists")

        if index > DAYS_TO_GET:
            return downloaded_files


def build_timestamp(filename):
    """Build a timestamp from a filename."""
    return filename.split("/")[-1].split(".")[0]


def read_stock_csv(file_path):
    """Read a CSV file and return a DataFrame."""
    df = pd.read_csv(file_path)
    df["timestamp"] = build_timestamp(file_path)
    df.drop(columns=["window_start", "transactions"], inplace=True)
    return df


def read_all_csv_files():
    """Read all CSV files and return a DataFrame."""
    all_files = glob("flatfiles/*.csv.gz")
    df = pd.concat((read_stock_csv(f) for f in all_files))
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["ticker", "timestamp"])
    df = df.reset_index(drop=True)
    return df


def build_parquet():
    """Build a parquet file from the flatfiles."""
    df = read_all_csv_files()
    df.to_parquet("flatfiles.parquet")


if __name__ == "__main__":
    download_flatfiles()
    build_parquet()
