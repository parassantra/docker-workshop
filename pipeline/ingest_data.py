#!/usr/bin/env python
# coding: utf-8

import click
import pandas as pd
from tqdm.auto import tqdm
from sqlalchemy import create_engine

# Define data types
dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

# Define datetime columns
parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]

@click.command()
@click.option('--year', default=2021, type=int, help='Year of the data')
@click.option('--month', default=1, type=int, help='Month of the data')
@click.option('--chunksize', default=100000, type=int, help='Chunksize for the data')
@click.option('--target-table', default='yellow_taxi_data', type=str, help='Target table for the data')
@click.option('--pg-user', 'pg_user', default='root', type=str, help='PostgreSQL user')
@click.option('--pg-password', 'pg_pass', default='root', type=str, help='PostgreSQL password')
@click.option('--pg-host', 'pg_host', default='localhost', type=str, help='PostgreSQL host')
@click.option('--pg-port', 'pg_port', default=5432, type=int, help='PostgreSQL port')
@click.option('--pg-db', 'pg_db', default='ny_taxi', type=str, help='PostgreSQL database')
def run_ingestion(year, month, chunksize, target_table, pg_user, pg_pass, pg_host, pg_port, pg_db):
    """Ingest NYC taxi data into PostgreSQL database."""

    prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/'
    url = f'{prefix}/yellow_tripdata_{year}-{month:02d}.csv.gz'
    engine = create_engine(f'postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')
   
    df_iter = pd.read_csv(
        url, 
        dtype=dtype, 
        parse_dates=parse_dates, 
        iterator=True,
        chunksize=chunksize
    )


    is_table_head = True
    for df_chunk in tqdm(df_iter):
        if is_table_head:
            df_chunk.head(n=0).to_sql(name=target_table, con=engine, if_exists='replace')
            is_table_head = False
        else:
            df_chunk.to_sql(name=target_table, con=engine, if_exists='append')
        print("Inserted:", len(df_chunk))


if __name__ == '__main__':
    run_ingestion()