import io
import os
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_upload_survey_success(client: AsyncClient, async_db: AsyncSession):
    """Test successful survey upload."""
    file_content = b"dummy data"
    files = {
        "file": ("test.xtf", io.BytesIO(file_content), "application/octet-stream")
    }
    data = {
        "channel": "starboard"
    }

    response = await client.post(f"{settings.API_V1_STR}/surveys/upload", files=files, data=data)

    assert response.status_code == 201
    result = response.json()
    assert result["success"] is True
    assert "survey_id" in result["data"]
    assert "job_id" in result["data"]
    assert result["data"]["status"] in ("uploaded", "queued")
    assert result["data"]["source_filename"] == "test.xtf"
    assert result["data"]["file_size_bytes"] == len(file_content)


@pytest.mark.asyncio
async def test_upload_oversized_file(client: AsyncClient, monkeypatch):
    """Test upload file exceeding size limit."""
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)

    file_content = b"a" * 101
    files = {
        "file": ("large.xtf", io.BytesIO(file_content), "application/octet-stream")
    }

    response = await client.post(f"{settings.API_V1_STR}/surveys/upload", files=files)
    assert response.status_code == 413
    result = response.json()
    assert result["success"] is False
    assert result["error"]["code"] == "FILE_TOO_LARGE"


@pytest.mark.asyncio
async def test_upload_wrong_type(client: AsyncClient):
    """Test upload with unsupported file extension."""
    file_content = b"dummy data"
    files = {
        "file": ("test.txt", io.BytesIO(file_content), "text/plain")
    }

    response = await client.post(f"{settings.API_V1_STR}/surveys/upload", files=files)

    assert response.status_code == 415
    result = response.json()
    assert result["success"] is False
    assert result["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


@pytest.mark.asyncio
async def test_list_surveys(client: AsyncClient, async_db: AsyncSession):
    """Test listing surveys."""
    response = await client.get(f"{settings.API_V1_STR}/surveys")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert isinstance(result["data"], list)


@pytest.mark.asyncio
async def test_get_survey_not_found(client: AsyncClient):
    """Test getting a non-existent survey returns 404."""
    bad_id = str(uuid.uuid4())
    response = await client.get(f"{settings.API_V1_STR}/surveys/{bad_id}")
    assert response.status_code == 404
    result = response.json()
    assert result["success"] is False
    assert result["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_survey(client: AsyncClient, async_db: AsyncSession):
    """Test deleting a survey."""
    file_content = b"dummy data"
    files = {
        "file": ("test_delete.xtf", io.BytesIO(file_content), "application/octet-stream")
    }

    upload_response = await client.post(f"{settings.API_V1_STR}/surveys/upload", files=files)
    assert upload_response.status_code == 201
    survey_id = upload_response.json()["data"]["survey_id"]

    delete_response = await client.delete(f"{settings.API_V1_STR}/surveys/{survey_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True

    get_response = await client.get(f"{settings.API_V1_STR}/surveys/{survey_id}")
    assert get_response.status_code == 404
