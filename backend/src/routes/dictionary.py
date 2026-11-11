from fastapi import APIRouter,Depends
from src.controllers import dictionary as controller
from src.schemas.entities import DictionaryInput
from src.services.auth import current,editor
router=APIRouter(prefix='/dictionaries',tags=['dictionaries'])
@router.get('')
def list_items(user=Depends(current)):return controller.list_items()
@router.post('',status_code=201)
def create(data:DictionaryInput,user=Depends(editor)):return controller.create(data)
