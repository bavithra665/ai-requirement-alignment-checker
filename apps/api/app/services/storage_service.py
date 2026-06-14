import os
import aiofiles
from fastapi import UploadFile
from pathlib import Path
from uuid import UUID

class StorageService:
    def __init__(self, base_upload_dir: str = "uploads"):
        self.base_upload_dir = Path(base_upload_dir)
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_brd(self, project_id: UUID, version: int, file: UploadFile) -> str:
        """
        Saves the uploaded BRD to the local filesystem.
        Structure: uploads/{project_id}/version_{version}/{filename}
        """
        project_dir = self.base_upload_dir / str(project_id) / f"version_{version}"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename
        safe_filename = os.path.basename(file.filename)
        file_path = project_dir / safe_filename
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
        return str(file_path)

storage_service = StorageService()
