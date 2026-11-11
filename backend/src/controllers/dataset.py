from src.services import dataset as service
def list_items(): return service.list_datasets()
def detail(id): return service.detail(id)
def create(data):
    target=getattr(data,'dataset_id',None) or getattr(data,'target_dataset_id',None)
    return service.supplement(target,data) if target else service.create(data)
def rename(id,data): return service.rename(id,data)
def supplement(id,data): return service.supplement(id,data)
def batches(id): return service.batches(id)
def quarantine(id): return service.quarantine(id)
