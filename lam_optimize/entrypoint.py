import argparse
import json
from pathlib import Path
from typing import List, Optional

from dflow import Workflow, download_artifact
from lam_optimize.main import relax_run
from lam_optimize.relaxer import Relaxer
from lam_optimize.workflow import get_relax_workflow


def main_parser():
    parser = argparse.ArgumentParser(
        description="A crystal structure optimization tool built on top of ASE",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        title="Valid subcommands", dest="command")

    parser_relax = subparsers.add_parser(
        "relax",
        help="Relax structures",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_relax.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="input cif folder",
    )
    parser_relax.add_argument(
        "-t",
        "--type",
        type=str,
        choices=["DP", "mace"],
        default="DP",
        help="task type",
    )
    parser_relax.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        help="model path",
    )
    parser_relax.add_argument(
        "--skip-check-convergence",
        action="store_true",
        help="skip checking convergence",
    )
    parser_relax.add_argument(
        "--skip-check-duplicate",
        action="store_true",
        help="skip checking duplicate",
    )
    parser_relax.add_argument(
        "-o",
        "--output",
        type=str,
        default="results.json",
        help="output path",
    )

    parser_submit = subparsers.add_parser(
        "submit",
        help="Submit a workflow to relax structures",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_submit.add_argument(
        "CONFIG",
        help="workflow config",
    )
    parser_submit.add_argument(
        "-i",
        "--input",
        type=str,
        nargs='+',
        required=True,
        help="input cif folders",
    )
    parser_submit.add_argument(
        "-t",
        "--type",
        type=str,
        choices=["DP", "mace"],
        default="DP",
        help="task type",
    )
    parser_submit.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        help="model path",
    )
    parser_submit.add_argument(
        "--skip-check-convergence",
        action="store_true",
        help="skip checking convergence",
    )
    parser_submit.add_argument(
        "--skip-check-duplicate",
        action="store_true",
        help="skip checking duplicate",
    )

    parser_download = subparsers.add_parser(
        "download",
        help="Download results from a relax workflow",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_download.add_argument(
        "ID",
        help="workflow ID",
    )
    parser_download.add_argument(
        "-o",
        "--output",
        type=str,
        default=".",
        help="output path",
    )
    return parser


def parse_args(args: Optional[List[str]] = None):
    """Commandline options argument parsing.

    Parameters
    ----------
    args : List[str]
        list of command line arguments, main purpose is testing default option
        None takes arguments from sys.argv
    """
    parser = main_parser()
    parsed_args = parser.parse_args(args=args)
    if parsed_args.command is None:
        parser.print_help()
    return parsed_args


def main():
    args = parse_args()

    if args.command == "relax":
        if args.type == "DP":
            relaxer = Relaxer(Path(args.model))
        elif args.type == "mace":
            relaxer = Relaxer("mace")
        res_df = relax_run(Path(args.input), relaxer, check_convergence=(not args.skip_check_convergence),
                           check_duplicate=(not args.skip_check_duplicate))
        res_df.to_json(args.output)
    elif args.command == "submit":
        with open(args.CONFIG, "r") as f:
            config = json.load(f)
        wf = get_relax_workflow(config["relax"], args.input, args.type, args.model)
        wf.submit()
    elif args.command == "download":
        wf = Workflow(id=args.ID)
        step = wf.query_step(name="relax", phase="Succeeded")[0]
        download_artifact(step.outputs.artifacts["res"], path=args.output)
        download_artifact(step.outputs.artifacts["relaxed_cifs"], path=args.output)
        download_artifact(step.outputs.artifacts["unconverged_cifs"], path=args.output)


if __name__ == "__main__":
    main()
