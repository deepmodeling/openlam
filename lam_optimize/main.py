# need to install torch, deepmd v3

from __future__ import annotations

import ase.io
from lam_optimize.db import CrystalStructure
from lam_optimize.relaxer import Relaxer
from lam_optimize.utils import get_e_form_per_atom, validate_cif, MATCHER
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from pymatgen.core import Structure
from pymatgen.io.ase import AseAtomsAdaptor
from tqdm import tqdm
import os
import signal
import traceback


def sigalrm_handler(signum, frame):
    raise TimeoutError("Timeout to relax")


def relax_run(fpth: Path, relaxer: Relaxer, fmax: float=1e-4, steps: int=200, traj_file: Path=None, timeout: int=None, check_convergence: bool=True, check_duplicate: bool=False, validate: bool=True):
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
            logging.warn(f"CIF error: {repr(e)}")
            structure = None
        if structure is not None:
            if timeout is not None:
                signal.signal(signal.SIGALRM, sigalrm_handler)
                signal.alarm(timeout)
            try:
                if traj_file is not None:
                    outpath = str(os.path.join(str(traj_file),fn ))
                else:
                    outpath = None
                result = relaxer.relax(structure, fmax=fmax, steps=steps, traj_file=outpath)
                relax_results[fn] = {
                    f"final_structure": result["final_structure"],
                    "final_energy": result["trajectory"].energies[-1],
                    "initial_structure": structure.as_dict(),
                }

            except Exception as exc:
                    logging.warn(f"Failed to relax {fn}: {exc!r}")
            finally:
                if timeout is not None:
                    signal.alarm(0)
        else:
            pass
    df_out = pd.DataFrame(relax_results).T
    print("\nSaved to df.\n")

    atoms_list = []
    for i in df_out.index:
        atoms = AseAtomsAdaptor.get_atoms(Structure.from_dict(df_out.loc[i, "final_structure"]))
        atoms_list.append(atoms)

    os.makedirs("unconverged", exist_ok=True)
    if check_convergence:
        new_atoms_list = []
        unconverged = []
        for i, atoms in enumerate(atoms_list):
            atoms.calc = relaxer.calculator
            if get_e_form_per_atom(atoms, atoms.get_potential_energy()) > 0:
                logging.warn("%s: energy not relaxed" % atoms.symbols)
                unconverged.append(Structure.from_dict(df_out.loc[df_out.index[i], "initial_structure"]))
            elif np.max(abs(atoms.get_forces())) > 0.05:
                logging.warn("%s: forces not relaxed" % atoms.symbols)
                unconverged.append(Structure.from_dict(df_out.loc[df_out.index[i], "initial_structure"]))
            else:
                new_atoms_list.append(atoms)
        atoms_list = new_atoms_list
        for structure in unconverged:
            atoms = AseAtomsAdaptor.get_atoms(structure)
            ase.io.write(f"unconverged/initial-{atoms.symbols}.cif", atoms, format='cif')

    if check_duplicate:
        new_atoms_list = []
        for atoms in atoms_list:
            atoms.calc = relaxer.calculator
            energy = atoms.get_potential_energy()
            structure = AseAtomsAdaptor.get_structure(atoms)
            formula = structure.reduced_formula
            for known_structure in CrystalStructure.query(formula=formula):
                if (
                    abs(known_structure.energy - energy)
                    / max(abs(known_structure.energy), abs(energy))
                    > 0.05
                ):
                    continue
                else:
                    if MATCHER.fit(known_structure.structure, structure):
                        logging.warn("%s: duplicate structure" % atoms.symbols)
                        break
            else:
                new_atoms_list.append(atoms)
        atoms_list = new_atoms_list

    os.makedirs("relaxed", exist_ok=True)
    for atoms in atoms_list:
        cif_file = f"relaxed/final-{atoms.symbols}.cif"
        ase.io.write(cif_file, atoms, format='cif')
        if validate:
            try:
                validate_cif(cif_file)
            except Exception:
                traceback.print_exc()
                os.remove(cif_file)

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
