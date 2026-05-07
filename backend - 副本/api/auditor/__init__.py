from .audit_workbench import router as audit_workbench_router
from .public_content import router as auditor_public_content_router
from fastapi import APIRouter

from .public_content import router as content_router

router = APIRouter(prefix="/auditor", tags=["审核员接口"])


router.include_router(content_router)