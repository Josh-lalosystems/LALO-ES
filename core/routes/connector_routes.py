from fastapi import APIRouter, HTTPException
from core.services.connector_manager import ConnectorManager

router = APIRouter()
manager = ConnectorManager()

@router.post('/api/connectors')
def add_connector(payload: dict):
    name = payload.get('type')
    config = payload.get('config', {})
    try:
        manager.add_connector(name, config)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/api/connectors')
def list_connectors():
    return {"connectors": manager.list_connectors()}

@router.get('/api/connectors/{name}')
def get_connector(name: str):
    connector = manager.get_connector(name)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    return {"name": name, "config": connector.config}

@router.put('/api/connectors/{name}')
def update_connector(name: str, payload: dict):
    config = payload.get('config', {})
    connector = manager.get_connector(name)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    connector.config = config
    return {"success": True}

@router.delete('/api/connectors/{name}')
def delete_connector(name: str):
    if name in manager.connectors:
        del manager.connectors[name]
        return {"success": True}
    raise HTTPException(status_code=404, detail="Connector not found")

@router.post('/api/connectors/{name}/test')
def test_connector(name: str):
    result = manager.test_connector(name)
    return {"success": result}

@router.post('/api/connectors/{name}/sync')
def sync_connector(name: str):
    result = manager.sync_connector(name)
    return {"result": result}
