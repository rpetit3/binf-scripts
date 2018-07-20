#! /usr/bin/env python3
"""
Last Updated: 07/10/2018

usage: ncbi-download.py [-h] [--db DB] [--email EMAIL] [--api_key API_KEY]
                        [--retmax INT] [--dry_run]
                        QUERY OUTPUT

Query NCBI and download FASTA sequences individually.

positional arguments:
  QUERY              Query to search.
  OUTPUT             Directory to write FASTA output to.

optional arguments:
  -h, --help         show this help message and exit
  --db DB            NCBI database to query. (Default: nuccore
  --email EMAIL      Email address for NCBI to contact in case of issues.
  --api_key API_KEY  NCBI API key to increase max queries per second.
  --retmax INT       Maximum number of genomes to download. (Default: 1000)
  --dry_run          Run as normal, but do not download any data.


MIT License

Copyright (c) 2018 Robert A. Petit III

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
import os
import time
import argparse as ap
from Bio import Entrez
import sys
Entrez.tool = "ncbi-download.py"
RETTYPE = 'fasta'
RETMODE = 'text'


if __name__ == '__main__':
    parser = ap.ArgumentParser(
        prog='ncbi-download.py', conflict_handler='resolve',
        description="Query NCBI and download FASTA sequences individually."
    )

    parser.add_argument('query', type=str, metavar="QUERY",
                        help='Query to search.')
    parser.add_argument('outdir', type=str, metavar="OUTPUT",
                        help='Directory to write FASTA output to.')
    parser.add_argument('--db', type=str, default='nuccore',
                        help='NCBI database to query. (Default: nuccore')
    parser.add_argument(
        '--email', type=str,
        help='Email address for NCBI to contact in case of issues.'
    )
    parser.add_argument(
        '--api_key', type=str,
        help='NCBI API key to increase max queries per second.'
    )
    parser.add_argument(
        '--retmax', default=1000, type=int, metavar="INT",
        help='Maximum number of genomes to download. (Default: 1000)'
    )
    parser.add_argument('--dry_run', action="store_true",
                        help='Run as normal, but do not download any data.')

    args = parser.parse_args()
    if args.email:
        Entrez.email = args.email

    if args.api_key:
        Entrez.api_key = args.api_key

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    handle = Entrez.esearch(db=args.db, retmax=args.retmax, term=args.query)
    esearch = Entrez.read(handle)
    print("Database: {0}".format(args.db))
    print("Max Records: {0}".format(args.retmax))
    print("Output Directory: {0}".format(args.outdir))
    print("Query: {0}".format(args.query))
    print("----------")
    print("Searching for records...")
    print("\tFound {0} records.\n".format(esearch["Count"]))
    print("Downloading records...")

    accessions = []
    for uuid in esearch['IdList']:
        handle = Entrez.esummary(db=args.db, id=uuid)
        esummary = Entrez.read(handle)
        accessions.append(esummary[0]["Caption"])
        print('\tDownloading {0}'.format(esummary[0]["Caption"]))
        if not args.dry_run:
            fasta_output = '{0}/{1}.fasta'.format(
                args.outdir, esummary[0]["Caption"]
            )
            if not os.path.isfile(fasta_output):
                efetch = Entrez.efetch(db=args.db, id=uuid, rettype=RETTYPE,
                                       retmode=RETMODE)

                # Write fasta output
                with open(fasta_output, 'w') as fh:
                    fh.write(efetch.read())
                efetch.close()
                # Query delays are automatically enforced by Biopython
            else:
                print('\tSkip existing {0}'.format(esummary[0]["Caption"]))

    if not args.dry_run:
        print("Outputting list of completed genomes.")
        output = '{0}/completed-genomes.txt'.format(args.outdir)
        with open(output, 'w') as fh:
            fh.write('\n'.join(accessions))
