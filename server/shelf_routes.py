from fastapi import APIRouter, HTTPException, Depends
from server.fastapi_auth import get_current_user
from db.firestore import db
from pydantic import BaseModel

router = APIRouter()

class Shelf(BaseModel):
    name: str
    description: str | None = None
    public: bool = True

@router.post("/api/shelves")
def create_shelf(shelf: Shelf, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    new_shelf = {**shelf.dict(), "ownerId": current_user["_id"]}
    shelves_ref = db.collection("shelves")
    result = shelves_ref.add(new_shelf)
    document_ref = result[1]  # Extract the document reference
    return {"id": document_ref.id, **new_shelf}

@router.get("/api/shelves/{shelf_id}")
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

@router.post("/api/shelves/{shelf_id}/members")
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

@router.get("/api/shelves/{shelf_id}/members")
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

@router.delete("/api/shelves/{shelf_id}/members/{member_id}")
def delete_shelf_member(shelf_id: str, member_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf_ref = db.collection("shelves").document(shelf_id)
    shelf = shelf_ref.get()
    if not shelf.exists:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    shelf_data = shelf.to_dict()
    if shelf_data["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    member_ref = db.collection("shelf_members").document(member_id)
    member = member_ref.get()
    if not member.exists:
        raise HTTPException(status_code=404, detail="Member not found.")
    member_ref.delete()
    return {"message": "Member deleted"}