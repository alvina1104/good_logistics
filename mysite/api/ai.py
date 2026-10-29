from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from mysite.api.auth import get_current_user
from mysite.database.db import get_db
from mysite.database.models import User, RoleChoices
from mysite.database.schema import ChatRequest, Action
from mysite.chains.chat import run_chat
from mysite.chains.tools import execute_action

ai_router = APIRouter(prefix="/ai", tags=["AI Chat"])


def ai_user(user: User = Depends(get_current_user)):
    if user.status not in (
        RoleChoices.buyer,
        RoleChoices.seller,
        RoleChoices.manager,
    ):
        raise HTTPException(403, "Нет доступа к AI Chat")

    return user


@ai_router.post("/chat/")
def chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(ai_user),
):
    return run_chat(data.question, db, user)


@ai_router.post("/execute/")
def execute(
    data: Action,
    db: Session = Depends(get_db),
    user: User = Depends(ai_user),
):
    try:
        result = execute_action(db, user, data)

        return {
            "answer": result["message"],
            "items": result.get("items", []),
        }

    except HTTPException:
        db.rollback()
        raise

    except ValidationError:
        db.rollback()
        raise HTTPException(422, "Некорректные данные товара")

    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Нарушены связи данных")

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Ошибка базы данных")
