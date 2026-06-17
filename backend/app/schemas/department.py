from pydantic import BaseModel


class DepartmentItem(BaseModel):
    id: int
    external_id: str | None = None
    code: str
    name: str
    region: str
    parent_id: int | None
    department_type: str | None
    full_path: str | None
    is_active: bool = True


class DepartmentTreeItem(BaseModel):
    id: int
    external_id: str | None = None
    code: str
    name: str
    department_type: str | None
    full_path: str | None
    is_active: bool = True
    children: list["DepartmentTreeItem"]


DepartmentTreeItem.model_rebuild()
