from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
import orjson

from ..db import get_db
from ..schemas import FlowCreate, FlowDB, FlowUpdate, FlowBase
from ..validators import validate_flow
from ..simulator import run_once

router = APIRouter(prefix="/api/flows", tags=["flows"])


def _serialize_id(doc):
    doc["_id"] = str(doc["_id"]) if doc.get("_id") else None
    return doc


@router.get("/", response_model=List[FlowDB])
async def list_flows(orgId: str, projectId: Optional[str] = None, db=Depends(get_db)):
    q = {"orgId": orgId}
    if projectId:
        q["projectId"] = projectId
    cur = db.flows.find(q).sort("updatedAt", -1)
    flows = [_serialize_id(f) async for f in cur]
    return flows


@router.get("/{flow_id}", response_model=FlowDB)
async def get_flow(flow_id: str, db=Depends(get_db)):
    try:
        oid = ObjectId(flow_id)
    except Exception:
        raise HTTPException(400, "Invalid flow id")
    doc = await db.flows.find_one({"_id": oid})
    if not doc:
        raise HTTPException(404, "Flow not found")
    return _serialize_id(doc)


@router.post("/", status_code=201, response_model=FlowDB)
async def create_flow(payload: FlowCreate, db=Depends(get_db)):
    validate_flow(payload)

    now = datetime.utcnow()
    doc = payload.model_dump()
    doc["createdAt"] = now
    doc["updatedAt"] = now
    try:
        res = await db.flows.insert_one(doc)
    except Exception as e:
        raise HTTPException(400, str(e))
    saved = await db.flows.find_one({"_id": res.inserted_id})
    return _serialize_id(saved)


@router.put("/{flow_id}", response_model=FlowDB)
async def update_flow(flow_id: str, payload: FlowUpdate, db=Depends(get_db)):
    try:
        oid = ObjectId(flow_id)
    except Exception:
        raise HTTPException(400, "Invalid flow id")

    existing = await db.flows.find_one({"_id": oid})
    if not existing:
        raise HTTPException(404, "Flow not found")

    updated = {**existing}
    if payload.name is not None:
        updated["name"] = payload.name
    if payload.nodes is not None:
        updated["nodes"] = [n.model_dump() for n in payload.nodes]
    if payload.edges is not None:
        updated["edges"] = [e.model_dump() for e in payload.edges]
    if payload.isDraft is not None:
        updated["isDraft"] = payload.isDraft
    if payload.metadata is not None:
        updated["metadata"] = payload.metadata

    if updated.get("isDraft") is False:
        updated["version"] = int(updated.get("version", 1)) + 1

    validate_flow(FlowBase(**{k: v for k, v in updated.items() if k in FlowBase.model_fields}))

    updated["updatedAt"] = datetime.utcnow()
    await db.flows.replace_one({"_id": oid}, updated)
    saved = await db.flows.find_one({"_id": oid})
    return _serialize_id(saved)


@router.delete("/{flow_id}", status_code=204)
async def delete_flow(flow_id: str, db=Depends(get_db)):
    try:
        oid = ObjectId(flow_id)
    except Exception:
        raise HTTPException(400, "Invalid flow id")
    res = await db.flows.delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(404, "Flow not found")
    return Response(status_code=204)


@router.get("/{flow_id}/export")
async def export_flow(flow_id: str, db=Depends(get_db)):
    try:
        oid = ObjectId(flow_id)
    except Exception:
        raise HTTPException(400, "Invalid flow id")
    doc = await db.flows.find_one({"_id": oid})
    if not doc:
        raise HTTPException(404, "Flow not found")
    fname = f"{doc['name'].replace(' ', '_')}_v{doc.get('version', 1)}.json"
    payload = orjson.dumps(doc, option=orjson.OPT_INDENT_2)
    headers = {"Content-Disposition": f'attachment; filename="{fname}"'}
    return Response(content=payload, media_type="application/json", headers=headers)


@router.post("/import", response_model=FlowDB)
async def import_flow(flow: FlowCreate, db=Depends(get_db)):
    validate_flow(flow)
    now = datetime.utcnow()
    doc = flow.model_dump()
    doc.pop("_id", None)
    doc["createdAt"] = now
    doc["updatedAt"] = now
    res = await db.flows.insert_one(doc)
    saved = await db.flows.find_one({"_id": res.inserted_id})
    return _serialize_id(saved)


@router.post("/{flow_id}/simulate")
async def simulate(flow_id: str, user_inputs: dict | None = None, db=Depends(get_db)):
    try:
        oid = ObjectId(flow_id)
    except Exception:
        raise HTTPException(400, "Invalid flow id")
    doc = await db.flows.find_one({"_id": oid})
    if not doc:
        raise HTTPException(404, "Flow not found")
    flow = FlowBase(**{k: v for k, v in doc.items() if k in FlowBase.model_fields})
    out = run_once(flow, user_inputs or {})
    return JSONResponse(out)
