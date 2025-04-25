# DOT Handler

DOT (DDL Object Type) handler console client to find, lookup and generate reports of DOTs in your SQL files.

---

## 1. Prerequisites

- `python` version > 3.12

## 2. Installation

This project has only 1 dependency listed in the [requirements.txt](./requirements.txt):

1. `typer` for client console applications

To install the dependency, first of all you have to create a `virtual environment`:

```shell
python -m venv venv/
```

Once you have the `virtual environment`, run:

```shell
# For UNIX-Like OS such as Ubuntu, Linux Mint, MacOS, OpenBSD, etc...
source venv/bin/activate
```

```commandline
REM For Windows based systems (cmd):
.\venv\Scripts\activate.bat
```

```powershell
# For Windows base systems (PowerShell):
.\venv\Scripts\Activate.ps1
```

(Optional) Before installing anything, you may want to upgrade your `pip`:

```shell
python -m pip install --upgrade pip
```

And now you can install the dependencies:

```shell
python -m pip install -r requirements.txt
```

## 3. Usage

This application provides you basic commands to handle:

1. `config`: to configurate your application.
2. `ds`: to manipulate the dataset and create reports or dumps.
3. `find`: to find definitions of DOTs in your files.
4. `lookup`: to lookup for usages of your definitions in your files.

## 3.1. Usage of: `config` command

### Action: `set`

Changes the value of the given `key` configuration with the given `value`.

| Parameter | Type         | Data Type | Required | Default |
|-----------|--------------|-----------|----------|---------|
| `key`     | _positional_ | string    | *yes*    | N/A     |
| `value`   | _positional_ | string    | *yes*    | N/A     |

Examples:

```shell
# Change the collision policy to 'keep-original'
python main.py config set 'policy.collision' keep-original
```

```shell
# Sets the default schema to 'employees'
python main.py config set 'db.schema' employees
```

### Action: `get`

Prints the value of the given `key` configuration. If the `key` does not exist, shows `'NULL'`.

| Parameter | Type         | Data Type | Required | Default |
|-----------|--------------|-----------|----------|---------|
| `key`     | _positional_ | string    | *yes*    | N/A     | 

Examples:

```shell
# Gets the current default schema
python main.py config get 'db.schema'
```

### Action: `list`

Prints all the keys and values of the current configurations.
Examples:

```shell
python main.py config list
```

### Action: `clear`

Deletes a configuration value by the given `key`.

| Parameter | Type         | Data Type | Required | Default |
|-----------|--------------|-----------|----------|---------|
| `key`     | _positional_ | string    | *yes*    | N/A     | 

Examples:

```shell
python main.py config clear 'custom.configuration'
```

## 3.2. Usage of: `ds` command

### Action: `show`

Prints reports of the given `query` to the given `output` based on the data from the given `dataset`.

The `query` argument is a string that should have the following structure:
`<collection>.<table>`.

For instance:
> 'definitions.views'

To know more about collection and tables, [go here](#4-types-and-datasets)

| Parameter | Type             | Data Type | Required | Default    |
|-----------|------------------|-----------|----------|------------|
| `query`   | _positional_     | string    | *yes*    | N/A        |
| `output`  | `-o` `--output`  | string    | no       | `<STDOUT>` |
| `dataset` | `-d` `--dataset` | string    | no       | `main`     |

Examples:

```shell
# Show all the usages of views
python main.py ds show 'usages.views'
```

```shell
# Show all the definitions of views in the dataset 'commerces'
python main.py ds show -d commerces 'definitions.views'
```

```shell
# Shows and prints a report file for all usages of views using the dataset 'derivatives'
python main.py ds show -o ./reports/derivatives.dump.txt -d derivatives 'usages.views'
```

### Action: `clear`

Deletes the given `target` in the given `dataset`.
If no `target` is given the whole dataset will be erased.

A `target` can be: `<collection>` or `<collection>.<table>`.

| Parameter | Type             | Data Type | Required | Default |
|-----------|------------------|-----------|----------|---------|
| `target`  | `-t` `--target`  | string    | *no*     | `all`   |
| `dataset` | `-d` `--dataset` | string    | *no*     | `main`  |

Examples:

```shell
# Deletes the main dataset
python main.py ds clear 
```

```shell
# Deletes the definitions of views in the main dataset
python main.py ds clear -t 'definitions.views' 
```

```shell
# Deletes the collection 'usages' from the dataset 'purchases'
python main.py ds clear -t 'usages' -d purchases 
```

## 3.3. Usage of: `find` command

`find` will try to search the definitions of the specified `dots` (DDL Object Type) in the given `source input path`
files,
filtered out by the given `source input file patterns`. And then, it will dump all the information into the given
`dataset`.

| Parameter                    | Type             | Data Type                     | Required | Default |
|------------------------------|------------------|-------------------------------|----------|---------|
| `dots`                       | _positional_     | [DOTS](#4-types-and-datasets) | *yes*    | N/A     |
| `source input path`          | _positional_     | string                        | *yes*    | N/A     |
| `source input file patterns` | `-p` `--pattern` | list[string]                  | *no*     | `*.sql` |
| `dataset`                    | `-d` `--dataset` | string                        | *no*     | `main`  |

Examples:

```shell
# Find all the definitions of views in the path /home/ben/migrations/v12
python main.py find views /home/ben/migrations/v12
```

```shell
# Find all the definitions of views in the files with extension .pls and .sql in the path C:\Oracle\HSBC\rpnoc-project\migrations  
python main.py find views C:\Oracle\HSBC\rpnoc-project\migrations -p *.pls -p *.sql
```

```shell
# Find all the definitions of views in the path ../../django-app/db/baseline and dump it into the dataset django-app  
python main.py find views ../../django-app/db/baseline -d django-app
```

## 3.4. Usage of: `lookup` command

`lookup` will try to search the usages of the specified `dots` (DDL Object Type) in the given `source input path`
files, filtered out by the given `source input file patterns`. And then, it will dump all the information into the given
`dataset`.

The `source input path` can be not only a folder path but a file path, too. In this case,
the parameter `source input file patterns` will be ignored.

Additionally, you can set a new parameter `dot name`, which will look up only for that name. If no value is given,
it will default to `*`: meaning to search for everything.

| Parameter                    | Type             | Data Type     | Required | Default |
|------------------------------|------------------|---------------|----------|---------|
| `dots`                       | _positional_     | [DOTS](#DOTS) | *yes*    | N/A     |
| `source input path`          | _positional_     | string        | *yes*    | N/A     |
| `source input file patterns` | `-p` `--pattern` | list[string]  | *no*     | `*.sql` |
| `dataset`                    | `-d` `--dataset` | string        | *no*     | `main`  |
| `dot name`                   | `-n` `--name`    | string        | *no*     | `*`     |

Examples:

```shell
# Look up for every view usage in the path /home/hanson/scripts using the dataset 'hanson'
python main.py lookup views /home/hanson/scripts -d hanson
```

```shell
# Look up for every view usage in the file V2_PDL_DOWNLOAD_PROCEDURE.pls
python main.py lookup views D:\Oracle\base\V2_PDL_DOWNLOAD_PROCEDURE.pls
```

```shell
# Look up only the usages of the view 'VW_INSTALLATION_PACKAGES' in the folder /app/db/v23 filtering out by file extensions *.sql and *.pls  
python main.py lookup views /app/db/v23 -p *.sql -p *.pls -n VW_INSTALLATION_PACKAGES
```

## 4. Types and Datasets

### 4.1. Supported DDL Object Type aka `DOTS` <a id="DOTS"></a>

In this early version, we only support `views`, but it's planned to extend it to others like `tables`, `procedures`,
etc.

### 4.2. Datasets

Datasets are JSON files located in: `~/.mdb-tools/dot-handler/dataset` which holds all the information processed by this
app. 

These files have a structure like:
```json
{
  "collection": {
    "table": {}
  }
}
```

### 4.3. Datasets: Collections
By the time, only 2 collections are managed by the app:
1. `definitions`: created when the `find` command is run
2. `usages`: created when the `lookup` command is run

### 4.3. Datasets: Tables 
Tables are objects containing entries of different types. By now, the tables refer to the DOT which was run 
for the `find` or `lookup`commands. 

## 5. Bugs and known issues
This is an early version of the app, so it can have some issues and bugs. Or at least, something that could be enhanced.
Please, feel free to report any bug, issue or enhancement to me at my [email](mailto:kevin.encinas@mongodb.com) or open 
an issue here in the repository!
