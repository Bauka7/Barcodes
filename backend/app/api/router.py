from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.barcode_codes import router as barcode_codes_router
from app.api.routes.barcodes import router as barcodes_router
from app.api.routes.clients import router as clients_router
from app.api.routes.departments import router as departments_router
from app.api.routes.health import router as health_router
from app.api.routes.official_shpi import router as official_shpi_router
from app.api.routes.range_requests import router as range_requests_router
from app.api.routes.ranges import router as ranges_router
from app.api.routes.users import router as users_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(admin_router)
api_router.include_router(official_shpi_router)
api_router.include_router(auth_router)
api_router.include_router(barcode_codes_router)
api_router.include_router(barcodes_router)
api_router.include_router(clients_router)
api_router.include_router(departments_router)
api_router.include_router(range_requests_router)
api_router.include_router(ranges_router)
api_router.include_router(users_router)
api_router.include_router(audit_router)
