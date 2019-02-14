#! /usr/bin/env python3
"""
Last Updated: 02/14/2019

usage: ncbi-assembly.py [-h] [--retmax INT]
                        [--assembly_level {complete,chromosome,scaffold,contig,all}]
                        [--delay INT] [--filter_columns] [--validate_filter]
                        [--report_readme] [--dry_run]
                        FILTER OUTPUT

Query NCBI and download FASTA sequences individually.

positional arguments:
  FILTER                Columns to filter. Expects COLUMN_NAME=VALUE format.
                            Example: "taxid=1280".
                        Multiple filters can be given using a ";" as the separator.
                            Example: "taxid=1280;infraspecific_name=USA300".
  OUTPUT                Directory to download assemblies to to.

optional arguments:
  -h, --help            show this help message and exit
  --retmax INT          Maximum number of assemblies to download. (Default: 1000)
  --assembly_level {complete,chromosome,scaffold,contig,all}
                        Determines the level of assemblies to download. See NCBI's
                        README (--report_readme) for more information about each level
  --delay INT           Delay between downloads. (Default: 3 seconds)
  --filter_columns      Print a list of filterable columns.
  --validate_filter     Print the expected filter to be applied.
  --report_readme       Print NCBI's assembly report README for filterable columns.
  --dry_run             Run as normal, but do not download any data.


MIT License

Copyright (c) 2019 Robert A. Petit III

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import requests
FILTER_COLUMNS = [
    'assembly_accession', 'bioproject', 'biosample', 'wgs_master',
    'refseq_category', 'taxid', 'species_taxid', 'organism_name',
    'infraspecific_name', 'isolate', 'version_status', 'assembly_level',
    'release_type', 'genome_rep', 'seq_rel_date', 'asm_name', 'submitter',
    'gbrs_paired_asm', 'paired_asm_comp', 'ftp_path', 'excluded_from_refseq',
    'relation_to_type_material'
]


def parse_filters(input_filters):
    """Parse input filters and validate them."""
    from collections import OrderedDict
    parsed_filter = OrderedDict()
    invalid = False
    for f in input_filters.split(";"):
        if '=' not in f:
            invalid = True
            parsed_filter[f] = f'ERROR: INVALID COLUMN NAME, OR NO VALUE GIVEN'
        else:
            column, value = f.split("=")
            parsed_filter[column] = value
            if column not in FILTER_COLUMNS:
                invalid = True
                parsed_filter[column] = f'{value} <-- ERROR: INVALID COLUMN NAME'

    return [parsed_filter, invalid]


def print_report_readme():
    """Print out the assembly report readme from NCBI."""
    r = requests.get(
        'https://ftp.ncbi.nlm.nih.gov/genomes/README_assembly_summary.txt'
    )
    print(r.text)


def download_report(column_filters):
    """Download latest bacteria assembly report from NCBI."""
    r = requests.get(
        'https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt'
    )
    col_names = None
    report = []
    for line in r.text.split('\n'):
        passes = []

        if line.startswith('# assembly_accession'):
            col_names = line.lstrip("# ").split('\t')
        elif col_names and line:
            row_values = dict(zip(col_names, line.split('\t')))
            for column, value in column_filters.items():
                if value.lower() in row_values[column].lower():
                    passes.append(True)
                elif column == 'assembly_level' and value == 'all':
                    passes.append(True)
                else:
                    passes.append(False)

            if len(passes) == sum(passes):
                report.append(row_values)

    return report


def download_assembly(assembly_path, output_path, debug=False):
    """Downloads all files associated with an Assembly accession."""
    import subprocess
    p = subprocess.Popen(
        ['rsync', '--copy-links', '--recursive', '--times', '--verbose',
         assembly_path, output_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    out, err = p.communicate()

    for line in out.decode("utf-8").split('\n'):
        print(f"[rsync STDOUT] {line}")

    for line in err.decode("utf-8").split('\n'):
        print(f"[rsync STDERR] {line}")


if __name__ == '__main__':
    import argparse as ap
    import json
    import os
    import sys
    import time

    parser = ap.ArgumentParser(
        prog='ncbi-assembly.py', conflict_handler='resolve',
        description="Query NCBI and download FASTA sequences individually.",
        formatter_class=ap.RawTextHelpFormatter
    )

    parser.add_argument(
        'filter', type=str, metavar="FILTER",
        help=('Columns to filter. Expects COLUMN_NAME=VALUE format.\n'
              '\tExample: "taxid=1280".\n'
              'Multiple filters can be given using a ";" as the separator.\n'
              '\tExample: "taxid=1280;infraspecific_name=USA300".')
    )
    parser.add_argument('outdir', type=str, metavar="OUTPUT",
                        help='Directory to download assemblies to to.')
    parser.add_argument(
        '--retmax', default=1000, type=int, metavar="INT",
        help='Maximum number of assemblies to download. (Default: 1000)'
    )
    parser.add_argument(
        '--assembly_level', default="complete",
        choices=['complete', 'chromosome', 'scaffold', 'contig', 'all'],
        help=("Determines the level of assemblies to download. See NCBI's \n"
              "README (--report_readme) for more information about each level")
    )
    parser.add_argument(
        '--delay', default=3, type=int, metavar="INT",
        help='Delay between downloads. (Default: 3 seconds)'
    )
    parser.add_argument(
        '--filter_columns', action="store_true",
        help="Print a list of filterable columns."
    )
    parser.add_argument(
        '--report_readme', action="store_true",
        help="Print NCBI's assembly report README for filterable columns."
    )
    parser.add_argument(
        '--validate_filter', action="store_true",
        help="Print the expected filter to be applied."
    )
    parser.add_argument(
        '--report_readme', action="store_true",
        help="Print NCBI's assembly report README for filterable columns."
    )
    parser.add_argument('--dry_run', action="store_true",
                        help='Run as normal, but do not download any data.')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    if args.report_readme:
        print_report_readme()
        sys.exit(0)
    elif args.filter_columns:
        print(sorted(FILTER_COLUMNS))
        sys.exit(0)

    filters, invalid_filter = parse_filters(args.filter)
    if invalid_filter:
        print("Given filter contains errors, please check...", file=sys.stderr)
        print(json.dumps(filters, indent=4), file=sys.stderr)
        sys.exit(1)
    elif args.validate_filter:
        print("The following filter will be applied:")
        print(json.dumps(filters, indent=4))
        sys.exit(0)

    print("Downloading Bacteria Assembly Report")
    filters['assembly_level'] = args.assembly_level
    report = download_report(filters)
    print(f"Found {len(report):,} assemblies.\n")
    print("Downloading assemblies...")
    for i, row in enumerate(report):
        print(f'Working on {row["assembly_accession"]} ({i+1} of {len(report)})')
        if not args.dry_run:
            if not os.path.exists(args.outdir):
                os.makedirs(args.outdir)
            output_dir = f'{args.outdir}/{row["assembly_accession"]}'
            os.makedirs(output_dir, exist_ok=True)
            assembly_path = row['ftp_path'].replace('ftp://', 'rsync://')
            download_assembly(assembly_path, output_dir)
            time.sleep(args.delay)

    print("Outputting assembly_summary.txt...")
    output = '{0}/assembly_summary.txt'.format(args.outdir)
    with open(output, 'w') as fh:
        fh.write("{0}\n".format('\t'.join(FILTER_COLUMNS)))
        for row in report:
            fh.write('{0}\n'.format(
                '\t'.join([row[c] for c in FILTER_COLUMNS])
            ))
