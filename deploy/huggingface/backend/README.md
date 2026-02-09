---
title: Todo Chatbot Backend API
emoji: ✅
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Todo Chatbot — Backend API

FastAPI backend for the Todo Chatbot project. Provides RESTful endpoints for task management with in-memory storage.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/tasks` | List tasks (with filters) |
| POST | `/api/tasks` | Create a task |
| GET | `/api/tasks/{id}` | Get a task |
| PATCH | `/api/tasks/{id}` | Update a task |
| DELETE | `/api/tasks/{id}` | Delete a task |
| POST | `/api/tasks/{id}/complete` | Complete a task |
| GET | `/docs` | Swagger API documentation |

## Headers

All task endpoints require `X-User-ID` header for user context.
