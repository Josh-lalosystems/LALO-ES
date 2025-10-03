# LALO AI API Specifications

## Core API Endpoints

### Authentication API

```yaml
/api/v1/auth:
  /login:
    post:
      description: Authenticate user
      request:
        body:
          type: object
          properties:
            username: string
            password: string
      response:
        200:
          type: object
          properties:
            token: string
            user: object
  
  /refresh:
    post:
      description: Refresh authentication token
      request:
        headers:
          Authorization: Bearer token
      response:
        200:
          type: object
          properties:
            token: string

  /verify:
    get:
      description: Verify token validity
      request:
        headers:
          Authorization: Bearer token
      response:
        200:
          type: object
          properties:
            valid: boolean
```

### Document Management API

```yaml
/api/v1/documents:
  /list:
    get:
      description: List available documents
      request:
        headers:
          Authorization: Bearer token
        query:
          folder: string
          type: string
      response:
        200:
          type: array
          items:
            type: object
            properties:
              id: string
              name: string
              type: string
              modified: date
  
  /upload:
    post:
      description: Upload new document
      request:
        headers:
          Authorization: Bearer token
        body:
          type: multipart/form-data
      response:
        200:
          type: object
          properties:
            id: string
            status: string

  /process:
    post:
      description: Process document
      request:
        headers:
          Authorization: Bearer token
        body:
          type: object
          properties:
            id: string
            operation: string
      response:
        200:
          type: object
          properties:
            result: object
```

### Browser Control API

```yaml
/api/v1/browser:
  /navigate:
    post:
      description: Navigate to URL
      request:
        headers:
          Authorization: Bearer token
        body:
          type: object
          properties:
            url: string
            tabId: string
      response:
        200:
          type: object
          properties:
            status: string
            tabId: string

  /interact:
    post:
      description: Interact with page element
      request:
        headers:
          Authorization: Bearer token
        body:
          type: object
          properties:
            tabId: string
            selector: string
            action: string
      response:
        200:
          type: object
          properties:
            status: string
            result: object

  /automate:
    post:
      description: Run automation sequence
      request:
        headers:
          Authorization: Bearer token
        body:
          type: object
          properties:
            script: array
      response:
        200:
          type: object
          properties:
            status: string
            results: array
```

## WebSocket Events

```yaml
events:
  document_update:
    type: object
    properties:
      type: string
      documentId: string
      status: string

  browser_event:
    type: object
    properties:
      type: string
      tabId: string
      event: object

  system_notification:
    type: object
    properties:
      type: string
      level: string
      message: string
```

## Error Responses

```yaml
errors:
  400:
    type: object
    properties:
      error: string
      message: string
      
  401:
    type: object
    properties:
      error: string
      message: string
      
  403:
    type: object
    properties:
      error: string
      message: string
      
  500:
    type: object
    properties:
      error: string
      message: string
```
