# need to install torch, deepmd v3

from __future__ import annotations

from lam_optimize.relaxer import Relaxer
import logging
import pandas as pd
from pathlib import Path
from pymatgen.core import Structure
from tqdm import tqdm
import os


def relax_run(fpth:Path, relaxer: Relaxer, fmax: float=1e-4, steps:int = 200, traj_file:Path=None):
    """
    This is the main relaxation function

    Parameters:
    ----------
    fpth: Path
        The absolute file path to the folder containing `.cif` files.
    relaxer: Relaxer
        The relaxer for optimization
    fmax: float
        Force convergence criteria, in eV/A.
    steps: int
        Max steps allowed for relaxation.
    traj_file: Path
        Path to store relaxation trajectory.
    """
    print("\nStart to relax structures.\n")
    relax_results = {}
    cifs = fpth.rglob("*.cif")
    for cif in tqdm(cifs, desc="Relaxing"):
        fn = str(cif).split("/")[-1].split(".")[0]
        try:
            structure = Structure.from_file(cif)
        except Exception as e:
            logging.info(f"CIF error: {repr(e)}")
            structure = None
        if structure is not None:
            try:
                if traj_file is not None:
                    outpath = str(os.path.join(str(traj_file),fn ))
                else:
                    outpath = None
                result = relaxer.relax(structure, fmax=1e-4, steps=steps, traj_file=outpath)
                relax_results[fn] = {
                    f"final_structure": result["final_structure"],
                    "final_energy": result["trajectory"].energies[-1],
                }

            except Exception as exc:
                    logging.info(f"Failed to relax {fn}: {exc!r}")
        else:
            pass
    df_out = pd.DataFrame(relax_results).T
    print("\nSaved to df.\n")
    return df_out

def single_point(fpth:Path, relaxer: Relaxer):
    """
    This function performs single point evaluation

    Parameters:
    ----------
    fpth: Path
        The absolute file path to the folder containing `.cif` files.
    relaxer: Relaxer
        The relaxer for optimization
    """
    print("\nStart to evaluate structures.\n")

    calculator = relaxer.calculator
    adaptor = relaxer.ase_adaptor
    eval_results = {}
    cifs = fpth.rglob("*.cif")
    for cif in tqdm(cifs, desc="Evaluating..."):
        fn = str(cif).split("/")[-1].split(".")[0]
        try:
            structure = Structure.from_file(cif)
        except Exception as e:
            logging.info(f"CIF error: {repr(e)}")
            structure = None
        if structure is not None:
            structure = adaptor.get_atoms(structure)
            structure.set_calculator(calculator)
            eval_results[fn] = {
                "potential_e": structure.get_potential_energy(),
                "force": structure.get_forces()
            }
    df_out = pd.DataFrame(eval_results).T
    print("\nSaved to df.\n")
    return df_out
    
if __name__ == "__main__":
    relaxer = Relaxer(Path("mp.pth"))
    fpath = Path("/test_data")
    print(relax_run(fpath,relaxer, traj_file=Path("output")))
