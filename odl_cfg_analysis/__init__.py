from odl_cfg_analysis import analyze


def perform_analysis(args):
    analyze.analyze(args['graph_style'], args["graph_format"], args["graph_file_dest"], args["paths_to_analyze"],
        args["highlight_modules"])
