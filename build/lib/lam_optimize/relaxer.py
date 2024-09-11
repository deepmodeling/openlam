# Adapted from m3gnet.Relaxer

import ase
from pymatgen.io.ase import AseAtomsAdaptor
import numpy as np
from pymatgen.core.structure import Molecule, Structure

from ase.optimize import (
    BFGS,
    FIRE,
    LBFGS,
    LBFGSLineSearch,
    BFGSLineSearch,
    MDMin,
    )
from ase.constraints import ExpCellFilter
import pickle
from pathlib import Path
from typing import Optional, Union

OPTIMIZERS = {
    "FIRE": FIRE,
    "BFGS": BFGS,
    "LBFGS": LBFGS,
    "LBFGSLineSearch": LBFGSLineSearch,
    "MDMin": MDMin,
    "BFGSLineSearch": BFGSLineSearch,
}


class Relaxer:
    """Wrapper for ase.Atoms
    
    Parameters:
    ----------
    model: Union[Path, str]
        Indicates which calculator to use during relaxation, `mace` will call default MACE-medium model,
        for DP model, a path to the freezed model is needed.
    optimizer: str
        The optimizer from ASE, supports `FIRE`, `BFGS`, `LBFGS`, `LBFGSLineSearch`, `MDMin`, `BFGSLineSearch`.
    relax_cell: bool
        Whether to relax cell with `ExpCellFilter`.
    """
    def __init__(self, model: Union[str, Path], optimizer: Optional[str] = "BFGS" , relax_cell: Optional[bool] = True):
        if isinstance(model, Path):
            try:
                from deepmd.calculator import DP as DPCalculator
                self.calculator = DPCalculator(model)
            except Exception as e:
                raise ValueError(f"DP calculator load failed: {e}")
        elif model == "mace":
            import torch
            from mace.calculators import mace_mp
            device = "cuda" if torch.cuda.is_available() else "cpu"
            MACE_CALC = mace_mp(model="medium", device=device, default_dtype="float64")
            self.calculator=MACE_CALC
        else:
            raise NotImplementedError("Only DP calculator and MACE calculator are supported.")
        
        self.optimizer = OPTIMIZERS[optimizer]
        self.relax_cell = relax_cell
        self.ase_adaptor = AseAtomsAdaptor()
  
    def relax(self, atoms, fmax: float, steps: int, traj_file: str = None):

        if isinstance(atoms, (Structure, Molecule)):
            atoms = self.ase_adaptor.get_atoms(atoms)
        atoms.set_calculator(self.calculator)
        obs = TrajectoryObserver(atoms)
        if self.relax_cell:
            atoms = ExpCellFilter(atoms)
        opt = self.optimizer(atoms)
        opt.attach(obs)
        opt.run(fmax=fmax, steps=steps)
        obs()
        if traj_file is not None:
            obs.save(traj_file)
        if isinstance(atoms, ExpCellFilter):
            atoms = atoms.atoms
        return {
            "final_structure": self.ase_adaptor.get_structure(atoms).as_dict(),
            "trajectory": obs,
        }

class TrajectoryObserver:
    """
    Trajectory observer is a hook in the relaxation process that saves the
    intermediate structures
    """

    def __init__(self, atoms: ase.Atoms):
        """
        Args:
            atoms (Atoms): the structure to observe
        """
        self.atoms = atoms
        self.energies: list[float] = []
        self.forces: list[np.ndarray] = []
        self.stresses: list[np.ndarray] = []
        self.atom_positions: list[np.ndarray] = []
        self.cells: list[np.ndarray] = []

    def __call__(self):
        """
        The logic for saving the properties of an Atoms during the relaxation
        Returns:
        """
        self.energies.append(self.compute_energy())
        self.forces.append(self.atoms.get_forces())
        self.stresses.append(self.atoms.get_stress())
        self.atom_positions.append(self.atoms.get_positions())
        self.cells.append(self.atoms.get_cell()[:])

    def compute_energy(self) -> float:
        """
        calculate the energy, here we just use the potential energy
        Returns:
        """
        energy = self.atoms.get_potential_energy()
        return energy

    def save(self, filename: str):
        """
        Save the trajectory to file
        Args:
            filename (str): filename to save the trajectory
        Returns:
        """
        with open(filename, "wb") as f:
            pickle.dump(
                {
                    "energy": self.energies,
                    "forces": self.forces,
                    "stresses": self.stresses,
                    "atom_positions": self.atom_positions,
                    "cell": self.cells,
                    "atomic_number": self.atoms.get_atomic_numbers(),
                },
                f,
            )

