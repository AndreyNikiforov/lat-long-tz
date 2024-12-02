# this will generate lng/lat tuples with specified precision degree (skipping other)
# will break dataset into chunks/files, so each can be search for TZ in parallel later

# pip install pyarrow rich more-itertools click

import click

from more_itertools import consume, ichunked
import pyarrow.parquet as pq
import pyarrow as pa
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn,TransferSpeedColumn
import sys
import os

# constants
lng_range = range(-180, 181, 1)
lat_range = range(-90, 91, 1)
degree_range = range(0,10, 1)

output_schema = pa.schema([
        pa.field('lng', pa.float64(), nullable=False),
        pa.field('lat', pa.float64(), nullable=False),
    ])

def get_precision_lng_lat():
    for lng in lng_range:
        for lat in lat_range:
            for lng_degree1 in degree_range:
                for lat_degree1 in degree_range:
                    for lng_degree2 in degree_range:
                        for lat_degree2 in degree_range:
                            for lng_degree3 in degree_range:
                                for lat_degree3 in degree_range:
                                    if lng_degree3 > 0 or lat_degree3 > 0:
                                        precision = 3
                                    elif lng_degree2 > 0 or lat_degree2 > 0:
                                        precision = 2
                                    elif lng_degree1 > 0 or lat_degree1 > 0:
                                        precision = 1
                                    else:
                                        precision = 0
                                    lng_ = lng + lng_degree1/10**1 + lng_degree2/10**2 + lng_degree3/10**3
                                    lat_ = lat + lat_degree1/10**1 + lat_degree2/10**2 + lat_degree3/10**3
                                    yield precision, lng_, lat_

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument("folder", type=click.STRING)

def main(folder):
    """Generates files with precision-lng-lat 

        FOLDER is degree of precision in generated lng-lat, e.g 2

        NOTE: This will create many small 4k files in each partition - not workable solution
    """
    print(f"Process ID: {os.getpid()}")
    total_count = len(lng_range) * len(lat_range) * 10**(3*2)
    print(f"Estimated count: {total_count}")

    with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TransferSpeedColumn()
        ) as progress:

        precision_lng_lat = progress.track(get_precision_lng_lat(), total=total_count)
        for src in ichunked(precision_lng_lat, 10_000_000):
            lst = {'precision': [], 'lng': [], 'lat': []}
            for precision, lng, lat in src:
                lst['precision'].append(precision)
                lst['lng'].append(lng)
                lst['lat'].append(lat)
            tbl = pa.Table.from_pydict(lst).cast(output_schema)
            pq.write_to_dataset(tbl, root_path=folder, partition_cols=["precision"])

    return 0



if __name__ == "__main__":
    sys.exit(main())
