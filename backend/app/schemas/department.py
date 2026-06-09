from pydantic import BaseModel


class DepartmentItem(BaseModel):
    id: int
    code: str
    name: str
    region: str
    parent_id: int | None
    department_type: str | None
    full_path: str | None


class DepartmentTreeItem(BaseModel):
    id: int
    code: str
    name: str
    department_type: str | None
    full_path: str | None
    children: list["DepartmentTreeItem"]


DepartmentTreeItem.model_rebuild()
