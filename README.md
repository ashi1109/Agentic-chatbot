# Chatbot Platform

A minimal chatbot platform built with FastAPI, SQLite, and Groq.

The platform allows users to create their own projects (agents), give each project a system prompt, and chat with it. Users can also view their conversation history and upload files to a project.

The main goal of this project was to keep the implementation simple while covering the basic pieces needed for a multi-user chatbot platform.

## Features

- User registration and login
- JWT-based authentication
- Create, view, update, and delete projects
- Each project has its own system prompt
- Project status (`active` / `inactive`)
- Chat with the project using Groq
- Conversation history stored in the database
- Project-level access control
- File upload and file listing for projects
- Simple web interface served directly by FastAPI

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- JWT
- Passlib + bcrypt
- Groq API
- OpenAI Python SDK (used with Groq's OpenAI-compatible API)
- HTML, CSS, JavaScript

## How it works

A project acts as the chatbot/agent.

Each project has:

- Name
- Description
- System prompt
- Status
- Conversation history
- Files associated with it

When a user sends a message, the backend first verifies the user's JWT and checks that the project belongs to that user.

The previous messages for that project are then loaded from the database and sent along with the new message to the LLM.

The LLM response is returned to the user and both sides of the conversation are stored in the database.

### Chat flow

```text
User
  |
  v
Frontend
  |
  v
FastAPI API
  |
  +--> JWT authentication
  |
  +--> Check project ownership
  |
  +--> Check project status
  |
  +--> Load conversation history
  |
  v
Groq API
  |
  v
Save user + assistant messages
  |
  v
Return response
