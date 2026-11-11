from src.models.entities import SequenceStudy
from src.utils import repository as repo
from src.utils.identity import new_id,now

def list_studies():return repo.all_rows('studies')
def create(data):
 repo.get('datasets',data.dataset_id)
 return repo.put('studies',SequenceStudy(new_id('study'),data.name,data.dataset_id,data.min_support,data.max_length,data.collapse_repeats,now()))
