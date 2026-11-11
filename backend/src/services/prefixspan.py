from decimal import Decimal,ROUND_CEILING
from collections import defaultdict
from src.constants.domain import MAX_PATTERN_CANDIDATES

def mine_patterns(rows,min_support=.1,max_length=3):
 if not rows or not 0<min_support<=1 or not 1<=max_length<=4:raise ValueError('支持度/模式长度/样本无效')
 n=len(rows);threshold=max(1,int((Decimal(str(min_support))*n).to_integral_value(rounding=ROUND_CEILING)));groups={g:sum(r['outcome']==g for r in rows) for g in ('converted','exited')};patterns=[];evaluated=0
 def grow(prefix,projected):
  nonlocal evaluated
  extensions=defaultdict(dict)
  for idx,start in projected.items():
   # Earliest suffix occurrence dominates later occurrences for subsequence existence.
   for pos in range(start,len(rows[idx]['path'])):
    symbol=rows[idx]['path'][pos]
    if idx not in extensions[symbol]:extensions[symbol][idx]=pos+1
  for symbol,suffixes in sorted(extensions.items()):
   evaluated+=1
   if evaluated>MAX_PATTERN_CANDIDATES:raise ValueError('候选模式超过6000，请提高支持度或缩短模式')
   count=len(suffixes)
   if count<threshold:continue
   pattern=prefix+(symbol,);converted=sum(rows[i]['outcome']=='converted' for i in suffixes);exited=count-converted
   cs=converted/groups['converted'] if groups['converted'] else None;es=exited/groups['exited'] if groups['exited'] else None
   patterns.append({'pattern':list(pattern),'count':count,'support':count/n,'converted_count':converted,'exited_count':exited,'converted_support':cs,'exited_support':es,'support_difference':cs-es if cs is not None and es is not None else None})
   if len(pattern)<max_length:grow(pattern,suffixes)
 grow((),{i:0 for i in range(n)})
 patterns.sort(key=lambda p:(-p['count'],-len(p['pattern']),tuple(p['pattern'])))
 return {'patterns':patterns[:200],'total_patterns':len(patterns),'patterns_truncated':len(patterns)>200,'candidate_patterns_evaluated':evaluated,'min_count':threshold,'group_sizes':groups}
