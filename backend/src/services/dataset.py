import csv,io
from dataclasses import asdict
from src.models.entities import JourneyDataset
from src.utils import repository as repo
from src.utils.identity import new_id,now
from src.constants.domain import OUTCOMES,MAX_JOURNEYS,MAX_PATH_LENGTH

def summary(item):return {k:v for k,v in item.items() if k!='rows'}|{'row_count':len(item['rows']),'converted':sum(r['outcome']=='converted' for r in item['rows']),'exited':sum(r['outcome']=='exited' for r in item['rows'])}
def list_datasets():return [summary(x) for x in repo.all_rows('datasets')]
def detail(id):return repo.get('datasets',id)
def rename(id,data):
 item=repo.get('datasets',id);item['name']=data.name;repo.put('datasets',item);return summary(item)
def create(data):
 dictionary=repo.get('dictionaries',data.dictionary_id);codes={e['code'] for e in dictionary['entries']}
 reader=csv.DictReader(io.StringIO(data.csv_text.lstrip('\ufeff')))
 if not {'journey_id','path','outcome'}.issubset(reader.fieldnames or []):raise ValueError('CSV需要journey_id,path,outcome；路径用>分隔')
 rows=[];seen=set()
 for n,r in enumerate(reader,2):
  if n>MAX_JOURNEYS+1:raise ValueError('最多2000条路径')
  id=(r.get('journey_id') or '').strip();path=[x.strip() for x in (r.get('path') or '').split('>')]
  if not id or id in seen or not 1<=len(path)<=MAX_PATH_LENGTH or any(not c or c not in codes for c in path) or r['outcome'] not in OUTCOMES:raise ValueError(f'第{n}行空路径/未知触点/重复编号/终态无效')
  seen.add(id);rows.append({'journey_id':id,'path':path,'outcome':r['outcome']})
 if not rows:raise ValueError('至少1条匿名观展路径')
 item=JourneyDataset(new_id('ds'),data.name,data.source,data.dictionary_id,rows,now());repo.put('datasets',item);return summary(asdict(item))
