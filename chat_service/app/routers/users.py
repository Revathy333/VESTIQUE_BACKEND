# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from sqlalchemy import text
# from app.database import get_db
# from app.redis_client import get_online_user_ids
# from app.schemas import OnlineUser

# router = APIRouter(prefix="/users", tags=["users"])


# @router.get("/available", response_model=list[OnlineUser])
# def get_available_users(db: Session = Depends(get_db)):
#     """
#     Returns all designers, tailors, boutique owners.
#     Reads from Django's users table directly.
#     Online users appear first.
#     """
#     result = db.execute(
#         text("""
#             SELECT id, email, first_name, last_name, role,
#                    profile_picture, business_name
#             FROM users
#             WHERE role IN ('designer', 'tailor', 'boutique')
#               AND is_active = true
#             ORDER BY first_name
#         """)
#     )
#     rows = result.mappings().all()
#     online_ids = get_online_user_ids()

#     users = [
#         OnlineUser(
#             id=row["id"],
#             email=row["email"],
#             first_name=row["first_name"],
#             last_name=row["last_name"],
#             role=row["role"],
#             profile_picture=row["profile_picture"],
#             business_name=row["business_name"],
#             is_online=row["id"] in online_ids,
#         )
#         for row in rows
#     ]

#     # Online users first, then alphabetical
#     users.sort(key=lambda u: (not u.is_online, u.first_name.lower()))
#     return users

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.redis_client import get_online_user_ids
from app.schemas import OnlineUser
from typing import Optional

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/available", response_model=list[OnlineUser])
def get_available_users(
    current_user_role: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Returns available users based on who is asking:
    - Designers / tailors / boutique → see customers + each other
    - Customers → see designers, tailors, boutique owners only
    - No role passed → return all active users (safe fallback)
    Online users appear first.
    """

    PROFESSIONAL_ROLES = ('designer', 'tailor', 'boutique')
    CUSTOMER_ROLES = ('customer',)  # ← adjust if your DB uses a different value

    if current_user_role and current_user_role in PROFESSIONAL_ROLES:
        # Professionals see customers + other professionals (except themselves filtered on FE)
        role_filter = "AND is_active = true"  # all active users
    elif current_user_role and current_user_role in CUSTOMER_ROLES:
        # Customers only see professionals
        role_filter = "AND role IN ('designer', 'tailor', 'boutique') AND is_active = true"
    else:
        # Fallback: return all active users
        role_filter = "AND is_active = true"

    result = db.execute(
        text(f"""
            SELECT id, email, first_name, last_name, role,
                   profile_picture, business_name
            FROM users
            WHERE 1=1
              {role_filter}
            ORDER BY first_name
        """)
    )
    rows = result.mappings().all()
    online_ids = get_online_user_ids()

    users = [
        OnlineUser(
            id=row["id"],
            email=row["email"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            role=row["role"],
            profile_picture=row["profile_picture"],
            business_name=row["business_name"],
            is_online=row["id"] in online_ids,
        )
        for row in rows
    ]

    # Online users first, then alphabetical
    users.sort(key=lambda u: (not u.is_online, u.first_name.lower()))
    return users