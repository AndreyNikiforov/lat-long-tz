from itertools import islice
import random
import onnxruntime as ort
import click
import sys
from timezonefinder import TimezoneFinder
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn,TransferSpeedColumn
import time
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

# pip install click timezonefinder rich onnxruntime cartopy matplotlib

tf = TimezoneFinder(in_memory=True)

def gen_lat_long():
    while(True):
        lng = random.uniform(-180.0, 180.0)
        lat = random.uniform(-90.0, 90.0)
        yield lat, lng

def get_tz(lng, lat, default):
    try:
        return tf.timezone_at(lng=lng, lat=lat)
    except:
        return default


# NAM y,x == lat,long
# left most 65.576472, -168.483307
# top most 71.349914, -156.705964
# bottom most 24.666625, -80.768467
# right most 47.264050, -52.116124
# SF Bay: 37.792000, -122.389002
def get_region(lat, lng):
    if 24.7 < lat and lat < 65.6 and \
        -168.5 < lng and lng < -52.1:
        return "NAM"
    return "Other"

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument("model", type=click.Path(exists=True))
@click.option("--limit", type=click.INT, default=1_000_000, help="Number of coordinates to try")
@click.option("--input-name", type=click.STRING, default="lng-lat", help="Input name of the model")
@click.option("--error-map", type=click.STRING, help="File name to export error map image")

def main(model, limit, input_name, error_map):
    """Calculates model accuracy

        MODEL onnx or ort file of the model

    """

    ort_sess = ort.InferenceSession(model)
    sliced = islice(gen_lat_long(), limit)
    counter = 0
    correct_count = 0
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.coastlines()
    with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TransferSpeedColumn()
        ) as progress:
        task_id = progress.add_task("Working...", total=limit)
        total_time_model = 0
        total_time_code = 0
        regions = {'NAM': {
            'counter': 0,
            'correct': 0,
        }}

        for lat, lng in sliced:
            start_time = time.perf_counter()
            outputs = ort_sess.run(None, {input_name: [[lng, lat]]})
            end_time = time.perf_counter()
            total_time_model += (end_time - start_time)

            pred_tz = outputs[0][0][0]

            start_time = time.perf_counter()
            true_tz = get_tz(lng, lat, "Error")
            end_time = time.perf_counter()
            total_time_code += (end_time - start_time)

            counter = counter + 1
            region = get_region(lat, lng)
            if region in regions:
                regions[region]['counter'] += 1
            if pred_tz == true_tz:
                correct_count = correct_count + 1
                if region in regions:
                    regions[region]['correct'] += 1
            else:
                ax.plot([lng], [lat],color='red', marker=",") 
            acc = correct_count/counter
            progress.update(task_id, completed=counter, description=f"Accuracy:{acc:.1%}")
        progress.print(f"Speed of the model inference: {counter/total_time_model:.1f} op/sec, and pure code: {counter/total_time_code:.1f} op/sec")
        progress.print(f"Accuracy of the model inference: {correct_count/counter:.1%}")
        for region in regions:
            if regions[region]['counter'] > 0:
                progress.print(f"Accuracy of the model inference for {region}: {regions[region]['correct']/regions[region]['counter']:.1%}")
            else:
                progress.print(f"No samples for {region}")
        if error_map:
            plt.savefig(error_map, dpi=300)
    return 0


if __name__ == "__main__":
    sys.exit(main())
