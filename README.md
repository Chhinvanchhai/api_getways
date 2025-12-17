# DynamicModelApi - Example README

## Overview

`DynamicModelApi` is a RESTful API module for Odoo that allows dynamic access to any model (`GET`, `POST`, `PUT`, `DELETE`) with proper permission checks. The API uses **HTTP routes** and handles JSON bodies directly, making it browser- and `curl`-friendly.

---

## Base URL
http://<odoo-host>:8069/api/v1/models/

- Replace `<odoo-host>` with your Odoo instance address.
- Model names are Odoo technical model names, e.g., `hr.department`, `res.partner`.

---

## Endpoints

### 1. GET — Retrieve Records

**Parameters:**

- `page` (optional, default=1): Page number for pagination.
- `limit` (optional, default=20, max=100): Records per page.
- `fields` (optional): Comma-separated list of fields to return.

**Example:**

```bash
    curl -X GET "http://localhost:8069/api/v1/models/hr.department?page=1&limit=5&fields=name,manager_id"

```
Respond data: 
```json

    {
        "model": "hr.department",
        "page": 1,
        "limit": 5,
        "total": 12,
        "result": [
            {"id": 1, "name": "HR", "manager_id": [2, "John Doe"]},
            {"id": 2, "name": "IT", "manager_id": [3, "Jane Smith"]}
        ]
    }

```

### 2. POST — Create Record

```bash
curl --location 'http://localhost:8069/api/v1/models/hr.department' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjksImV4cCI6MTc2NTk0NzE2N30.QzZV3MXje3rIzpVsEdRhgm-KbcuTtVs96E0H6DQ8hFk' \

--data '{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
      "data":{
          "name":"Good"
      }
  }
}
'

```
Respond data: 
```json
    {
        "jsonrpc": "2.0",
        "id": null,
        "result": "<_Response 10 bytes [200 OK]>"
    }

```


### 2. PUT, PATH — Create Record

```bash

curl --location --request PUT 'http://localhost:8069/api/v1/models/hr.department/3' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjksImV4cCI6MTc2NTk0NzE2N30.QzZV3MXje3rIzpVsEdRhgm-KbcuTtVs96E0H6DQ8hFk' \
--data '{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
      "data":{
          "name":"Sale 4444"
      }
  }
}
'
```

Respond data: 
```json
    {
        "jsonrpc": "2.0",
        "id": null,
        "result": "<_Response 10 bytes [200 OK]>"
    }