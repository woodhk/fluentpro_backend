from typing import List, Dict, Any, Optional
from uuid import UUID
from supabase import Client
from ..base import SupabaseRepository
from ...core.logging import get_logger

logger = get_logger(__name__)


class CommunicationRepository(SupabaseRepository):
    """Repository for communication partners and situations."""
    
    def __init__(self, db: Client):
        super().__init__(db, "communication_partners")
        self.user_partners_table = "user_communication_partners"
        self.units_table = "units"
        self.user_partner_units_table = "user_partner_units"
    
    async def get_all_active_partners(self) -> List[Dict[str, Any]]:
        """Get all active communication partners."""
        result = self.db.table(self.table_name)\
            .select("*")\
            .eq("is_active", True)\
            .order("name")\
            .execute()
        return result.data or []
    
    async def get_all_active_units(self) -> List[Dict[str, Any]]:
        """Get all active communication situations/units."""
        result = self.db.table(self.units_table)\
            .select("*")\
            .eq("is_active", True)\
            .order("name")\
            .execute()
        return result.data or []
    
    async def get_user_selected_partners(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's selected communication partners with priority."""
        result = self.db.table(self.user_partners_table)\
            .select("*, communication_partners!inner(*)")\
            .eq("user_id", user_id)\
            .order("priority")\
            .execute()
        return result.data or []
    
    async def save_user_partner_selections(
        self, 
        user_id: str, 
        partner_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Save user's communication partner selections with priority."""
        # First, delete existing selections
        self.db.table(self.user_partners_table)\
            .delete()\
            .eq("user_id", user_id)\
            .execute()
        
        # Insert new selections with priority
        records = []
        for priority, partner_id in enumerate(partner_ids, start=1):
            records.append({
                "user_id": user_id,
                "communication_partner_id": partner_id,
                "priority": priority
            })
        
        if records:
            result = self.db.table(self.user_partners_table)\
                .insert(records)\
                .execute()
            return result.data or []
        return []
    
    async def get_user_situations_for_partner(
        self, 
        user_id: str, 
        partner_id: str
    ) -> List[Dict[str, Any]]:
        """Get user's selected situations for a specific partner."""
        result = self.db.table(self.user_partner_units_table)\
            .select("*, units!inner(*)")\
            .eq("user_id", user_id)\
            .eq("communication_partner_id", partner_id)\
            .order("priority")\
            .execute()
        return result.data or []
    
    async def save_user_partner_situations(
        self,
        user_id: str,
        partner_id: str,
        unit_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Save user's situation selections for a specific partner."""
        # First, delete existing selections for this partner
        self.db.table(self.user_partner_units_table)\
            .delete()\
            .eq("user_id", user_id)\
            .eq("communication_partner_id", partner_id)\
            .execute()
        
        # Insert new selections with priority
        records = []
        for priority, unit_id in enumerate(unit_ids, start=1):
            records.append({
                "user_id": user_id,
                "communication_partner_id": partner_id,
                "unit_id": unit_id,
                "priority": priority,
                "is_custom": False
            })
        
        if records:
            result = self.db.table(self.user_partner_units_table)\
                .insert(records)\
                .execute()
            return result.data or []
        return []
    
    async def get_user_complete_selections(self, user_id: str) -> Dict[str, Any]:
        """Get complete overview of user's selections."""
        # Get partners with their situations
        partners = await self.get_user_selected_partners(user_id)
        
        result = {
            "user_id": user_id,
            "partners": []
        }
        
        for partner in partners:
            partner_id = partner["communication_partner_id"]
            situations = await self.get_user_situations_for_partner(user_id, partner_id)
            
            result["partners"].append({
                "partner": partner["communication_partners"],
                "priority": partner["priority"],
                "situations": [
                    {
                        "unit": sit["units"],
                        "priority": sit["priority"]
                    }
                    for sit in situations
                ]
            })
        
        return result