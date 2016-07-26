import argparse
import sys

import pkg_resources

import odl_cfg_analysis


def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Analyze odl config dependencies")

    default_style = pkg_resources.resource_filename('odl_cfg_analysis', 'graph_style')
    parser.add_argument('--graph-style', metavar='file', default=default_style, type=argparse.FileType('r'))

    parsed = parser.parse_args(args)
    print(vars(parsed))

    odl_cfg_analysis.perform_analysis(vars(parsed))
