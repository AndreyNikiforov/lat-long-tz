# this will generate all lng/lat/tz tuples for training
# pip install timezonefinder

from timezonefinder import TimezoneFinder
import pyarrow.parquet as pq
import pyarrow as pa
from tqdm import tqdm 

tf = TimezoneFinder(in_memory=True)

lng_range = range(-180, 180, 1)
lat_range = range(-90, 90, 1)

def get_tz(lng, lat):
    try:
        return tf.timezone_at(lng=lng, lat=lat)
    except:
        return ""

dummy_lst = [{'lng': 1.2, 'lat': 3.4, 'tz': "abc"}]
dummy_tbl = pa.Table.from_pylist(dummy_lst)

# parq with new tbl per row was killed/died after ~1hr, generated huge file (compression is post processing?)
with pq.ParquetWriter('data0.parq', dummy_tbl.schema) as writer:
    #  header
    lst = []
    for lng in tqdm([lng * 1.0 for lng in lng_range]):
        for lat in [lat * 1.0 for lat in lat_range]:
            tz = get_tz(lng, lat)
            if tz:
                lst.append({'lng': lng, 'lat': lat, 'tz': tz})
    tbl = pa.Table.from_pylist(lst)
    writer.write_table(tbl)
