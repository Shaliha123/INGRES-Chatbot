# 30_REST_API_Details.md

# REST API Details

## Authentication

POST /api/v1/register

POST /api/v1/login

POST /api/v1/logout

GET /api/v1/profile

---

## Chat

POST /api/v1/chat

GET /api/v1/chat/history

DELETE /api/v1/chat/history

---

## Knowledge

GET /api/v1/knowledge

GET /api/v1/knowledge/{id}

POST /api/v1/knowledge

PUT /api/v1/knowledge/{id}

DELETE /api/v1/knowledge/{id}

---

## Documents

POST /api/v1/documents

GET /api/v1/documents

DELETE /api/v1/documents/{id}

---

## Analytics

GET /api/v1/dashboard

GET /api/v1/analytics

---

## Admin

GET /api/v1/users

PUT /api/v1/users/{id}

DELETE /api/v1/users/{id}