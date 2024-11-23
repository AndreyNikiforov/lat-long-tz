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

dummy_lst = [{'lng': 1.2, 'lat': 3.4}]
dummy_tbl = pa.Table.from_pylist(dummy_lst)

def get_lng_lat3():
    for lng in lng_range:
        for lat in lat_range:
            for lng_degree1 in degree_range:
                for lat_degree1 in degree_range:
                    for lng_degree2 in degree_range:
                        for lat_degree2 in degree_range:
                            for lng_degree3 in degree_range:
                                for lat_degree3 in degree_range:
                                    if lng_degree3 > 0 or lat_degree3 > 0:
                                        # prev precision degrees were already written to data{0,1,2}
                                        lng_ = lng + lng_degree1/10**1 + lng_degree2/10**2 + lng_degree3/10**3
                                        lat_ = lat + lat_degree1/10**1 + lat_degree2/10**2 + lat_degree3/10**3
                                        yield lng_, lat_

def get_lng_lat2():
    for lng in lng_range:
        for lat in lat_range:
            for lng_degree1 in degree_range:
                for lat_degree1 in degree_range:
                    for lng_degree2 in degree_range:
                        for lat_degree2 in degree_range:
                            if lng_degree2 > 0 or lat_degree2 > 0:
                                # prev precision degrees were already written to data{0,1}
                                lng_ = lng + lng_degree1/10**1 + lng_degree2/10**2
                                lat_ = lat + lat_degree1/10**1 + lat_degree2/10**2
                                yield lng_, lat_

def get_lng_lat1():
    for lng in lng_range:
        for lat in lat_range:
            for lng_degree1 in degree_range:
                for lat_degree1 in degree_range:
                    if lng_degree1 > 0 or lat_degree1 > 0:
                        # prev precision degrees were already written to data{0}
                        lng_ = lng + lng_degree1/10**1
                        lat_ = lat + lat_degree1/10**1
                        yield lng_, lat_

def get_lng_lat0():
    for lng in lng_range:
        for lat in lat_range:
            yield float(lng), float(lat)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument("precision", type=click.IntRange(0, 3))
@click.argument("prefix", type=click.STRING)
@click.argument("records_per_file", type=click.INT)
@click.argument("records_per_batch", type=click.INT)
@click.option("--skip", type=click.INT, default=0, help="Number of initial files to skip")
@click.option("--limit", type=click.INT, default=None, help="Number of files to produce, all if not specified")

def main(precision, prefix, records_per_file, records_per_batch, skip, limit):
    """Generates files with lng-lat 

        PRECISION is degree of precision in generated lng-lat, e.g 2

        PREFIX is for the output file names, e.g `geo3`

        RECORDS_PER_FILE is the number of records to keep per output file, e.g. 1000000000

        RECORDS_PER_BATCH is the number of records to accumulate in ram before flushing to disk (optimize for RAM usage), e.g. 10000000
    """
    if skip < 0:
        print("Skip option should be positive or zero")
        return 1
    if limit is not None and limit < 1:
        print("Limit option, if specified, should be positive and greater than zero")
        return 1
    print(f"Process ID: {os.getpid()}")
    total_count = len(lng_range) * len(lat_range) * 10**(precision*2)
    if skip * records_per_file > total_count:
        print("Skiping more than max possible")
        return 1
    if limit is not None:
        total_count = min(total_count, (skip + limit) * records_per_file)
    print(f"Estimated count (limited, but not skipped): {total_count}")

    with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TransferSpeedColumn()
        ) as progress:

        total_task = progress.add_task("Total", total=total_count)
        if precision == 0:
            get_lng_lat = get_lng_lat0
        elif precision == 1:
            get_lng_lat = get_lng_lat1
        elif precision == 2:
            get_lng_lat = get_lng_lat2
        elif precision == 3:
            get_lng_lat = get_lng_lat3
        else:
            raise NotImplementedError(f"Precision of {precision} is not supported by all parts of the code")
        
        lng_lat_chunked = ichunked(get_lng_lat(), records_per_file)
        for i, src in enumerate(lng_lat_chunked):
            if limit and (i - skip) >= limit:
                progress.update(total_task, completed=total_count)
                break
            if i >= skip:
                file_name = f"{prefix}_{i}.parquet"
                with pq.ParquetWriter(file_name, dummy_tbl.schema) as writer:
                    # chunk further to limit ram use
                    for sub in ichunked(src, records_per_batch):
                        lst = {'lng': [], 'lat': []}
                        for lng, lat in sub:
                            lst['lng'].append(lng)
                            lst['lat'].append(lat)
                            progress.update(total_task, advance=1)
                        tbl = pa.Table.from_pydict(lst)
                        writer.write_table(tbl)
            else:
                for sub in src:
                    progress.update(total_task, advance=1)  # for responsive canceling
    return 0



if __name__ == "__main__":
    sys.exit(main())
