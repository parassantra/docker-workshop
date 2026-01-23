#!/usr/bin/env python
# coding: utf-8

import click
import pandas as pd
from tqdm.auto import tqdm
from sqlalchemy import create_engine


def get_file_type(file_path):
    """Detect file type from extension."""
    file_path_lower = file_path.lower()
    if file_path_lower.endswith('.parquet'):
        return 'parquet'
    elif file_path_lower.endswith('.csv') or file_path_lower.endswith('.csv.gz'):
        return 'csv'
    else:
        raise ValueError(f"Unsupported file type. Use .csv, .csv.gz, or .parquet")


def process_csv(file_url, engine, target_table, chunksize):
    """Process CSV file in chunks."""
    df_iter = pd.read_csv(
        file_url,
        iterator=True,
        chunksize=chunksize
    )
    
    is_table_head = True
    total_rows = 0
    
    for df_chunk in tqdm(df_iter, desc="Processing chunks"):
        if is_table_head:
            df_chunk.to_sql(name=target_table, con=engine, if_exists='replace')
            is_table_head = False
            print(f"Table '{target_table}' created")
        else:
            df_chunk.to_sql(name=target_table, con=engine, if_exists='append')
        
        total_rows += len(df_chunk)
        print(f"Inserted: {len(df_chunk)} rows")
    
    return total_rows


def process_parquet(file_url, engine, target_table, chunksize):
    """Process parquet file (read all, insert in chunks)."""
    print("Reading parquet file...")
    df = pd.read_parquet(file_url)
    total_rows = len(df)
    
    # Insert in chunks
    is_table_head = True
    for start in tqdm(range(0, total_rows, chunksize), desc="Processing chunks"):
        end = min(start + chunksize, total_rows)
        df_chunk = df.iloc[start:end]
        
        if is_table_head:
            df_chunk.to_sql(name=target_table, con=engine, if_exists='replace')
            is_table_head = False
            print(f"Table '{target_table}' created")
        else:
            df_chunk.to_sql(name=target_table, con=engine, if_exists='append')
        
        print(f"Inserted: {len(df_chunk)} rows")
    
    return total_rows


@click.command()
@click.option('--file-url', 'file_url', type=str, required=True, help='URL or path to CSV/Parquet file')
@click.option('--target-table', 'target_table', type=str, required=True, help='Target table name')
@click.option('--chunksize', default=100000, type=int, help='Chunksize for processing')
@click.option('--pg-user', 'pg_user', default='root', type=str, help='PostgreSQL user')
@click.option('--pg-password', 'pg_password', default='root', type=str, help='PostgreSQL password')
@click.option('--pg-host', 'pg_host', default='localhost', type=str, help='PostgreSQL host')
@click.option('--pg-port', 'pg_port', default=5432, type=int, help='PostgreSQL port')
@click.option('--pg-db', 'pg_db', default='ny_taxi', type=str, help='PostgreSQL database')
def run_insert_table(file_url, target_table, chunksize, pg_user, pg_password, pg_host, pg_port, pg_db):
    """Insert CSV or Parquet data into PostgreSQL database."""
    
    # Create database connection
    engine = create_engine(f'postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}')
    
    # Detect file type
    file_type = get_file_type(file_url)
    
    print(f"Reading from: {file_url}")
    print(f"File type: {file_type}")
    print(f"Target table: {target_table}")
    
    # Process based on file type
    if file_type == 'csv':
        total_rows = process_csv(file_url, engine, target_table, chunksize)
    else:
        total_rows = process_parquet(file_url, engine, target_table, chunksize)
    
    print(f"Done! Total rows inserted: {total_rows}")


if __name__ == '__main__':
    run_insert_table()
