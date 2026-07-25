# 12_API_Contracts.md

# API Contracts

Base URL

/api/v1

---

Authentication

POST /register

POST /login

POST /logout

GET /profile

---

Chat

POST /chat

GET /history

DELETE /history

---

Knowledge Base

GET /knowledge

GET /knowledge/{id}

POST /knowledge

PUT /knowledge/{id}

DELETE /knowledge/{id}

---

Documents

POST /documents

GET /documents

DELETE /documents/{id}

---

Analytics

GET /dashboard

GET /analytics

---

Admin

GET /users

PUT /users/{id}

DELETE /users/{id}