
# pip install "dask[complete]" click

import dask.dataframe as dd
import click
import sys
import re


def blocksize_validator(ctx, param, value):
    if re.match('\d+[kKmMgG]', value):
        return value
    else:
        raise click.BadParameter('Invalid blocksize. Must be number with K/M/G suffix')
    
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}

@click.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument("path", type=click.STRING)
@click.option(
    "--blocksize", 
    type=click.STRING, 
    default="256M", 
    show_default=True, 
    help="What blocksize to use when reading parquet",
    callback=blocksize_validator
    )
def main(path, blocksize):
    """Count records in all parquet files matching pattern

        PATH file pattern to files, e.g. "data/lng-lat-tz/geo*.parquet", one file, or one folder
    """

    df = dd.read_parquet(
        path, 
        aggregate_files=True,
        split_row_groups='adaptive', # works but slow
        # 1 - 7min
        # 5 - 8 min
        # 6 - killed
        # 7 - killed
        # 10 - killed
        # adaptive - killed
        # aggregate_files=True,
        # split_row_groups="adaptive",
        # split_row_groups=1, 
        blocksize=blocksize, # default
        # 6m/adaptive - 7min
        # 6m/infer - 8min
        # 8m/infer - 8min
        # 8m/adaptive - 8min
        # 16m/infer - killed
        # 16m/adaptive - killed
        # 32m/infer - killed
        # metadata_task_size=0,
        )
    count = df.count(axis=0).compute()
    print(f"Total records: {count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
