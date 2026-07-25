# 19_API_Request_Response.md

# API Request & Response Standards

## Request Format

Content-Type:
application/json

---

## Success Response

{
    "success": true,
    "message": "",
    "data": {}
}

---

## Error Response

{
    "success": false,
    "message": "",
    "error": {}
}

---

## HTTP Status Codes

200 OK

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

500 Internal Server Error