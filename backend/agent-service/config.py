import os
from dotenv import load_dotenv

load_dotenv()

# API Keys and Secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "hiep-tran-thanh-mieu")

# Email Configuration
FROM_EMAIL = os.getenv("FROM_EMAIL", "quochaitnpl04@gmail.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

# Agent Prompts
SYSTEM_PROMPT = """Bạn là một AI chef chuyên nghiệp, giúp người dùng nấu các món ăn từ nguyên liệu có sẵn.
Nhiệm vụ của bạn là:
1. Phân tích danh sách nguyên liệu đã được phát hiện
2. Đề xuất các món ăn phù hợp có thể nấu từ những nguyên liệu đó
3. Sau khi người dùng chọn món, cung cấp hướng dẫn chi tiết về cách nấu
4. Phân tích dinh dưỡng và lượng calo của món ăn

Hãy trả lời bằng tiếng Việt một cách thân thiện và chuyên nghiệp."""

SUGGEST_DISHES_PROMPT = """Dựa trên danh sách nguyên liệu sau đây đã được phát hiện từ ảnh:
{ingredients}

Hãy đề xuất 3-5 món ăn phù hợp có thể nấu từ những nguyên liệu này.
Với mỗi món ăn, hãy cung cấp:
1. Tên món ăn
2. Mô tả ngắn gọn về món ăn
3. Độ khó (Dễ/Trung bình/Khó)
4. Thời gian nấu ước tính
5. Nguyên liệu cần thêm (nếu có)

Yêu cầu:
1. Chỉ trả về theo định dạng JSON body như dưới, không kèm mô tả hay lời giải thích nào khác.

Format trả về dưới dạng JSON:
{{
    "dishes": [
        {{
            "name": "Tên món ăn",
            "description": "Mô tả",
            "difficulty": "Dễ|Trung bình|Khó",
            "cooking_time": "X phút",
            "additional_ingredients": ["nguyên liệu 1", "nguyên liệu 2"]
        }}
    ]
}}"""

GENERATE_RECIPE_PROMPT = """Người dùng đã chọn món: {dish_name}

Danh sách nguyên liệu có sẵn:
{ingredients}

Danh sách nguyên liệu cần thêm: 
{additional_ingredients}


Hãy tạo hướng dẫn chi tiết để nấu món này, bao gồm:

1. **Nguyên liệu cần thiết**:
   - Liệt kê tất cả nguyên liệu với số lượng cụ thể
   - Đánh dấu những nguyên liệu đã có sẵn
   - Đánh dấu những nguyên liệu cần mua thêm

2. **Chuẩn bị**:
   - Các bước sơ chế nguyên liệu
   - Công cụ nấu nướng cần thiết

3. **Các bước nấu** (chi tiết từng bước):
   - Bước 1: ...
   - Bước 2: ...
   - ...

4. **Mẹo và lưu ý**:
   - Những điểm cần chú ý khi nấu
   - Cách làm cho món ăn ngon hơn

5. **Phân tích dinh dưỡng** (cho 1 khẩu phần):
   - Lượng calo: X kcal
   - Protein: X g
   - Carbohydrate: X g
   - Fat: X g
   - Chất xơ: X g
   - Vitamin và khoáng chất nổi bật

6. **Thời gian**:
   - Thời gian chuẩn bị: X phút
   - Thời gian nấu: X phút
   - Tổng thời gian: X phút

7. **Số khẩu phần**: X người

Hãy trả lời chi tiết và dễ hiểu, phù hợp cho người mới học nấu ăn."""

EMAIL_DISH_SELECTION_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Món ăn hôm nay của bạn là</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border: 1px solid #e0e0e0; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ padding: 30px 20px; background-color: #ffffff; }}
        .greeting {{ font-size: 16px; margin-bottom: 20px; }}
        .dish-card {{ background-color: #f8f9fa; margin: 20px 0; padding: 20px; border-left: 4px solid #667eea; }}
        .dish-name {{ color: #333; font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
        .dish-info {{ font-size: 14px; color: #555; margin: 8px 0; line-height: 1.5; }}
        .selection-section {{ margin-top: 30px; padding: 20px; background-color: #f0f4ff; border-radius: 8px; text-align: center; }}
        .button {{ display: inline-block; padding: 14px 28px; background-color: #667eea; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 8px 4px; font-weight: 600; border: 2px solid #667eea; }}
        .button:hover {{ background-color: #5568d3; }}
        .footer {{ padding: 20px; text-align: center; color: #666; font-size: 13px; background-color: #f8f9fa; border-top: 1px solid #e0e0e0; }}
        .footer p {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍳 Gợi Ý Món Ăn Cho Bạn</h1>
        </div>
        <div class="content">
            <div class="greeting">
                <p>Xin chào <strong>{username}</strong>,</p>
                <p>Dựa trên các nguyên liệu bạn có: <strong>{ingredients}</strong></p>
                <p>Chúng tôi xin gợi ý những món ăn phù hợp dưới đây:</p>
            </div>
            
            {dishes_html}
            
            <div class="selection-section">
                <p style="font-size: 16px; font-weight: bold; margin-bottom: 15px;">Bạn muốn nấu món nào?</p>
                <p style="font-size: 14px; color: #666; margin-bottom: 20px;">Nhấp vào nút bên dưới để chọn món và nhận hướng dẫn chi tiết</p>
                {selection_buttons}
            </div>
        </div>
        <div class="footer">
            <p>Cảm ơn bạn đã sử dụng dịch vụ UET Foody</p>
            <p>Đây là email tự động, vui lòng không trả lời email này</p>
        </div>
    </div>
</body>
</html>
"""

EMAIL_RECIPE_TEMPLATE = """
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #10B981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: white; padding: 30px; }}
        .section {{ margin: 25px 0; }}
        .section-title {{ color: #10B981; font-size: 20px; font-weight: bold; margin-bottom: 12px; border-bottom: 2px solid #10B981; padding-bottom: 5px; }}
        .ingredient-list {{ list-style: none; padding: 0; }}
        .ingredient-item {{ padding: 8px; margin: 5px 0; background-color: #f0fdf4; border-left: 3px solid #10B981; }}
        .step {{ margin: 15px 0; padding: 15px; background-color: #f9fafb; border-radius: 6px; }}
        .step-number {{ display: inline-block; width: 30px; height: 30px; background-color: #10B981; color: white; text-align: center; line-height: 30px; border-radius: 50%; margin-right: 10px; }}
        .nutrition-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .nutrition-table td {{ padding: 10px; border: 1px solid #e5e7eb; }}
        .nutrition-table tr:nth-child(even) {{ background-color: #f9fafb; }}
        .highlight {{ background-color: #fef3c7; padding: 2px 6px; border-radius: 3px; }}
        .footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #e5e7eb; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>👨‍🍳 Hướng Dẫn Nấu: {dish_name}</h1>
        </div>
        <div class="content">
            {recipe_content}
        </div>
        <div class="footer">
            <p>🍽️ Chúc bạn nấu ăn ngon miệng!</p>
            <p>Email này được gửi tự động từ AI Chef Assistant</p>
        </div>
    </div>
</body>
</html>
"""

# Database/Storage for pending requests
PENDING_REQUESTS_DIR = os.getenv("PENDING_REQUESTS_DIR", "./pending_requests")
