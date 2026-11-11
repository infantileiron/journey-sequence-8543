from dataclasses import dataclass,field
from typing import Any
@dataclass
class TouchpointDictionary:
 id:str
 name:str
 entries:list[dict]
 created_at:str=''
@dataclass
class JourneyDataset:
 id:str
 name:str
 source:str
 dictionary_id:str
 rows:list[dict]
 created_at:str=''
 version:int=1
 batches:list[dict]=field(default_factory=list)
@dataclass
class SequenceStudy:
 id:str
 name:str
 dataset_id:str
 min_support:float=.1
 max_length:int=3
 collapse_repeats:bool=True
 created_at:str=''
@dataclass
class SequenceRun:
 id:str
 study_id:str
 status:str='queued'
 result:dict[str,Any]=field(default_factory=dict)
 error:str=''
 created_at:str=''
 dataset_id:str=''
 dataset_version:int=0
 snapshot_rows:list[dict]=field(default_factory=list)
@dataclass
class PathReview:
 id:str
 run_id:str
 comment:str
 status:str='pending'
 reviewer:str=''
 created_at:str=''
@dataclass
class Report:
 id:str
 run_id:str
 review_id:str
 title:str
 created_at:str=''
