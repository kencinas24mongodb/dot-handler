from datetime import datetime
from pathlib import Path
from typing import List

from typer import Argument
from typer import Option
from typer import Typer
from typer import echo

from engine import configuration
from engine import storage
from engine.configuration import ConfCommand
from engine.finder import find_dot_definition_from_file
from engine.finder import store_dot_definitions
from engine.lookup import lookup_dot_usages_from_file
from engine.lookup import store_dot_usages
from engine.utils import DDLObjectTypeSupported

app = Typer(add_help_option=True)


@app.command()
def find(dots: DDLObjectTypeSupported = Argument(..., case_sensitive=False, help="DDL Object type supported"),
         src_input_path: Path = Argument(..., exists=True, dir_okay=True, readable=True,
                                         help="Input source path for files"),
         src_file_patterns: List[str] = Option(["*.sql"], "-p", "--pattern", help="File pattern to search the objects",
                                               show_default=True),
         ds_name: str = Option("main", "-d", "--dataset", help="Dataset name to save the results", show_default=True)):
    # Flat the filepaths by the patterns
    src_filepaths = []
    for pattern in src_file_patterns:
        src_filepaths += src_input_path.rglob(pattern)

    dot_table = find_dot_definition_from_file(dots, src_filepaths)
    if len(dot_table) > 0:
        store_dot_definitions(ds_name, dots, dot_table)


@app.command()
def lookup(dots: DDLObjectTypeSupported = Argument(..., case_sensitive=False, help="DDL Object type supported"),
           src_input_path: Path = Argument(..., exists=True, readable=True, help="Input source path for files"),
           src_file_patterns: List[str] = Option(["*.sql"], "-p", "--pattern",
                                                 help="File pattern to search the objects", show_default=True),
           ds_name: str = Option("main", "-d", "--dataset", help="Dataset name to save the results",
                                 show_default=True),
           do_name: str = Option("*", "-n", "--name", help="DDL Object name to lookup")):
    if src_input_path.is_file():
        echo(f"[INFO] ⚠️ A file was given as src_path: {src_input_path.absolute()}")
        src_file_patterns = [src_input_path.name]
        src_input_path = src_input_path.parent

    to_store_calls = {}
    for pattern in src_file_patterns:
        for src_file in src_input_path.rglob(pattern):
            to_store_calls[src_file] = lookup_dot_usages_from_file(dots, do_name, ds_name, src_file)

    store_dot_usages(ds_name, dots, to_store_calls)


@app.command()
def config(command: ConfCommand = Argument(..., case_sensitive=False), conf_key: str | None = Argument(None),
           value: str | None = Argument(None)):
    match command:
        case ConfCommand.SET:
            if not conf_key:
                echo("[ERROR] ❌ Missing configuration key!")
                exit(1)

            if not value:
                echo("[ERROR] ❌ Missing value for configuration!")
                exit(1)

            configuration.set_config(conf_key, value)

        case ConfCommand.GET:
            if not conf_key:
                echo("[ERROR] ❌ Missing configuration key!")
                exit(1)
            value = configuration.get_config(conf_key)
            echo(f"⚙️ {conf_key}: {value if value is not None else 'NULL'}")

        case ConfCommand.LIST:
            for key, conf in configuration.load_conf().items():
                echo(f"⚙️  {key}: {conf if conf is not None else 'NULL'}")

        case ConfCommand.CLEAR:
            if not conf_key:
                echo("[ERROR] ❌ Missing configuration key!")
                exit(1)
            configuration.set_config(conf_key, None)


# Dataset
conf_sub_app = Typer()


# app ds show 'definitions.views' -o foo/bar/biz.log -d foo
@conf_sub_app.command(name="show")
def ds_show(query: str = Argument(...), ds_name: str = Option("main", "-d", "--dataset"),
            output: str = Option("<STDOUT>", "-o", "--output")):
    if not storage.exists(ds_name):
        echo(f"[ERROR] ❌ Dataset {ds_name} does not exist!")
        exit(1)

    q_parts = query.lower().split(".")
    if len(q_parts) != 2:
        echo(f"[ERROR] ❌ Given query invalid, should be '<collection>.<table>': {query}")
        exit(1)
    else:
        q_collection, q_table = q_parts[0], q_parts[1]

    fp_out = None
    if output != "<STDOUT>":
        fp_out = Path(output)
        fp_out.parent.mkdir(parents=True, exist_ok=True)

        if fp_out.exists() and not fp_out.is_file():
            echo(f"[ERROR] ❌ Given output path is not a file: {fp_out.absolute()}")
            exit(1)

        if not fp_out.exists():
            fp_out.touch()
        else:
            fp_out.unlink()
            fp_out.touch()

    def pecho(message: str):
        echo(message)
        if fp_out:
            with fp_out.open("a+", encoding='utf-16') as fp:
                echo(message, file=fp)

    ds = storage.load_dataset(ds_name)

    collection: dict | None = ds.get(q_collection, None)
    if not collection:
        echo(f"f[ERROR] ❌ No collection found by name: {q_collection}")
        exit(1)

    table: dict | None = collection.get(q_table, None)
    if not table:
        echo(f"[ERROR]  ❌ No table found by name: {q_table}")
        exit(1)

    # Print header
    pecho(f"💾 Dataset:    {ds_name}")
    pecho(f"💾 Collection: {q_collection}")
    pecho(f"💾 Table:      {q_table}")
    pecho(f"{'=' * 80}")

    match q_collection:
        case 'definitions':
            for key, definition in table.items():
                pecho(f"🗝️ {key}")
                pecho(f"📄 Name:      {definition['name']}")
                pecho(f"📄 Schema:    {definition['schema']}")
                pecho(f"📄 Filepath:  {definition['filepath']}")
                pecho(f"📄 Line:      {definition['line']}")
                pecho(f"📄 Timestamp: {datetime.fromtimestamp(definition['timestamp'])}")
                pecho(f"{'-' * 80}")
        case 'usages':
            pecho(f"📄 Generation: {collection.get('generation', 0)}")
            pecho(f"{'-' * 80}")
            for key, usages in table.items():
                if key == 'generation': continue
                pecho(f"🗝️ {key}: {len(usages)}")
                for i, usage in enumerate(usages):
                    pecho(f"✅ Usage {i + 1}")
                    pecho(f"    📄 Filepath:  {usage['filepath']}")
                    pecho(f"    📄 Line:      {usage['line']}")
                    pecho(f"    📄 Timestamp: {datetime.fromtimestamp(usage['timestamp'])}")

                    if i < len(usages) - 1:
                        pecho(f"{'.' * 80}")

                pecho(f"{'-' * 80}")




@conf_sub_app.command(name="clear")
def ds_clear(ds_name: str  = Option("main", "-d", "--dataset"),
             target: str = Option("all", "-t", "--target")):
    if not storage.exists(ds_name):
        echo(f"[ERROR] ❌ Dataset {ds_name} does not exist!")
        exit(1)

    if target == "all":
        storage.rm(ds_name)
        echo(f"[INFO] 🗑️ Dataset {ds_name} was deleted!")
        exit(0)

    ds = storage.load_dataset(ds_name)

    t_parts = target.lower().split(".")

    t_collection = t_parts[0]

    collection: dict | None = ds.get(t_collection, None)
    if not collection:
        echo(f"[WARNING] ⚠️ Collection {t_collection} does not exists in dataset {ds_name}!")
        exit(0)

    if len(t_parts) == 1:
        del ds[t_collection]
        echo(f"[INFO] 🗑️ Collection {t_collection} was deleted from dataset {ds_name}!")
    else:
        if len(t_parts) != 2:
            echo(f"[ERROR] ❌ Target is not valid for deletion, expected '<collection>[.<table>]', got: {target}")
            exit(1)

        t_table = t_parts[1]
        if t_table not in collection:
            echo(f"[WARNING]  Table {t_table} does not exist in collection {t_collection} in dataset {ds_name}")
            exit(0)

        del collection[t_table]
        ds[t_collection] = collection
        echo(f"[INFO] 🗑️ Table {t_table} was deleted from collection {t_collection} in dataset {ds_name}")

    storage.save_dataset(ds, ds_name)

if __name__ == '__main__':
    # How to use
    # --------------------------------------------------------------
    # Set configurations:
    #   app config set 'my.conf' my-value
    # Get configurations:
    #   app config get 'my-conf'
    # List configurations:
    #   app config list
    # Clear configurations:
    #   app config clear 'my.conf'
    # --------------------------------------------------------------
    # Find supported DDL objects types (aka: dots) definitions in files:
    #   app find <dots> <source files input folder path> -d <dataset: main> -p <source input file pattern>
    #   Examples:
    #       - Find 'views' in 'D:\oracle\migration' in files like '*.pls' and '*.sql'
    #         app find views D:\oracle\migration -p '*.pls' -p '*.sql'
    #       - Find 'views' in '/home/john.smith/work/migration' in files '*.sql' and save it in a dataset named 'employees'
    #         app find views /home/john.smith/work/migration -d employees
    # --------------------------------------------------------------
    # Look up supported DDL object types (aka: dots) usages in files:
    #   app lookup <dots> <source files input folder path> -d <dataset: main>  -p <source input file pattern> -n <dots name>
    #   Examples:
    #       - Lookup 'views' in '..\migrations\v2.0.1' in files '*.sql'
    #         app lookup views ..\migrations\v2.0.1
    #       - Lookup the view 'F_VIEW_DX' in file '/home/company/migrations/some-file.sql'
    #         app lookup views /home/company/migrations/some-file.sql -n F_VIEW_DX
    #       - Lookup 'views' in path '../migrations/baseline' and store the results in dataset 'baseline'
    #         app lookup views ../migrations/baseline -d baseline
    # --------------------------------------------------------------
    # Show dataset information, where query must be a <collection>.<table> string:
    #   app ds show <query> -d <dataset> -o <output>
    #   Examples:
    #       - Show all definitions of views
    #         app ds show 'definitions.views'
    #       - Show all usages of views and output to a file
    #         app ds show 'usages.views' -o usages.log
    #       - Show all usages of views using the definitions in the dataset "rhx32" and output to a file
    #         app ds show 'usages.views' -d rhx32 -o ../dumps/rhx32-views-usages.dump
    # --------------------------------------------------------------
    # Clear data set information
    #   app ds clear -d <dataset> -t <target>
    #   Examples:
    #       - Clear all content of main dataset
    #         app ds clear
    #       - Clear collection 'definitions' from dataset 'baseline'
    #         app ds clear -d baseline -t definitions
    #       - Clear table 'views' from collection 'usages' from dataset 'r2d2'
    #         app ds clear -d r2d2 -t 'usages.views'
    app.add_typer(conf_sub_app, name="ds")
    app()
