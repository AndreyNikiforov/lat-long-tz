# this will list all known tz

# pip install pyarrow rich click timezonefinder

import click

import pyarrow.parquet as pq
import pyarrow as pa
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn,TransferSpeedColumn
from timezonefinder import TimezoneFinder

# constants
dummy_lst = [{'tz': "abc"}]
dummy_tbl = pa.Table.from_pylist(dummy_lst)

tf = TimezoneFinder(in_memory=True)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument("filename", type=click.STRING)
@click.option("--add", multiple=True, show_default=True, help="Add custom values to the output")

def main(filename, add):
    """Lists all tz into file 

        FILENAME is for the output file name, e.g. `tz.parquet`
    """

    with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TransferSpeedColumn()
        ) as progress:

        with pq.ParquetWriter(filename, dummy_tbl.schema) as writer:
            lst = []
            for tz in progress.track(tf.timezone_names + list(add)):
                lst.append({'tz': tz})
            tbl = pa.Table.from_pylist(lst)
            writer.write_table(tbl)
    return 0

if __name__ == "__main__":
    exit(main())
