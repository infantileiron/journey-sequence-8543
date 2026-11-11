from collections import Counter
from src.constants.domain import MAX_UNIQUE_PATHS

def levenshtein(a,b):
 previous=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  current=[i]
  for j,y in enumerate(b,1):current.append(min(previous[j]+1,current[j-1]+1,previous[j-1]+(x!=y)))
  previous=current
 return previous[-1]
def align(a,b):
 d=[[0]*(len(b)+1) for _ in range(len(a)+1)]
 for i in range(len(a)+1):d[i][0]=i
 for j in range(len(b)+1):d[0][j]=j
 for i in range(1,len(a)+1):
  for j in range(1,len(b)+1):d[i][j]=min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+(a[i-1]!=b[j-1]))
 i,j=len(a),len(b);operations=[]
 while i or j:
  if i and j and a[i-1]==b[j-1] and d[i][j]==d[i-1][j-1]:operations.append({'operation':'keep','from':a[i-1],'to':b[j-1]});i-=1;j-=1
  elif i and j and d[i][j]==d[i-1][j-1]+1:operations.append({'operation':'substitute','from':a[i-1],'to':b[j-1]});i-=1;j-=1
  elif i and d[i][j]==d[i-1][j]+1:operations.append({'operation':'delete','from':a[i-1],'to':None});i-=1
  else:operations.append({'operation':'insert','from':None,'to':b[j-1]});j-=1
 operations.reverse();assert sum(o['operation']!='keep' for o in operations)==d[-1][-1]
 return {'distance':d[-1][-1],'operations':operations}
def representatives(rows):
 groups={'all':Counter(tuple(r['path']) for r in rows),'converted':Counter(tuple(r['path']) for r in rows if r['outcome']=='converted'),'exited':Counter(tuple(r['path']) for r in rows if r['outcome']=='exited')}
 if len(groups['all'])>MAX_UNIQUE_PATHS:raise ValueError('折叠后唯一序列超过160，请缩小样本或预先分组')
 cache={}
 def distance(a,b):
  if a==b:return 0
  key=tuple(sorted((a,b)))
  if key not in cache:cache[key]=levenshtein(*key)
  return cache[key]
 medoids={}
 for group,counts in groups.items():
  if not counts:medoids[group]=None;continue
  cost,path=min((sum(freq*distance(path,other) for other,freq in counts.items()),path) for path in sorted(counts))
  medoids[group]={'path':list(path),'frequency':counts[path],'weighted_total_distance':cost,'mean_distance':cost/sum(counts.values()),'journeys':sum(counts.values())}
 alignments=[]
 if groups['converted']:
  for path,freq in sorted(groups['exited'].items(),key=lambda x:(-x[1],x[0]))[:12]:
   target=min(groups['converted'],key=lambda p:(distance(path,p),-groups['converted'][p],p))
   alignments.append({'exited_path':list(path),'frequency':freq,'converted_path':list(target),**align(path,target)})
 return {'medoids':medoids,'alignments':alignments,'unique_paths':len(groups['all']),'distance_cache_pairs':len(cache),'alignment_limit':12}
