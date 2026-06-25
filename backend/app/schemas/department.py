from pydantic import BaseModel


class DepartmentItem(BaseModel):
    id: int
    external_id: str | None = None
    code: str
    name: str
    region: str
    shpi_region_code: str | None = None
    shpi_region_name: str | None = None
    parent_id: int | None
    department_type: str | None
    full_path: str | None
    is_active: bool = True


class DepartmentTreeItem(BaseModel):
    id: int
    external_id: str | None = None
    code: str
    name: str
    shpi_region_code: str | None = None
    shpi_region_name: str | None = None
    department_type: str | None
    full_path: str | None
    is_active: bool = True
    children: list["DepartmentTreeItem"]


class MissingShpiRegionDepartmentItem(BaseModel):
    id: int
    code: str
    name: str
    department_type: str | None
    full_path: str | None


class MissingShpiRegionDepartmentResponse(BaseModel):
    items: list[MissingShpiRegionDepartmentItem]
    total: int


DepartmentTreeItem.model_rebuild()
