from typing import Dict, Any

class FieldMapper:
    """Map field names between API versions"""
    
    V1_TO_V2_MAPPING = {
        'user_name': 'full_name',
        'user_email': 'email',
        'created': 'created_at',
        'modified': 'updated_at'
    }
    
    V2_TO_V1_MAPPING = {v: k for k, v in V1_TO_V2_MAPPING.items()}
    
    @classmethod
    def map_request_fields(cls, data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """Map request fields between versions"""
        if from_version == 'v1' and to_version == 'v2':
            mapping = cls.V1_TO_V2_MAPPING
        elif from_version == 'v2' and to_version == 'v1':
            mapping = cls.V2_TO_V1_MAPPING
        else:
            return data
        
        mapped_data = {}
        for key, value in data.items():
            new_key = mapping.get(key, key)
            mapped_data[new_key] = value
        
        return mapped_data
    
    @classmethod
    def map_response_fields(cls, data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """Map response fields between versions"""
        return cls.map_request_fields(data, from_version, to_version)