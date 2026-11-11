<script setup lang="ts">
import {ref,watch} from 'vue';
import * as api from '../api/datasets';
import * as dictionaries from '../api/dictionaries';
import {useResource} from '../hooks/useResource';
import {refreshResources} from '../stores/resources';
import {user} from '../stores/session';
import PageTitle from '../components/common/PageTitle.vue';
import Notice from '../components/common/Notice.vue';
import type {DatasetBatch,QuarantineRow} from '../types/entities';

const {data,error}=useResource(api.list,[]);
const {data:dicts}=useResource(dictionaries.list,[]);
const name=ref('补充匿名观展路径');
const dictionary=ref('dict-gallery');
const source=ref('gallery_paths_202611.csv');
const csv=ref('');
const target=ref('');
const supplementSource=ref('gallery_paths_202611_supplement.csv');
const supplementCsv=ref('');
const batchId=ref('');
const message=ref('');
const batchList=ref<DatasetBatch[]>([]);
const issues=ref<QuarantineRow[]>([]);

watch(data,(items)=>{if(!target.value&&items.length)target.value=items[0].id},{immediate:true});
watch(target,(id)=>loadBatches(id));
async function loadBatches(id:string){if(!id){batchList.value=[];issues.value=[];return}try{batchList.value=await api.batches(id);issues.value=await api.quarantine(id)}catch(e:any){message.value=e.message}}
async function createDataset(){try{await api.create({name:name.value,dictionary_id:dictionary.value,source:source.value,csv_text:csv.value});csv.value='';message.value='';refreshResources()}catch(e:any){message.value=e.message}}
async function supplement(){if(!target.value){message.value='请选择要补传的原数据集';return}try{const r=await api.supplement(target.value,{source:supplementSource.value||undefined,batch_id:batchId.value||undefined,csv_text:supplementCsv.value});message.value=`${r.replay?'重复批次，未重复计入':'补传完成'}：本次接纳 ${r.accepted} 条，忽略 ${r.ignored} 条，隔离 ${r.quarantined} 条；数据集共 ${r.row_count} 条旅程，版本 v${r.version}`;supplementCsv.value='';batchId.value='';await loadBatches(target.value);refreshResources()}catch(e:any){message.value=e.message}}
async function upload(e:Event,field:'create'|'supplement'){const f=(e.target as HTMLInputElement).files?.[0];if(f){if(f.size>1000000){message.value='CSV不能超过1MB';return}const text=await f.text();if(field==='create')csv.value=text;else supplementCsv.value=text}}
</script>
<template>
<PageTitle chapter="02" title="一条旅程，只记一份支持" description="补传归入原数据集，按 journey_id 与 revision 接纳新版本；旧修订、重复批次不改变支持度，坏行隔离保留原因。"/>
<Notice :error="error||message"/>
<section class="paper table-scroll">
<table>
<thead><tr><th>路径数据</th><th>版本</th><th>旅程数</th><th>转化 / 退出</th><th>累计接纳 / 忽略 / 隔离</th><th>批次数</th></tr></thead>
<tbody><tr v-for="d in data" :key="d.id"><td><b>{{d.name}}</b><small>{{d.source}}</small></td><td>v{{d.version||1}}</td><td>{{d.row_count}}</td><td>{{d.converted}} / {{d.exited}}</td><td>{{d.accepted_total||0}} / {{d.ignored_total||0}} / {{d.quarantined_total||0}}</td><td>{{d.batch_count||0}}</td></tr></tbody>
</table>
</section>

<form v-if="user?.role!=='viewer'" class="paper form-grid" @submit.prevent="createDataset">
<h2 style="grid-column:1/-1">新建原始数据集</h2>
<label>数据集名称<input aria-label="数据集名称" v-model="name"/></label>
<label>编码册<select v-model="dictionary"><option v-for="d in dicts" :key="d.id" :value="d.id">{{d.name}}</option></select></label>
<label>CSV文件<input type="file" accept=".csv" @change="upload($event,'create')"/></label>
<label class="wide">路径内容<textarea v-model="csv" placeholder="journey_id,path,outcome"/></label>
<button class="primary">校验并导入旅程</button>
</form>

<form v-if="user?.role!=='viewer'" class="paper form-grid" @submit.prevent="supplement">
<h2 style="grid-column:1/-1">补传到原数据集</h2>
<label>原数据集<select aria-label="补传目标数据集" v-model="target"><option v-for="d in data" :key="d.id" :value="d.id">{{d.name}}（v{{d.version||1}}，{{d.row_count}}条）</option></select></label>
<label>批次编号（可留空自动生成）<input v-model="batchId" placeholder="batch-20261112-01"/></label>
<label>CSV文件<input type="file" accept=".csv" @change="upload($event,'supplement')"/></label>
<label>文件名<input v-model="supplementSource"/></label>
<label class="wide">补传内容（journey_id,path,outcome[,revision]）<textarea v-model="supplementCsv" placeholder="journey_id,revision,path,outcome"/></label>
<button class="primary">校验并补传</button>
</form>

<section v-if="target" class="paper">
<h2>补传批次核对</h2>
<p class="annotation">每批显示本次接纳、忽略与隔离数量。相同批次编号重复提交不会再次计入；旧修订被忽略；隔离行保留原始内容与原因，可修正后作为新批次重放。</p>
<div class="table-scroll"><table>
<thead><tr><th>批次</th><th>总行数</th><th>接纳</th><th>忽略</th><th>隔离</th><th>版本</th></tr></thead>
<tbody><tr v-for="b in batchList" :key="b.batch_id"><td><b>{{b.batch_id}}</b><small>{{b.kind}} · {{b.source}} · {{b.received_at}}</small></td><td>{{b.total_rows}}</td><td>{{b.accepted}}</td><td>{{b.ignored}}</td><td>{{b.quarantined}}</td><td><small>v{{b.version_before}} → v{{b.version_after}}</small></td></tr></tbody>
</table></div>
<div v-if="issues.length" class="table-scroll" style="margin-top:24px"><h3>隔离行与原因</h3><table>
<thead><tr><th>批次</th><th>行号</th><th>旅程编号</th><th>修订号</th><th>原因</th></tr></thead>
<tbody><tr v-for="(issue,i) in issues" :key="i"><td>{{issue.batch_id}}</td><td>{{issue.line}}</td><td>{{issue.journey_id||'—'}}</td><td>{{issue.revision??'—'}}</td><td>{{issue.reason}}</td></tr></tbody>
</table></div>
</section>
</template>
