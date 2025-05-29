from typing import List, Optional

import marshmallow_dataclass
from marshmallow import EXCLUDE


@marshmallow_dataclass.dataclass
class DownloadModelData:
    class Meta:
        unknown = EXCLUDE
    type : int
    repo_id : str
    backend : str
    additionalLicenseLink: Optional[str]

@marshmallow_dataclass.dataclass
class DownloadModelRequestBody:
    data : List[DownloadModelData]
    source : str

@marshmallow_dataclass.dataclass
class ComfyUICustomNodesGithubRepoId:
    username: str
    repoName: str
    gitRef: Optional[str]

@marshmallow_dataclass.dataclass
class ComfyUICustomNodesDownloadRequest:
    data : List[ComfyUICustomNodesGithubRepoId]

@marshmallow_dataclass.dataclass
class ComfyUICheckWorkflowRequirementRequest:
    pythonPackages : List[str]
    customNodes : List[ComfyUICustomNodesGithubRepoId]

@marshmallow_dataclass.dataclass
class ComfyUIPackageInstallRequest:
    data : List[str]
