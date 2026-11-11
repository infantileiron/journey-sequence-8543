import copy,json
from src.models.entities import SequenceRun
from src.utils import repository as repo
from src.utils.identity import new_id, now
from src.services.statistics import analyze
from src.config.settings import TASK_MODE, REDIS_URL, ARTIFACT_DIR

def list_runs(): return [{k:v for k,v in run.items() if k!='snapshot_rows'} for run in repo.all_rows("runs")]
def detail(id): return repo.get("runs",id)
def execute(id):
    run=repo.get("runs",id)
    if run["status"] in ("running","completed"): return run
    run["status"]="running"; repo.put("runs",run)
    try:
        exp=repo.get("studies",run["study_id"])
        dataset_id=run.get("dataset_id") or exp["dataset_id"]
        dataset=repo.get("datasets",dataset_id)
        dictionary=repo.get("dictionaries",dataset["dictionary_id"])
        # A queued run keeps the rows it was submitted with, even if a supplement lands meanwhile.
        rows=run["snapshot_rows"] if "snapshot_rows" in run else dataset["rows"]
        result=analyze(rows,dictionary,exp)
        result["dataset_id"]=dataset_id
        result["dataset_version"]=run.get("dataset_version",dataset.get("version",1))
        run["result"]=result
        ARTIFACT_DIR.mkdir(parents=True,exist_ok=True)
        (ARTIFACT_DIR / (id+".json")).write_text(json.dumps(run["result"],ensure_ascii=False))
        run["status"]="completed"
    except Exception as exc:
        run["status"]="failed"; run["error"]=str(exc)
    return repo.put("runs",run)
def create(data):
    exp=repo.get("studies",data.study_id)
    dataset=repo.get("datasets",exp["dataset_id"])
    if sum(r["status"] in ("queued","running") for r in repo.all_rows("runs"))>=10: raise ValueError("运行队列已满，请等待已有任务完成")
    run=repo.put("runs",SequenceRun(new_id("run"),data.study_id,created_at=now(),dataset_id=exp["dataset_id"],dataset_version=int(dataset.get("version") or 1),snapshot_rows=copy.deepcopy(dataset.get("rows") or [])))
    if TASK_MODE=="inline": return execute(run["id"])
    try:
        import redis
        redis.Redis.from_url(REDIS_URL).rpush("journey-sequence:jobs",run["id"])
    except Exception:
        run["status"]="failed"; run["error"]="队列不可用，请恢复Redis后重新提交"
        repo.put("runs",run)
        raise ValueError(run["error"])
    return run
