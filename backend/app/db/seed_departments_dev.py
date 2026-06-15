import asyncio

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models import Department


DEV_DEPARTMENTS = [
    {
        "code": "KZROOT",
        "name": "АО Казпочта",
        "region": "Казахстан",
        "department_type": "root",
        "parent_code": None,
    },
    {
        "code": "ASTANA",
        "name": "Астанинский почтамт",
        "region": "Астана",
        "department_type": "post office",
        "parent_code": "KZROOT",
    },
    {
        "code": "ARSHALY_SOPS",
        "name": "Аршалынский СОПС",
        "region": "Акмолинская область",
        "department_type": "group",
        "parent_code": "ASTANA",
    },
    {
        "code": "ARSHALY_SOPS_CENTER",
        "name": "ЦОУ Аршалынский СОПС",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "ARSHALY_SOPS",
    },
    {
        "code": "AKTASTY",
        "name": "Актасты",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "ARSHALY_SOPS",
    },
    {
        "code": "VOLGODONOVKA",
        "name": "Волгодоновка",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "ARSHALY_SOPS",
    },
    {
        "code": "DONETSKOE",
        "name": "Донецкое",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "ARSHALY_SOPS",
    },
    {
        "code": "KONSTANTINOVKA",
        "name": "Константиновка",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "ARSHALY_SOPS",
    },
    {
        "code": "TURGENEVKA",
        "name": "Тургеневка",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "ARSHALY_SOPS",
    },
    {
        "code": "SARYOBA",
        "name": "Сарыоба",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "ARSHALY_SOPS",
    },
    {
        "code": "RAZDOLNOE",
        "name": "Раздольное",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "ARSHALY_SOPS",
    },
    {
        "code": "NOVOVLADIMIROVKA",
        "name": "Нововладимировка",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "ARSHALY_SOPS",
    },
    {
        "code": "AKBULAK",
        "name": "Акбулак",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "ARSHALY_SOPS",
    },
    {
        "code": "EREYMENTAU_RUPS",
        "name": "Ерейментауский РУПС",
        "region": "Акмолинская область",
        "department_type": "group",
        "parent_code": "ASTANA",
    },
    {
        "code": "EREYMENTAU_RUPS_CENTER",
        "name": "ЦОУ Ерейментауский РУПС",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "OLZHABAI_BATYR",
        "name": "Олжабай Батыр",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "TAIBAI",
        "name": "Тайбай",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "BESTOGAI",
        "name": "Бестогай",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "AKSUAT",
        "name": "Аксуат",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "ERKESHILIK",
        "name": "ЕРКЕНШИЛИК",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "TURGAI",
        "name": "Тургай",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "SELETY",
        "name": "Селеты",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "NOVOMARKOVKA",
        "name": "Новомарковка",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "KUNSHALGAN",
        "name": "Куншалган",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "IZOBILNOE",
        "name": "Изобильное",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "ULENTY",
        "name": "Уленты",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "EREYMENTAU_RUPS",
    },
    {
        "code": "KORGALZHYN_RUPS",
        "name": "Коргалжынский РУПС",
        "region": "Акмолинская область",
        "department_type": "group",
        "parent_code": "ASTANA",
    },
    {
        "code": "KORGALZHYN_RUPS_CENTER",
        "name": "ЦОУ Коргалжынский РУПС",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "KORGALZHYN_RUPS",
    },
    {
        "code": "ARYKTY",
        "name": "Арыкты",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "KORGALZHYN_RUPS",
    },
    {
        "code": "KENBIDAIYK",
        "name": "Кенбидайык",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "KORGALZHYN_RUPS",
    },
    {
        "code": "ORKENDEU",
        "name": "Оркендеу",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "KORGALZHYN_RUPS",
    },
    {
        "code": "SULYKOL",
        "name": "Сулыколь",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "KORGALZHYN_RUPS",
    },
    {
        "code": "SHALKAR",
        "name": "Шалкар",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "KORGALZHYN_RUPS",
    },
    {
        "code": "SABYNDY",
        "name": "Сабынды",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "KORGALZHYN_RUPS",
    },
    {
        "code": "MAISHUKYR",
        "name": "Майшукыр",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "KORGALZHYN_RUPS",
    },
    {
        "code": "KARAEGIN",
        "name": "Караегин",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "KORGALZHYN_RUPS",
    },
    {
        "code": "ZHANTEKE",
        "name": "Жантеке",
        "region": "Акмолинская область",
        "department_type": "department",
        "parent_code": "KORGALZHYN_RUPS",
    },
    {
        "code": "ASTANA_CITY",
        "name": "г.Астана",
        "region": "Астана",
        "department_type": "group",
        "parent_code": "ASTANA",
    },
    {
        "code": "010001",
        "name": "Астана-1",
        "region": "Астана",
        "department_type": "department",
        "parent_code": "ASTANA_CITY",
    },
    {
        "code": "ASTANA_3",
        "name": "Астана-3",
        "region": "Астана",
        "department_type": "department",
        "parent_code": "ASTANA_CITY",
    },
    {
        "code": "ASTANA_4",
        "name": "Астана-4",
        "region": "Астана",
        "department_type": "department",
        "parent_code": "ASTANA_CITY",
    },
    {
        "code": "ASTANA_6",
        "name": "Астана-6",
        "region": "Астана",
        "department_type": "department",
        "parent_code": "ASTANA_CITY",
    },
    {
        "code": "ASTANA_15",
        "name": "Астана-15",
        "region": "Астана",
        "department_type": "department",
        "parent_code": "ASTANA_CITY",
    },
    {
        "code": "ASTANA_14",
        "name": "Астана-14",
        "region": "Астана",
        "department_type": "department",
        "parent_code": "ASTANA_CITY",
    },
    {
        "code": "ASTANA_13",
        "name": "Астана-13",
        "region": "Астана",
        "department_type": "department",
        "parent_code": "ASTANA_CITY",
    },
    {
        "code": "ASTANA_12",
        "name": "Астана-12",
        "region": "Астана",
        "department_type": "department",
        "parent_code": "ASTANA_CITY",
    },
    {
        "code": "ASTANA_11",
        "name": "Астана-11",
        "region": "Астана",
        "department_type": "department",
        "parent_code": "ASTANA_CITY",
    },
    {
        "code": "ASTANA_10",
        "name": "Астана-10",
        "region": "Астана",
        "department_type": "department",
        "parent_code": "ASTANA_CITY",
    },
    {
        "code": "ASTANA_9",
        "name": "Астана-9",
        "region": "Астана",
        "department_type": "department",
        "parent_code": "ASTANA_CITY",
    },
]

DEMO_DEPARTMENT_CODES_TO_REMOVE = {"ALMATY", "050001", "010002"}


async def seed_dev_departments() -> None:
    async with AsyncSessionLocal() as session:
        departments_by_code: dict[str, Department] = {}
        created_count = 0
        updated_count = 0
        removed_count = 0

        stale_result = await session.execute(
            select(Department).where(Department.code.in_(DEMO_DEPARTMENT_CODES_TO_REMOVE))
        )
        for department in stale_result.scalars().all():
            await session.delete(department)
            removed_count += 1

        await session.flush()

        result = await session.execute(select(Department))
        for department in result.scalars().all():
            departments_by_code[department.code] = department

        for item in DEV_DEPARTMENTS:
            department = departments_by_code.get(str(item["code"]))

            if department is None:
                department = Department(
                    code=str(item["code"]),
                    name=str(item["name"]),
                    region=str(item["region"]),
                    department_type=str(item["department_type"]),
                )
                session.add(department)
                await session.flush()
                departments_by_code[department.code] = department
                created_count += 1
            else:
                department.name = str(item["name"])
                department.region = str(item["region"])
                department.department_type = str(item["department_type"])
                updated_count += 1

        await session.flush()

        for item in DEV_DEPARTMENTS:
            department = departments_by_code[str(item["code"])]
            parent_code = item["parent_code"]
            parent = departments_by_code.get(str(parent_code)) if parent_code else None
            parent_path = parent.full_path if parent else None
            department.parent_id = parent.id if parent else None
            department.full_path = (
                f"{parent_path} / {department.name}" if parent_path else department.name
            )

        await session.commit()

    print(f"Created dev departments: {created_count}")
    print(f"Updated dev departments: {updated_count}")
    print(f"Removed demo departments: {removed_count}")


def main() -> None:
    asyncio.run(seed_dev_departments())


if __name__ == "__main__":
    main()
