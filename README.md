# A crystal structure optimization tool built on top of ASE

## Installation

After cloning this project, install `lam-crystal-philately` with common dependencies (including requirements for workflows) by
```
pip install .
```
To install additional dependencies for DP
```
pip install ".[dp]"
```
or mace
```
pip install ".[mace]"
```

Download the latest DP model for structure optimization by
```
wget https://bohrium-api.dp.tech/ds-dl/lam-crystal-model-01oe-v2.zip
unzip lam-crystal-model-01oe-v2.zip
```


## Structure Optimization

### Python API

```
from pathlib import Path
from lam_optimize.main import relax_run
from lam_optimize.relaxer import Relaxer

cif_folder_path = Path("/cifs")
relaxer = Relaxer("mace") # using default mace model
# relaxer = Relaxer(Path("dp.pth")) # using DP model
res_df = relax_run(
    cif_folder_path,
    relaxer
)
```

You should see something similar to this:

<img width="429" alt="image" src="https://github.com/deepmodeling/lam-crystal-philately/assets/137014849/0e652ec3-aa8d-4332-b90a-c3fb13c081ff">

The resulting dataframe should contain the following columns:

<img width="539" alt="image" src="https://github.com/deepmodeling/lam-crystal-philately/assets/137014849/f3be0bbf-ff85-4d27-92b2-46ba81e9c5c2">

To get the optimized structure (if converged), do the following:

```
from pymatgen.core import Structure

Structure.from_dict(df['final_structure'][0])
```

### Commandline tool

To optimize structures using DP model
```
lam-opt relax -i examples/data -m <path-to-DP-model>
```
or using mace
```
lam-opt relax -i examples/data -t mace
```

To submit a workflow for optimizing structures on parallel
```
lam-opt submit examples/wf.json -i part0 part1 -m <path-to-DP-model>
```
where the arguments after `-i` should be a list of directories containing cifs.

## Single Point Evaluation

```
from lam_optimize.main import single_point

single_point(Path(fpth), relaxer)

```
This returns the potential energy and forces for a given `.cif` structure.

<img width="568" alt="image" src="https://github.com/deepmodeling/lam-crystal-philately/assets/137014849/6917528d-7e2a-4dc0-a49a-a87825983fba">