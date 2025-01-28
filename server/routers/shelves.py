from fastapi import APIRouter, HTTPException, Depends
from server.fastapi_auth import get_current_user
from db.firestore import db
from server.models import Shelf, ShelfResponse, ShelfMember
from typing import List
from datetime import datetime

router = APIRouter(tags=["shelves"])

@router.get("/api/shelves/public", response_model=List[ShelfResponse])
def get_public_shelves():
    """
    Получить все публичные полки
    """
    shelves_list = []
    shelves_ref = db.collection("shelves")
    for shelf in shelves_ref.where("public", "==", True).stream():
        shelf_data = shelf.to_dict()
        shelves_list.append({
            "id": shelf.id,
            "name": shelf_data["name"],
            "description": shelf_data.get("description", ""),
            "public": shelf_data["public"],
            "ownerId": shelf_data["ownerId"]
        })
    return shelves_list

@router.get("/api/shelves/my", response_model=List[ShelfResponse])
def get_user_shelves(current_user: dict = Depends(get_current_user)):
    """
    Получить все полки пользователя (где он владелец)
    """
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
        
    shelves_list = []
    shelves_ref = db.collection("shelves")
    for shelf in shelves_ref.where("ownerId", "==", current_user["_id"]).stream():
        shelf_data = shelf.to_dict()
        shelves_list.append({
            "id": shelf.id,
            "name": shelf_data["name"],
            "description": shelf_data.get("description", ""),
            "public": shelf_data["public"],
            "ownerId": shelf_data["ownerId"]
        })
    return shelves_list

@router.get("/api/shelves/member", response_model=List[ShelfResponse])
def get_member_shelves(current_user: dict = Depends(get_current_user)):
    """
    Получить все полки, в которых пользователь является участником
    """
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
        
    # Сначала получаем все ID полок, где пользователь участник
    members_ref = db.collection("shelf_members")
    shelf_ids = []
    for member in members_ref.where("userId", "==", current_user["_id"]).stream():
        shelf_ids.append(member.to_dict()["shelfId"])
    
    # Если нет полок, возвращаем пустой список
    if not shelf_ids:
        return []
    
    # Получаем информацию о каждой полке
    shelves_list = []
    shelves_ref = db.collection("shelves")
    for shelf_id in shelf_ids:
        shelf = shelves_ref.document(shelf_id).get()
        if shelf.exists:  # Проверяем, что полка все еще существует
            shelf_data = shelf.to_dict()
            shelves_list.append({
                "id": shelf.id,
                "name": shelf_data["name"],
                "description": shelf_data.get("description", ""),
                "public": shelf_data["public"],
                "ownerId": shelf_data["ownerId"]
            })
    
    return shelves_list

@router.post("/api/shelves", response_model=ShelfResponse)
def create_shelf(shelf: Shelf, current_user: dict = Depends(get_current_user)):
    """
    Создать новую полку и добавить владельца как участника
    """
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    
    # Создаем полку
    new_shelf = {**shelf.dict(), "ownerId": current_user["_id"]}
    shelves_ref = db.collection("shelves")
    result = shelves_ref.add(new_shelf)
    document_ref = result[1]  # Extract the document reference
    shelf_id = document_ref.id
    
    # Добавляем владельца как участника
    members_ref = db.collection("shelf_members")
    member_data = {
        "shelfId": shelf_id,
        "userId": current_user["_id"],
        "created_at": datetime.utcnow().isoformat()
    }
    members_ref.add(member_data)
    
    return {"id": shelf_id, **new_shelf}

@router.get("/api/shelves/{shelf_id}", response_model=ShelfResponse)
def get_shelf(shelf_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf_ref = db.collection("shelves").document(shelf_id)
    shelf = shelf_ref.get()
    if not shelf.exists:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    shelf_data = shelf.to_dict()
    if not shelf_data["public"] and shelf_data["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    return {
        "id": shelf.id,
        "name": shelf_data["name"],
        "description": shelf_data.get("description", ""),
        "public": shelf_data["public"],
        "ownerId": shelf_data["ownerId"]
    }

@router.post("/api/shelves/{shelf_id}/members", response_model=ShelfMember)
def add_shelf_member(shelf_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf_ref = db.collection("shelves").document(shelf_id)
    shelf = shelf_ref.get()
    if not shelf.exists:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    shelf_data = shelf.to_dict()
    if shelf_data["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    new_member = {"shelfId": shelf_id, "userId": user_id}
    members_ref = db.collection("shelf_members")
    result = members_ref.add(new_member)
    return {"id": result.id, **new_member}

@router.get("/api/shelves/{shelf_id}/members", response_model=List[ShelfMember])
def get_shelf_members(shelf_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf_ref = db.collection("shelves").document(shelf_id)
    shelf = shelf_ref.get()
    if not shelf.exists:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    shelf_data = shelf.to_dict()
    if not shelf_data["public"] and shelf_data["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    members_ref = db.collection("shelf_members")
    members = members_ref.where("shelfId", "==", shelf_id).stream()
    return [{"id": member.id, "shelfId": member.to_dict()["shelfId"], "userId": member.to_dict()["userId"]} for member in members] 