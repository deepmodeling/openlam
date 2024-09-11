import os
from pathlib import Path
from typing import List, Literal, Optional

import lam_optimize
from dflow import Secret, Step, Workflow, upload_artifact
from dflow.plugins.dispatcher import DispatcherExecutor
from dflow.python import OP, Artifact, Parameter, PythonOPTemplate, Slices
from lam_optimize.main import relax_run
from lam_optimize.relaxer import Relaxer


@OP.function
def relax(
        cif_folder: Artifact(Path),
        type: str,
        model: Artifact(Path, optional=True),
        config: Parameter(dict, default={}),
) -> {
    "res": Artifact(Path),
    "relaxed_cifs": Artifact(Path),
    "unconverged_cifs": Artifact(Path),
}:
    if type == "DP":
        relaxer = Relaxer(model)
    elif type == "mace":
        relaxer = Relaxer("mace")
    res_df = relax_run(cif_folder, relaxer, **config)
    res_df.to_json("results.json")
    return {
        "res": Path("results.json"),
        "relaxed_cifs": Path("relaxed"),
        "unconverged_cifs": Path("unconverged"),
    }


def get_relax_workflow(
        config: dict,
        cif_folders: List[Path],
        type: Literal["DP", "mace"],
        model: Optional[Path] = None,
) -> Workflow:
    cif_art = upload_artifact(cif_folders)
    model_art = upload_artifact(model) if model is not None else None
    executor = config.get("executor")
    if executor is not None:
        executor = DispatcherExecutor(**executor)
    envs = {}
    if os.environ.get("OPENLAM_STRUCTURE_QUERY_URL"):
        envs["OPENLAM_STRUCTURE_QUERY_URL"] = os.environ.get("OPENLAM_STRUCTURE_QUERY_URL")
    if os.environ.get("BOHRIUM_ACCESS_KEY"):
        envs["BOHRIUM_ACCESS_KEY"] = Secret(os.environ.get("BOHRIUM_ACCESS_KEY"))
    step = Step(
        name="relax",
        template=PythonOPTemplate(
            relax,
            image=config["image"],
            python_packages=lam_optimize.__path__,
            slices=Slices(
                input_artifact=["cif_folder"],
                output_artifact=["res", "relaxed_cifs", "unconverged_cifs"],
                create_dir=True,
                **config.get("slices_config", {}),
            ),
            envs=envs,
            **config.get("template_config", {}),
        ),
        parameters={
            "type": type,
            "config": config.get("inputs", {}),
        },
        artifacts={
            "cif_folder": cif_art,
            "model": model_art,
        },
        executor=executor,
        with_param=range(len(cif_folders)),
        **config.get("step_config", {}),
    )
    wf = Workflow(config.get("name", "parallel-relax"))
    wf.add(step)
    return wf
