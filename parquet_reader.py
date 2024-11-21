# reads parquet file

# pip install pyarrow click

from itertools import islice
import click

import pyarrow.parquet as pq
import pyarrow as pa
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn,TransferSpeedColumn

# constants
dummy_lst = [{'lng': 1.2, 'lat': 3.4, 'tz': "abc"}]
dummy_tbl = pa.Table.from_pylist(dummy_lst)


# https://stackoverflow.com/questions/77148138/how-to-iterate-and-read-one-row-at-at-time-from-multiple-parquet-files
def file_iterator(parquet_file):
    for record_batch in parquet_file.iter_batches():
        for d in record_batch.to_pylist():
            yield d

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument("input_file", type=click.STRING)
@click.argument("skip", type=click.INT)
@click.argument("count", type=click.INT)

def main(input_file, skip, count):
    """Reads content of the parquet files 

        INPUT_FILE - what to read

        SKIP number of records to skip first, e.g. 0

        COUNT number of records to show, e.g. 10

    """
    with pq.ParquetFile(input_file) as parquet_file:
        src = file_iterator(parquet_file)
        sliced = islice(src, skip, skip+count)
        for rec in sliced:
            print(rec)


if __name__ == "__main__":
    main()
