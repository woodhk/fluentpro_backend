# API Versioning Guide

## Versioning Strategy

FluentPro API uses **URL versioning** with the following format:
```
https://api.fluentpro.com/api/v{major}/
```

### Version Lifecycle

1. **Development** (v2-dev): New features under development
2. **Beta** (v2-beta): Feature complete, testing in progress
3. **Stable** (v2): Production ready, fully supported
4. **Deprecated** (v1): Old version, maintenance only
5. **Sunset** (v0): No longer supported

### Breaking Changes

The following changes require a new major version:

- Removing endpoints
- Removing or renaming request/response fields
- Changing field types
- Adding required fields without defaults
- Changing HTTP status codes
- Changing error response format

### Non-Breaking Changes

The following can be added to existing versions:

- Adding new endpoints
- Adding optional request fields
- Adding response fields
- Adding new HTTP methods to existing endpoints
- Changing internal implementation

## Migration Process

### For API Consumers

1. **Monitor deprecation notices** in API responses
2. **Test new version** in development environment
3. **Update client code** to handle new response format
4. **Switch to new version** before old version sunset

### Deprecation Notice Format

```json
{
  "data": { ... },
  "meta": {
    "deprecation": {
      "version": "v1",
      "sunset_date": "2024-12-31",
      "migration_guide": "https://docs.fluentpro.com/api/v1-to-v2",
      "message": "This version will be sunset on 2024-12-31. Please migrate to v2."
    }
  }
}
```

## Version Support Policy

- **Current version**: Full support, new features
- **Previous version**: Bug fixes only, 12 months support
- **Deprecated versions**: Security fixes only, 6 months notice before sunset