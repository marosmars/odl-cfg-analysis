import pkg_resources
from odl_cfg_analysis import analyze


def perform_analysis(args):
    analyze.analyze(
        args['graph_style']
    )
