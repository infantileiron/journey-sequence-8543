import copy,csv,hashlib,io
from dataclasses import asdict
from src.models.entities import JourneyDataset
from src.utils import repository as repo
from src.utils.identity import new_id,now
from src.constants.domain import OUTCOMES,MAX_JOURNEYS,MAX_PATH_LENGTH

DEFAULT_REVISION=1

def _reader(csv_text):
 reader=csv.DictReader(io.StringIO(csv_text.lstrip('\ufeff')))
 names=[(name or '').strip().lstrip('\ufeff') for name in (reader.fieldnames or [])]
 if not {'journey_id','path','outcome'}.issubset(names):raise ValueError('CSV需要journey_id,path,outcome；路径用>分隔')
 reader.fieldnames=names
 return reader,names

def _revision(value,present):
 if not present or value is None or str(value).strip()=='':
  return DEFAULT_REVISION,None
 try:revision=int(str(value).strip())
 except (TypeError,ValueError):return None,'修订号必须是整数'
 if revision<0:return None,'修订号不能为负数'
 return revision,None

def _row_revision(row):
 try:return int(row.get('revision',DEFAULT_REVISION))
 except (TypeError,ValueError):return DEFAULT_REVISION

def _path(value,codes):
 raw='' if value is None else str(value)
 path=[part.strip() for part in raw.split('>')]
 if not raw.strip() or any(not part for part in path):return None,'空路径'
 if not 1<=len(path)<=MAX_PATH_LENGTH:return None,f'路径触点数量必须在1—{MAX_PATH_LENGTH}'
 unknown=[part for part in path if part not in codes]
 if unknown:return None,'未知触点：'+','.join(unknown)
 return path,None

def _outcome(value):
 raw='' if value is None else str(value).strip()
 if raw not in OUTCOMES:return None,'终态必须为converted或exited'
 return raw,None

def _normalize(item):
 """Give legacy payloads a revision/version/batches view and keep one row per journey."""
 item=copy.deepcopy(item)
 item.setdefault('version',1)
 item.setdefault('batches',[])
 rows=item.get('rows') or []
 index={};deduped=[]
 for row in rows:
  if not isinstance(row,dict):continue
  row.setdefault('revision',DEFAULT_REVISION)
  journey_id=row.get('journey_id')
  if not journey_id:continue
  if journey_id in index:
   # A duplicate must never contribute twice to support; keep the newest revision.
   if _row_revision(row)>_row_revision(deduped[index[journey_id]]):deduped[index[journey_id]]=row
   continue
  index[journey_id]=len(deduped);deduped.append(row)
 item['rows']=deduped
 try:item['version']=int(item.get('version') or 1)
 except (TypeError,ValueError):item['version']=1
 return item

def summary(item):
 item=_normalize(item);rows=item['rows'];batches=item.get('batches',[])
 accepted=sum(int(b.get('accepted') or 0) for b in batches)
 ignored=sum(int(b.get('ignored') or 0) for b in batches)
 quarantined=sum(int(b.get('quarantined') or 0) for b in batches)
 result={k:v for k,v in item.items() if k not in ('rows','batches','snapshot_rows')}
 result.update({'row_count':len(rows),'converted':sum(r.get('outcome')=='converted' for r in rows),'exited':sum(r.get('outcome')=='exited' for r in rows),'batch_count':len(batches),'accepted':accepted,'ignored':ignored,'quarantined':quarantined,'accepted_count':accepted,'ignored_count':ignored,'quarantined_count':quarantined,'accepted_total':accepted,'ignored_total':ignored,'quarantined_total':quarantined,'quarantine_count':quarantined,'max_revision':max((_row_revision(r) for r in rows),default=0),'dataset_version':item['version']})
 return result

def list_datasets():return [summary(x) for x in repo.all_rows('datasets')]
def detail(id):
 item=_normalize(repo.get('datasets',id))
 return {**summary(item),'rows':item['rows'],'batches':item['batches']}
def batches(id):return _normalize(repo.get('datasets',id))['batches']
def quarantine(id):
 item=_normalize(repo.get('datasets',id));issues=[]
 for batch in item['batches']:
  for row in batch.get('quarantined_rows',[]):issues.append({**row,'batch_id':batch.get('batch_id')})
 return issues
def rename(id,data):
 item=_normalize(repo.get('datasets',id));item['name']=data.name;repo.put('datasets',item);return summary(item)

def _content_hash(csv_text):return hashlib.sha256(csv_text.lstrip('\ufeff').encode()).hexdigest()
def _auto_batch_id(csv_text):return 'batch-'+_content_hash(csv_text)[:16]
def _batch_id(value,csv_text):
 raw='' if value is None else str(value).strip()
 return raw or _auto_batch_id(csv_text)

def _parse_initial(csv_text,codes):
 reader,names=_reader(csv_text);has_revision='revision' in names or 'rev' in names
 rows=[];seen=set()
 for n,raw in enumerate(reader,2):
  if n>MAX_JOURNEYS+1:raise ValueError('最多2000条路径')
  journey_id=(raw.get('journey_id') or '').strip()
  revision,revision_error=_revision(raw.get('revision') if 'revision' in names else raw.get('rev'),has_revision)
  path,path_error=_path(raw.get('path'),codes)
  outcome,outcome_error=_outcome(raw.get('outcome'))
  if not journey_id:raise ValueError(f'第{n}行缺少旅程编号')
  if revision_error or path_error or outcome_error:raise ValueError(f'第{n}行{revision_error or path_error or outcome_error}')
  if journey_id in seen:raise ValueError(f'第{n}行重复旅程编号，一条旅程只保留一个版本')
  seen.add(journey_id);rows.append({'journey_id':journey_id,'revision':revision,'path':path,'outcome':outcome})
 if not rows:raise ValueError('至少1条匿名观展路径')
 return rows

def _parse_supplement(csv_text,codes,current):
 reader,names=_reader(csv_text);has_revision='revision' in names or 'rev' in names
 pending={};pending_line={};ignored=[];quarantined=[];total=0
 for n,raw in enumerate(reader,2):
  total+=1
  if total>MAX_JOURNEYS:raise ValueError('单批最多2000条路径')
  raw_journey=raw.get('journey_id')
  journey_id=('' if raw_journey is None else str(raw_journey)).strip()
  raw_revision=raw.get('revision') if 'revision' in names else raw.get('rev')
  revision,revision_error=_revision(raw_revision,has_revision)
  path,path_error=_path(raw.get('path'),codes)
  outcome,outcome_error=_outcome(raw.get('outcome'))
  reason=revision_error or path_error or outcome_error
  if not journey_id:reason='缺少旅程编号'
  if reason:
   quarantined.append({'line':n,'journey_id':journey_id,'revision':revision if revision is not None else raw_revision,'path':raw.get('path'),'outcome':raw.get('outcome'),'raw':{name:raw.get(name) for name in names},'reason':reason})
   continue
  current_row=pending.get(journey_id) or current.get(journey_id)
  current_revision=_row_revision(current_row) if current_row else None
  if current_row is None or revision>current_revision:
   if journey_id in pending:
    # A later row in the same batch may supersede an earlier one, but only once.
    ignored.append({'line':pending_line[journey_id],'journey_id':journey_id,'revision':_row_revision(pending[journey_id]),'reason':f'同批次被更高修订 {revision} 覆盖'})
   pending[journey_id]={'journey_id':journey_id,'revision':revision,'path':path,'outcome':outcome};pending_line[journey_id]=n
  else:
   reason=f'旧修订 {revision} 不覆盖当前修订 {current_revision}' if revision<current_revision else f'修订 {revision} 已存在，重复行不重复计入'
   ignored.append({'line':n,'journey_id':journey_id,'revision':revision,'reason':reason})
 return pending,ignored,quarantined,total

def _result(item,batch,replay):
 result=summary(item)
 quarantined=int(batch.get('quarantined') or 0);total=int(batch.get('total_rows') or 0)
 return {**result,'dataset':result,'batch':batch,'version':result['version'],'row_count':result['row_count'],'accepted':0 if replay else int(batch.get('accepted') or 0),'ignored':(total-quarantined) if replay else int(batch.get('ignored') or 0),'quarantined':quarantined,'accepted_count':0 if replay else int(batch.get('accepted') or 0),'ignored_count':(total-quarantined) if replay else int(batch.get('ignored') or 0),'quarantined_count':quarantined,'quarantined_rows':batch.get('quarantined_rows',[]),'ignored_rows':batch.get('ignored_rows',[]),'replay':replay,'already_applied':replay,'duplicate':replay}

def create(data):
 target=getattr(data,'dataset_id',None) or getattr(data,'target_dataset_id',None)
 if target:return supplement(target,data)
 dictionary=repo.get('dictionaries',data.dictionary_id);codes={e['code'] for e in dictionary['entries']}
 rows=_parse_initial(data.csv_text,codes)
 hash_value=_content_hash(data.csv_text);batch_id=_batch_id(getattr(data,'batch_id',None),data.csv_text)
 batch={'batch_id':batch_id,'content_hash':hash_value,'source':data.source,'kind':'initial','received_at':now(),'total_rows':len(rows),'accepted':len(rows),'ignored':0,'quarantined':0,'ignored_rows':[],'quarantined_rows':[],'version_before':0,'version_after':1}
 item=JourneyDataset(new_id('ds'),data.name,data.source,data.dictionary_id,rows,now(),1,[batch]);repo.put('datasets',item);return summary(asdict(item))

def supplement(id,data):
 item=_normalize(repo.get('datasets',id));dictionary=repo.get('dictionaries',item['dictionary_id']);codes={e['code'] for e in dictionary['entries']}
 csv_text=data.csv_text;hash_value=_content_hash(csv_text);batch_id=_batch_id(getattr(data,'batch_id',None),csv_text)
 existing=next((batch for batch in item['batches'] if batch.get('batch_id')==batch_id),None)
 if existing:
  if existing.get('content_hash') and existing['content_hash']!=hash_value:raise ValueError('批次号已用于不同内容，请使用新的批次号')
  return _result(item,existing,True)
 current={row['journey_id']:row for row in item['rows']}
 pending,ignored,quarantined,total=_parse_supplement(csv_text,codes,current)
 version_before=item['version']
 if pending:
  rows=item['rows'];index={row['journey_id']:position for position,row in enumerate(rows)}
  if len(index)+sum(1 for journey_id in pending if journey_id not in index)>MAX_JOURNEYS:raise ValueError('数据集最多2000条路径，本次补传未写入')
  for journey_id,row in pending.items():
   if journey_id in index:rows[index[journey_id]]=row
   else:index[journey_id]=len(rows);rows.append(row)
  item['version']=version_before+1
 source=(getattr(data,'source','') or item.get('source') or '')[:100]
 batch={'batch_id':batch_id,'content_hash':hash_value,'source':source,'kind':'supplement','received_at':now(),'total_rows':total,'accepted':len(pending),'ignored':len(ignored),'quarantined':len(quarantined),'ignored_rows':ignored,'quarantined_rows':quarantined,'version_before':version_before,'version_after':item['version']}
 item['batches'].append(batch)
 # The payload is a single row; one put makes the whole batch (and its audit trail) atomic.
 repo.put('datasets',item)
 return _result(item,batch,False)

# Compatibility aliases for callers that describe the operation as append/ingest.
append=supplement
ingest=supplement
upload=supplement
