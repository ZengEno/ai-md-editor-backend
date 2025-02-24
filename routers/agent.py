import uuid
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, status
from routers.auth_utils import get_jwt_payload, oauth2_bearer
from database.db import db
from database.db_classes import AssistantData
from agent.agent_classes import Reflections


agent_router = APIRouter(tags=["Agent Assistant"])


@agent_router.post("/create")
async def create_agent(assistant_name: str, 
                       llm_provider: str, 
                       jwt_token: str = Depends(oauth2_bearer)):
    payload = get_jwt_payload(jwt_token=jwt_token)

    # 1. 检查用户是否存在
    user_id = payload['data']['user_id']
    existing_assistants = await db.assistant_data.find({"user_id": user_id}).to_list(length=None)
    if assistant_name in [assistant['assistant_name'] for assistant in existing_assistants]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Assistant name already exists")
    
    # 2. 创建助手
    assistant_id = str(uuid.uuid4())
    assistant_data = AssistantData(
        user_id=user_id,
        assistant_id=assistant_id,
        assistant_name=assistant_name,
        llm_provider=llm_provider, 
        reflections=Reflections(style_guidelines=[], general_facts=[]),
        custom_actions=None
    )

    # 3. 保存助手
    result = await db.assistant_data.insert_one(assistant_data.model_dump())
    if result.inserted_id:
        # 更新用户助手列表
        await db.user_profiles.update_one(
            {"user_id": user_id},
            {"$push": {"assistant_info_list": {"assistant_id": assistant_id, 
                                               "assistant_name": assistant_name}}}
        )

        # 返回助手
        return {"messages": "Assistant created successfully",
                "assistant_id": assistant_id,
                "assistant_name": assistant_name,
                "llm_provider": llm_provider}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail="Failed to create assistant")
    


@agent_router.post("/delete")
async def delete_agent(assistant_id: str, 
                       jwt_token: str = Depends(oauth2_bearer)):
    payload = get_jwt_payload(jwt_token=jwt_token)
    user_id = payload['data']['user_id']
    result = await db.assistant_data.delete_one({"assistant_id": assistant_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Assistant not found")
    return {"messages": "Assistant deleted successfully"}


@agent_router.get("/list")
async def list_agents(jwt_token: str = Depends(oauth2_bearer)):
    payload = get_jwt_payload(jwt_token=jwt_token)
    user_id = payload['data']['user_id']
    assistants = await db.assistant_data.find({"user_id": user_id}).to_list(length=None)
    if not assistants:
        return []
    
    assistants = [AssistantData(**assistant) for assistant in assistants]

    return assistants


@agent_router.post("/update")
async def update_agent(assistant_data: AssistantData, 
                       jwt_token: str = Depends(oauth2_bearer)):
    payload = get_jwt_payload(jwt_token=jwt_token)
    user_id = payload['data']['user_id']
    assistant_data.user_id = user_id
    assistant_id=assistant_data.assistant_id
    result = await db.assistant_data.update_one({"assistant_id": assistant_id, "user_id": user_id}, 
                                       {"$set": assistant_data.model_dump()})
    if result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail="Failed to update assistant, check assistant_id and user_id")
    return {"messages": "Assistant updated successfully"}



