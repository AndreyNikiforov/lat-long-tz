import sys
import click
import pyarrow.parquet as pq

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}

@click.command(context_settings=CONTEXT_SETTINGS, no_args_is_help=True)
@click.argument("filename", type=click.STRING)
def main(filename):
    """Print schema of parquet file

        FILENAME file pattern to file
    """
    schema = pq.read_schema(filename)

    print(schema)
    return 0


if __name__ == "__main__":
    sys.exit(main())
