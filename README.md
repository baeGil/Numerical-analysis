# Numerical Analysis Solver

Hệ thống AI giải quyết các bài toán numerical analysis phức tạp sử dụng phương pháp "Plan and Solve" với LangGraph

## 🚀 Tính năng chính

- **Phân loại tự động**: Nhận diện loại bài toán (tìm nghiệm, tích phân, hệ phương trình, etc.)
- **Nghiên cứu thuật toán**: Tìm kiếm và đề xuất thuật toán phù hợp
- **Xác thực phương pháp**: Đánh giá và chọn thuật toán tối ưu
- **Lập kế hoạch chi tiết**: Tạo các bước thực thi cụ thể
- **Thực thi tự động**: Chạy code với E2B Sandbox và các tools hỗ trợ
- **Tích hợp nghiên cứu**: Sử dụng ArXiv, Wikipedia, DuckDuckGo Search

## 📋 Yêu cầu hệ thống

- Python 3.8+
- Google Gemini API Key từ Google AI Studio
- E2B API Key (tùy chọn, cho sandbox execution)

## 🛠️ Cài đặt

1. **Clone repository**
```bash
git clone https://github.com/baeGil/Numerical-analysis.git
```

2. **Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

3. **Cấu hình môi trường**
```bash
cp .env.example .env
```

Chỉnh sửa file `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
E2B_API_KEY=your_e2b_api_key_here
```

## 🎯 Cách sử dụng

### Sử dụng cơ bản

Trong file `main.py` tìm tìm đến dòng ở cuối file:
```python 
sample = "Bằng phương pháp dây cung,...
```
Thay sample bằng bài toán cụ thể của bạn 

# Chạy bài toán tìm nghiệm
Ví dụ task sau:
sample = "Bằng phương pháp dây cung, tìm nghiệm gần đúng của phương trình sau: x**3 - x - 1 = 0 trong khoảng phân ly nghiệm (1, 2), với sai số epsilon = 10e-5."

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Classify      │───▶│    Research     │───▶│    Validate     │
│ (Phân loại)     │    │ (Nghiên cứu)    │    │ (Xác thực)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Final       │◀───│      Run        │◀───│      Plan       │
│ (Tổng hợp)      │    │ (Thực thi)      │    │ (Lập kế hoạch)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Các thành phần chính

- **`main.py`**: Entry point và LangGraph workflow
- **`problem_classifier.py`**: Phân loại bài toán
- **`algorithm_researcher.py`**: Nghiên cứu và đề xuất thuật toán
- **`algorithm_map.py`**: Mapping thuật toán theo category
- **`planner.py`**: Tạo kế hoạch thực thi
- **`validator.py`**: Xác thực và chọn thuật toán tốt nhất
- **`tools.py`**: E2B Sandbox tools để thực thi python code
- **`settings.py`**: Cấu hình LLM và môi trường

## 🔧 Cấu hình

### Gemini API
Đăng ký tại [Google AI Studio](https://makersuite.google.com/app/apikey) để lấy API key.

### E2B Sandbox (Tùy chọn)
Đăng ký tại [E2B](https://e2b.dev) để có khả năng chạy code trong sandbox.

### Các loại bài toán được hỗ trợ

- `root_finding`: Tìm nghiệm phương trình
- `linear_system`: Giải hệ phương trình tuyến tính
- `integration`: Tính tích phân
- `ode_ivp`: Phương trình vi phân thường
- `pde`: Phương trình đạo hàm riêng
- `optimization_unconstrained`: Bài toán tối ưu không ràng buộc
- `other`: Các bài toán khác
Hiện tại mình vẫn đang thử nghiệm cho các dạng toán này, không chắc chắn giải được mọi bài toán.

**Returns:**
- `dict`: Thông tin phân loại với các key:
  - `category`: Loại bài toán
  - `short_form`: Biểu thức Python tóm tắt
  - `domain_hint`: Miền xác định
  - `notes`: Ghi chú
  - `original_task`: Đề bài gốc

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Google Gemini](https://ai.google.dev/)
- [E2B](https://e2b.dev)
- [LangChain](https://langchain.com/) 
Và các tools khác như wikipedia, arxiv, duckduckgo...