from src.models.entities import TouchpointDictionary
from src.utils import repository as repo
from src.utils.identity import new_id,now

def list_dictionaries():return repo.all_rows('dictionaries')
def create(data):
 entries=[e.model_dump() for e in data.entries]
 if len({e['code'] for e in entries})!=len(entries):raise ValueError('触点编码不能重复')
 return repo.put('dictionaries',TouchpointDictionary(new_id('dict'),data.name,entries,now()))
