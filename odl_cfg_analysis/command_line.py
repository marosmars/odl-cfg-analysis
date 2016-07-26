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
    parser.add_argument('--graph-style', metavar='FILE', default=default_style, type=argparse.FileType('r'),
                        help="Graph style dictionary file providing graph style e.g. " +
                             "https://github.com/marosmars/odl-cfg-analysis/blob/master/odl_cfg_analysis/graph_style")
    parser.add_argument('--graph-format', metavar='OUTPUT_FORMAT', default="jpeg",
                        help="See available at http://www.graphviz.org/doc/info/output.html")
    parser.add_argument('--graph-file-dest', metavar='GENERATED_GRAPH_NAME', default="dependencies",
                        help="Just the name of graph output file")
    parser.add_argument("--paths-to-analyze", required=True, nargs="+",
                        help="Files or folders containing ODL XML configuration", metavar="FILES/FOLDERS")
    parser.add_argument("--highlight-modules", nargs="+", default=[],
                        help="Module names to be highlighted + their dependencies recursively in the resulting graph",
                        metavar="MODULE_NAMES")

    parsed = parser.parse_args(args)
    odl_cfg_analysis.perform_analysis(vars(parsed))
