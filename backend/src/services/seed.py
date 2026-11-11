import random
from src.utils import repository as repo
from src.utils.identity import now
from src.utils.security import hash_password
from src.services.statistics import analyze

def demo_rows():
 rng=random.Random(2210);patterns=[['ENTRY','INTRO','MAIN','WORKSHOP','SHOP'],['ENTRY','MAIN','WORKSHOP','SHOP'],['ENTRY','INTRO','SIDE','MAIN','SHOP'],['ENTRY','INTRO','MAIN'],['ENTRY','SIDE'],['ENTRY','INTRO'],['ENTRY','MAIN','SIDE','MAIN','SHOP'],['ENTRY','SIDE','WORKSHOP'],['ENTRY','INTRO','MAIN','WORKSHOP'],['ENTRY','MAIN'],['ENTRY','SIDE','MAIN','SHOP'],['ENTRY','INTRO','SIDE','WORKSHOP','SHOP']];rows=[]
 for i in range(700):
  p=list(patterns[i%len(patterns)])
  if i%5==0:p.insert(1,p[0])
  converted=rng.random() < (.78 if p[-1]=='SHOP' else .15)
  if i%len(patterns) in (7,9):converted=False  # Exit-only variants demonstrate nonzero edit alignment.
  rows.append({'journey_id':f'QS-{i+1:04d}','path':p,'outcome':'converted' if converted else 'exited'})
 return rows

def seed():
 repo.init_db()
 for role,name in [('admin','策展复核人'),('analyst','观展路径分析员'),('viewer','展务观察员')]:
  email=f'{role}@qishan.test';repo.put('users',{'id':email,'email':email,'name':name,'role':role,'password_hash':hash_password('Gallery2026!')},insert_only=True)
 dictionary={'id':'dict-gallery','name':'栖山秋展 · 六触点编码册','entries':[{'code':c,'label':l} for c,l in [('ENTRY','入口'),('INTRO','序厅'),('MAIN','主展厅'),('SIDE','侧展廊'),('WORKSHOP','体验室'),('SHOP','纪念区')]],'created_at':now()};repo.put('dictionaries',dictionary,insert_only=True)
 rows=demo_rows();repo.put('datasets',{'id':'ds-gallery','name':'秋展匿名观展路径 · 700条','source':'gallery_paths_202611.csv','dictionary_id':'dict-gallery','rows':rows,'created_at':now()},insert_only=True)
 study={'id':'study-autumn','name':'秋展触达顺序 · 折叠连续重复','dataset_id':'ds-gallery','min_support':.1,'max_length':3,'collapse_repeats':True,'created_at':now()};repo.put('studies',study,insert_only=True)
 repo.put('runs',{'id':'run-baseline','study_id':'study-autumn','status':'completed','result':analyze(rows,dictionary,study),'error':'','created_at':now()},insert_only=True)
 repo.put('reviews',{'id':'review-baseline','run_id':'run-baseline','comment':'支持度以旅程为分母，分组差异仅描述关联，不作因果或归因结论。','status':'approved','reviewer':'admin@qishan.test','created_at':now()},insert_only=True)
 repo.put('reports',{'id':'report-baseline','run_id':'run-baseline','review_id':'review-baseline','title':'栖山秋展路径顺序复核册','created_at':now()},insert_only=True)
 return {t:len(repo.all_rows(t)) for t in ('users','datasets','dictionaries','studies','runs','reviews','reports')}
