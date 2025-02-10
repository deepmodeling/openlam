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
wget https://bohrium-api.dp.tech/ds-dl/lam-crystal-model-01oe-v4.zip
unzip lam-crystal-model-01oe-v4.zip
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


## Query crystal structures from OpenLAM Database

Set environmental variable `BOHRIUM_ACCESS_KEY` which is generated from https://bohrium.dp.tech/settings/user
```
export BOHRIUM_ACCESS_KEY=xxx
```
Query crystal structures from OpenLAM Database using Python API (The method `query_by_page` is deprecated! Use `query_by_offset` instead.)
```python
from lam_optimize import CrystalStructure
data = CrystalStructure.query_by_offset()
```
The method `query_by_offset` accept following arguments as query conditions
```python
formula: Optional[str] = None
min_energy: Optional[float] = None
max_energy: Optional[float] = None
min_submission_time: Optional[datetime.datetime] = None
max_submission_time: Optional[datetime.datetime] = None
offset: int = 0
limit: int = 10
```
The structure of the returned data is like
```
{'nextStartId': 18, 'items': [<lam_optimize.db.CrystalStructure object at 0x7fbd6832e520>, <lam_optimize.db.CrystalStructure object at 0x7fbd6d04aaf0>, <lam_optimize.db.CrystalStructure object at 0x7fbd6d11c610>, <lam_optimize.db.CrystalStructure object at 0x7fbd6d11cd60>, <lam_optimize.db.CrystalStructure object at 0x7fbd6d21a130>, <lam_optimize.db.CrystalStructure object at 0x7fbd6d21a4c0>, <lam_optimize.db.CrystalStructure object at 0x7fbd6d21a850>, <lam_optimize.db.CrystalStructure object at 0x7fbd6d21abe0>, <lam_optimize.db.CrystalStructure object at 0x7fbd6d21af70>, <lam_optimize.db.CrystalStructure object at 0x7fbd6d21d340>]}
```
Except for `nextStartId` (used as `offset` in the next query), `items` is a list of `CrystalStructure` objects
```python
class CrystalStructure:
    formula: str
    structure: pymatgen.core.Structure
    energy: float
    submission_time: datetime.datetime
```

The method `query` merging paged results is also provided
```python
structures = CrystalStructure.query(formula="Sr2YSbO6")
```
which returns a list of `CrystalStructure` objects.

NOTE: Calling non-paging method without query condition will be extremely slow.

## Query hull from OpenLAM Database

Set environmental variable `BOHRIUM_ACCESS_KEY` which is generated from https://bohrium.dp.tech/settings/user
```
export BOHRIUM_ACCESS_KEY=xxx
```
Query hull by composition from OpenLAM Database using Python API
```python
from lam_optimize.utils import query_hull_by_composition
hull = query_hull_by_composition(["Ac", "Ag", "Bi", "As", "Rh", "Cl", "O"])
```
You can calculate energy above hull using the hull
```python
from lam_optimize.utils import get_e_above_hull
ehull = get_e_above_hull(structure, hull, 0.123)
```
To refer to OpenLAM Database in a publication, please cite the [preprint](https://arxiv.org/abs/2501.16358):
> Anyang Peng, Xinzijian Liu, Ming-Yu Guo, Linfeng Zhang, Han Wang. "The OpenLAM Challenges." arXiv, January 20, 2025. https://doi.org/10.48550/arXiv.2501.16358.
