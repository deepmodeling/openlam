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


# Query crystal structures from OpenLAM Database

Set environmental variable `BOHRIUM_ACCESS_KEY` which is generated from https://bohrium.dp.tech/settings/user
```
export BOHRIUM_ACCESS_KEY=xxx
```
Query crystal structures from OpenLAM Database using Python API
```python
from lam_optimize import CrystalStructure
data = CrystalStructure.query_by_page()
```
The method `query_by_page` accept following arguments as query conditions
```python
formula: Optional[str] = None
min_energy: Optional[float] = None
max_energy: Optional[float] = None
min_submission_time: Optional[datetime.datetime] = None
max_submission_time: Optional[datetime.datetime] = None
page: int = 1
```
The structure of the returned data is like
```
{'page': 1, 'pageSize': 10, 'total': 59, 'items': [<__main__.CrystalStructure object at 0x7f84bb5319a0>, <__main__.CrystalStructure object at 0x7f84a9623850>, <__main__.CrystalStructure object at 0x7f84bb54eb20>, <__main__.CrystalStructure object at 0x7f84bb54edc0>, <__main__.CrystalStructure object at 0x7f84bb56f4f0>, <__main__.CrystalStructure object at 0x7f84bb56fbe0>, <__main__.CrystalStructure object at 0x7f84bb574310>, <__main__.CrystalStructure object at 0x7f84bb574a30>, <__main__.CrystalStructure object at 0x7f84bb583940>, <__main__.CrystalStructure object at 0x7f8478019dc0>]}
```
Except for the paging information, `items` is a list of `CrystalStructure` objects
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
