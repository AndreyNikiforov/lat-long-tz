# this will generate all lng/lat/tz tuples for training
# pip install timezonefinder pyarrow tqdm

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

t = tqdm(total=len(lng_range) * len(lat_range) * 10**6)

# parq with new tbl per row was killed/died after ~1hr, generated huge file (compression is post processing?)
with pq.ParquetWriter('data3.parq', dummy_tbl.schema) as writer:
    #  header
    # file.write("lng,lat,tz\n")
    for lng in [lng * 1.0 for lng in lng_range]:
        lst = []
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
                                        tz = get_tz(lng_, lat_)
                                        if tz:
                                            lst.append({'lng': lng_, 'lat': lat_, 'tz': tz})
                                    t.update()
        tbl = pa.Table.from_pylist(lst)
        writer.write_table(tbl)
t.close()