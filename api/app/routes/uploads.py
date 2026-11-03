from pathlib import Path

from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.schemas import UploadOut
from app.security import legacy_identity

router = APIRouter()


@router.post("/api/requirements", status_code=201, response_model=UploadOut)
async def upload_requirement(
    request: Request,
    file: UploadFile = File(...),
    identity: dict[str, str] = Depends(legacy_identity),
) -> UploadOut:
    target = Path(request.app.state.upload_dir) / str(file.filename)
    content = await file.read()
    target.write_bytes(content)
    return UploadOut(
        owner=identity["username"],
        file_name=file.filename,
        stored_at=str(target),
        size=len(content),
    )
