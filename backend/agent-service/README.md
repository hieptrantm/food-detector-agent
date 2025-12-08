# Agent Service - AI Cooking Assistant

## Mô tả

Agent Service là một AI Agent sử dụng LangGraph với MCP (Model Context Protocol) để gợi ý món ăn và tạo hướng dẫn nấu ăn dựa trên các nguyên liệu được phát hiện từ ảnh.

## Tính năng

- **React Agent Pattern**: Agent hoạt động theo mô hình React với khả năng quyết định của con người
- **Human-in-the-Loop**: Người dùng tương tác qua email để chọn món ăn
- **LangGraph State Management**: Quản lý trạng thái workflow phức tạp
- **Email Integration**: Gửi gợi ý và hướng dẫn qua SendGrid
- **OpenAI Integration**: Sử dụng GPT-4 để tạo gợi ý và hướng dẫn

## Quy trình hoạt động

```
1. User upload ảnh → AI Service phát hiện nguyên liệu
                     ↓
2. Agent Service nhận danh sách nguyên liệu
                     ↓
3. LLM gợi ý 3-5 món ăn phù hợp
                     ↓
4. Gửi email cho user với các món ăn gợi ý
                     ↓
5. [HUMAN DECISION] User chọn món qua email link
                     ↓
6. Agent tiếp tục: LLM tạo hướng dẫn chi tiết
                     ↓
7. Phân tích dinh dưỡng, calo, thời gian nấu
                     ↓
8. Gửi email hướng dẫn hoàn chỉnh cho user
```

## API Endpoints

### 1. Start Cooking Session
```http
POST /agent/start
Authorization: Bearer <token>

Request:
{
  "detected_ingredients": [
    {
      "label": "tomato",
      "confidence": 0.95,
      "bbox": [100, 100, 200, 200]
    }
  ]
}

Response:
{
  "request_id": "uuid",
  "status": "success",
  "message": "Đã gửi email gợi ý món ăn",
  "stage": "waiting_selection"
}
```

### 2. Select Dish (via email link)
```http
GET /agent/select-dish?token=<selection_token>&dish_index=0

Response:
{
  "success": true,
  "message": "Đã chọn món. Hướng dẫn sẽ được gửi qua email",
  "request_id": "uuid"
}
```

### 3. Check Status
```http
GET /agent/status/<request_id>
Authorization: Bearer <token>

Response:
{
  "request_id": "uuid",
  "stage": "completed",
  "status": "completed",
  "created_at": "2025-12-07T...",
  "updated_at": "2025-12-07T...",
  "error": null
}
```

## Cấu trúc

```
agent-service/
├── config.py                 # Configuration và prompts
├── main.py                   # FastAPI application
├── requirements.txt
├── Dockerfile
├── .env
└── app/
    ├── models/
    │   └── state.py          # State definitions
    ├── services/
    │   ├── cooking_agent.py  # LangGraph agent
    │   ├── email_service.py  # SendGrid integration
    │   └── state_store.py    # State persistence
    └── controllers/
        └── agent_controller.py  # API endpoints
```

## Environment Variables

```env
OPENAI_API_KEY=your_openai_api_key
SENDGRID_API_KEY=your_sendgrid_api_key
SECRET_KEY=your_secret_key
FROM_EMAIL=your_email@example.com
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
AUTH_SERVICE_URL=http://auth-service:8000
PENDING_REQUESTS_DIR=/app/pending_requests
```

## Cài đặt

### Local Development

```bash
cd backend/agent-service
pip install -r requirements.txt
python main.py
```

### Docker

```bash
cd backend
docker-compose up agent-service
```

## LangGraph Workflow

Agent sử dụng StateGraph với các nodes:

1. **suggest_dishes**: LLM gợi ý món ăn từ nguyên liệu
2. **send_selection_email**: Gửi email cho user chọn món
3. **[WAIT]**: Chờ user phản hồi qua email
4. **generate_recipe**: LLM tạo hướng dẫn chi tiết
5. **send_recipe_email**: Gửi email hướng dẫn

## Prompts Configuration

Tất cả prompts được cấu hình trong `config.py`:

- `SYSTEM_PROMPT`: System prompt cho AI Chef
- `SUGGEST_DISHES_PROMPT`: Prompt gợi ý món ăn
- `GENERATE_RECIPE_PROMPT`: Prompt tạo hướng dẫn nấu
- Email templates: HTML templates cho emails

## State Management

Agent state được lưu trữ dạng file JSON trong `pending_requests/`:

```json
{
  "request_id": "uuid",
  "user_id": "123",
  "stage": "waiting_selection",
  "detected_ingredients": [...],
  "suggested_dishes": [...],
  "awaiting_human_feedback": true,
  ...
}
```

## Testing

```bash
# Start service
docker-compose up agent-service

# Test với curl
curl -X POST http://localhost:8000/agent/start \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "detected_ingredients": [
      {"label": "cà chua", "confidence": 0.95, "bbox": [0,0,100,100]}
    ]
  }'
```

## Notes

- Sử dụng GPT-4o-mini để tối ưu chi phí
- Email selection tokens có thời hạn 24 giờ
- States được lưu persistent trong volume
- Hỗ trợ tiếng Việt hoàn toàn

## Dependencies

- **LangGraph**: Workflow orchestration
- **LangChain**: LLM integration
- **OpenAI**: GPT-4 API
- **SendGrid**: Email service
- **FastAPI**: Web framework
- **Pydantic**: Data validation
