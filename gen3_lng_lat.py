# this will generate all lng/lat tuples with precision degree of 3 (skipping other)
# will break dataset into chunks/files, so each can be search for TZ in parallel later

# pip install pyarrow rich more-itertools click

import click

from more_itertools import ichunked
import pyarrow.parquet as pq
import pyarrow as pa
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn,TransferSpeedColumn

# constants
lng_range = range(-180, 180, 1)
lat_range = range(-90, 90, 1)

dummy_lst = [{'lng': 1.2, 'lat': 3.4}]
dummy_tbl = pa.Table.from_pylist(dummy_lst)

def get_lng_lat():
    for lng in [lng * 1.0 for lng in lng_range]:
        for lat in [lat * 1.0 for lat in lat_range]:
            for lng_degree1 in [degree for degree in range(0,9)]:
                for lat_degree1 in [degree for degree in range(0,9)]:
                    for lng_degree2 in [degree for degree in range(0,9)]:
                        for lat_degree2 in [degree for degree in range(0,9)]:
                            for lng_degree3 in [degree for degree in range(0,9)]:
                                for lat_degree3 in [degree for degree in range(0,9)]:
                                    if lng_degree3 > 0 or lat_degree3 > 0:
                                        # prev precision degrees were already written to data{0,1,2}
                                        lng_ = lng + lng_degree1/10**1 + lng_degree2/10**2 + lng_degree3/10**3
                                        lat_ = lat + lat_degree1/10**1 + lat_degree2/10**2 + lat_degree3/10**3
                                        yield lng_, lat_


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument("prefix", type=click.STRING)
@click.argument("records_per_file", type=click.INT)
@click.argument("records_per_batch", type=click.INT)

def main(prefix, records_per_file, records_per_batch):
    """Generates files with lng-lat 

    PREFIX is for the output file names, e.g `geo3`

    RECORDS_PER_FILE is the number of records to keep per output file, e.g. 1000000000

    RECORDS_PER_BATCH is the number of records to accumulate in ram before flushing to disk, e.g. 10000000
    """
    with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TransferSpeedColumn()
        ) as progress:

        total_count = len(lng_range) * len(lat_range) * 10**6
        print(f"Estimated count: {total_count}")
        total_task = progress.add_task("Total", total=total_count)
        lng_lat_chunked = ichunked(get_lng_lat(), records_per_file)
        for i, src in enumerate(lng_lat_chunked):
            file_name = f"{prefix}_{i}.parquet"
            with pq.ParquetWriter(file_name, dummy_tbl.schema) as writer:
                # chunk further to limit ram use
                for sub in ichunked(src, records_per_batch):
                    lst = []
                    for lng, lat in sub:
                        lst.append({'lng': lng, 'lat': lat})
                        progress.update(total_task, advance=1)
                    tbl = pa.Table.from_pylist(lst)
                    writer.write_table(tbl)


if __name__ == "__main__":
    main()
