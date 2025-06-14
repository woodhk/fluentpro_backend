from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from ..base import BaseResponse


# Request/Response models for communication partners
class CommunicationPartner(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GetCommunicationPartnersResponse(BaseResponse):
    partners: List[CommunicationPartner]


class SelectCommunicationPartnersRequest(BaseModel):
    partner_ids: List[UUID] = Field(
        ..., min_length=1, description="List of selected partner IDs in priority order"
    )


class SelectCommunicationPartnersResponse(BaseResponse):
    selected_count: int
    partner_selections: List[dict]  # Contains id, partner_id, priority info


# Request/Response models for situations
class CommunicationSituation(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GetSituationsForPartnerRequest(BaseModel):
    partner_id: UUID


class GetSituationsResponse(BaseResponse):
    partner_id: UUID
    partner_name: str
    available_situations: List[CommunicationSituation]
    selected_situations: List[UUID] = []


class SelectSituationsRequest(BaseModel):
    partner_id: UUID
    situation_ids: List[UUID] = Field(
        ...,
        min_length=1,
        description="List of selected situation IDs in priority order",
    )


class SelectSituationsResponse(BaseResponse):
    partner_id: UUID
    selected_count: int
    situation_selections: List[dict]


# Summary response
class OnboardingPart2SummaryResponse(BaseResponse):
    total_partners_selected: int
    total_situations_selected: int
    selections: List[dict]  # Detailed breakdown by partner
