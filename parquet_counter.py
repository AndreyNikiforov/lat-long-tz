
# pip install "dask[complete]" click

import dask.dataframe as dd
import click
import sys

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}

@click.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument("path", type=click.STRING)
def main(path):
    """Count records in all parquet files matching pattern

        PATH file pattern to files, e.g. "data/lng-lat-tz/geo*.parquet"
    """

    df = dd.read_parquet(path)
    count = df.count(axis=0).compute()
    print(f"Total records: {count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
