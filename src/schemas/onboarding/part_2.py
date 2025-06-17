from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from ..base import BaseResponse


# Request/Response models for communication partners
class CommunicationPartner(BaseModel):
    identifier: str  # String identifier based on name
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GetCommunicationPartnersResponse(BaseResponse):
    partners: List[CommunicationPartner]


class SelectCommunicationPartnersRequest(BaseModel):
    partner_ids: List[str] = Field(
        ..., min_length=1, description="List of selected partner identifiers in priority order"
    )


class SelectCommunicationPartnersResponse(BaseResponse):
    selected_count: int
    partner_selections: List[dict]  # Contains identifier, priority info


# Request/Response models for situations
class CommunicationSituation(BaseModel):
    identifier: str  # String identifier based on name
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GetSituationsForPartnerRequest(BaseModel):
    partner_id: str


class GetSituationsResponse(BaseResponse):
    partner_id: str
    partner_name: str
    available_situations: List[CommunicationSituation]
    selected_situations: List[str] = []


class SelectSituationsRequest(BaseModel):
    partner_id: str
    situation_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of selected situation identifiers in priority order",
    )


class SelectSituationsResponse(BaseResponse):
    partner_id: str
    selected_count: int
    situation_selections: List[dict]


# Summary response
class OnboardingPart2SummaryResponse(BaseResponse):
    total_partners_selected: int
    total_situations_selected: int
    selections: List[dict]  # Detailed breakdown by partner
