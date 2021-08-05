from .Database import Database
from sys import exit, stdout
from os.path import dirname, abspath, join
from os import mkdir, chdir
from datetime import datetime
import base64
import csv

"""
python3 croconvert.py -t html chechnya_proverki_ul_2012/
"""


def convert(args):
    """looks up template to convert to, parses the database and passes it to jinja2"""

    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        exit(
            "Fatal: Jinja templating engine not found. Install using pip install jinja2"
        )

    db = Database(args.dbdir)

    template_dir = join(dirname(dirname(abspath(__file__))), "templates")
    j2_env = Environment(loader=FileSystemLoader(template_dir))
    j2_templ = j2_env.get_template(args.template + ".j2")
    j2_templ.stream(db=db, base64=base64).dump(stdout)


def safename(name):
    return name.replace(':', '_').replace('/', '_').replace('\\', '_')


def cvs(args):
    """creates a directory with the current timestamp and in it a set of CVS or TSV
       files with all the tables found and an extra directory with all the files"""
    db = Database(args.dbdir)

    mkdir(args.outputdir)
    chdir(args.outputdir)

    filereferences = []

    # first dump all non-file tables
    for table in db.enumerate_tables(files=False):
        tablesafename = safename(table.tablename) + ".csv"

        with open(tablesafename, 'w', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([field.name for field in table.fields])

            # Record should be iterable over its fields, so we could use writerows
            for record in db.enumerate_records(table):
                writer.writerow([field.content for field in record.fields])

                filereferences.extend([field for field in record.fields if field.typ == 6])

    # Write all files from the file table. This is useful for unreferenced files
    for table in db.enumerate_tables(files=True):
        filedir = "Files-" + table.abbrev
        mkdir(filedir)

        for system_number, content in db.enumerate_files(table):
            with open(join(filedir,str(system_number)), "wb") as binfile:
                binfile.write(content)

    if len(filereferences):
        filedir = "Files-Referenced"
        mkdir(filedir)

    # Write all referenced files with their filename and extension intact
    for reffile in filereferences:
        if reffile.content:  # only print when file is not NULL
            filesafename = safename(reffile.filename) + "."  + safename(reffile.extname)
            content = db.get_record(reffile.filedatarecord)
            with open(join("Files-Referenced", filesafename), "wb") as binfile:
                binfile.write(content)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CRONOS database converter")
    parser.add_argument("--template", "-t", type=str, default="html",
                        help="output template to use for conversion")
    parser.add_argument("--outputdir", "-o", type=str, default="cronodump"+datetime.now().strftime("-%Y-%m-%d-%H-%M-%S-%f"), help="directory to create the dump in")
    parser.add_argument("dbdir", type=str)
    args = parser.parse_args()

    if args.template == "cvs":
        cvs(args)
    else:
        convert(args)

if __name__ == "__main__":
    main()
