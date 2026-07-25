# 18_Database_Schemas.md

# Database Schemas

## users

Fields

- _id
- name
- email
- role
- profile_image
- created_at
- updated_at

---

## chat_history

Fields

- _id
- user_id
- question
- response
- conversation_id
- timestamp

---

## knowledge_base

Fields

- _id
- title
- category
- content
- keywords
- source
- created_at

---

## documents

Fields

- _id
- title
- filename
- file_type
- uploaded_by
- upload_date
- storage_path

---

## analytics

Fields

- _id
- total_users
- total_chats
- total_documents
- last_updated

---

## logs

Fields

- _id
- user_id
- action
- status
- timestamp

---

## settings

Fields

- _id
- user_id
- theme
- language
- notifications