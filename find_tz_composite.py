# this will take lng/lat input and generate lng/lat/tz tuples

# pip install pyarrow timezonefinder rich more-itertools click

import click

from more_itertools import ichunked
import pyarrow.parquet as pq
import pyarrow as pa
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn,TransferSpeedColumn
from timezonefinder import TimezoneFinder
import sys

# constants
dummy_lst = [{'lng': 1.2, 'lat': 3.4, 'tz': "abc"}]
dummy_tbl = pa.Table.from_pylist(dummy_lst)

tf = TimezoneFinder(in_memory=True)

def get_tz(lng, lat):
    try:
        return tf.timezone_at(lng=lng, lat=lat)
    except:
        return ""


# https://stackoverflow.com/questions/77148138/how-to-iterate-and-read-one-row-at-at-time-from-multiple-parquet-files
def file_iterator(parquet_file, batch_size):
    for record_batch in parquet_file.iter_batches(batch_size=batch_size):
        for d in record_batch.to_pylist():
            yield d

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument("input_file", type=click.STRING)
@click.argument("output_file", type=click.STRING)
@click.argument("records_per_reading_batch", type=click.INT)
@click.argument("records_per_writing_batch", type=click.INT)

def main(input_file, output_file, records_per_reading_batch, records_per_writing_batch):
    """Finds tz for given file with lng-lat and prodices composite lng-lat-tz file

    INPUT_FILE is for the input parque file with lng-lat data, e.g `geo3-0.parquet`

    OUTPUT_FILE is for the output parque file with lng-lat-tz data, e.g `data3-0.parquet`

    RECORDS_PER_READING_BATCH is the number of records to read, e.g. 65536

    RECORDS_PER_WRITING_BATCH is the number of records to accumulate in ram before flushing to disk, e.g. 10000000
    """
    with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TransferSpeedColumn()
        ) as progress:

        with pq.ParquetFile(input_file) as parquet_file:
            scan_task = progress.add_task("Scanning for total record count", total=1)
            total_count = parquet_file.scan_contents(batch_size=records_per_reading_batch)
            progress.update(scan_task, advance=1)
            print(f"Total records: {total_count}")
            total_task = progress.add_task("Producing lng-lat-tz file", total=total_count)
            src = file_iterator(parquet_file, records_per_reading_batch)
            with pq.ParquetWriter(output_file, dummy_tbl.schema) as writer:
                # chunk to limit ram use
                for sub in ichunked(src, records_per_writing_batch):
                    lst = []
                    for rec in sub:
                        lng = rec['lng']
                        lat = rec['lat']
                        tz = get_tz(lng, lat)
                        if tz:
                            lst.append({'lng': lng, 'lat': lat, 'tz': tz})
                        progress.update(total_task, advance=1)
                    tbl = pa.Table.from_pylist(lst)
                    writer.write_table(tbl)
    return 0

if __name__ == "__main__":
    sys.exit(main())
