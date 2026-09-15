# Architecture

## Overview

```text
                    Frontend
                       |
                       v
                  FastAPI API
                       |
          +------------+------------+
          |            |            |
          v            v            v
        Auth       Projects        Chat
          |            |            |
          +------------+------------+
                       |
                       v
                  SQLAlchemy
                       |
                       v
                    SQLite
```

## Authentication Flow

```text
Register
   |
   v
Hash Password
   |
   v
Store User
   |
   v
Login
   |
   v
Verify Password
   |
   v
Generate JWT
   |
   v
Client uses JWT for protected APIs
```

## Project Flow

```text
User
 |
 v
Create Project
 |
 v
Project
 ├── Name
 ├── Description
 ├── System Prompt
 └── Status
       |
       v
   active / inactive
```

## Chat Flow

```text
User sends message
        |
        v
Validate JWT
        |
        v
Check Project Ownership
        |
        v
Check Project Status
        |
        +---- inactive ----> Return Error
        |
        v
Load Chat History
        |
        v
Add Current User Message
        |
        v
Send to Groq
(OpenAI-compatible API)
        |
        v
Receive AI Response
        |
        v
Save User + Assistant Messages
        |
        v
Return Response
```

## Data Flow

```text
User
 |
 +----> Project
          |
          +----> Messages
          |
          +----> Files
```

## Error Flow

```text
Invalid JWT
    |
    v
401 Unauthorized

Invalid Project / Ownership
    |
    v
Access Denied

Inactive Project
    |
    v
400 Bad Request

Groq / LLM Failure
    |
    v
502 Bad Gateway
```
