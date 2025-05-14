# Dự án: AI Agent Tự động Phân phối Thông tin từ PDF qua Email

## Tổng quan

Dự án này xây dựng một hệ thống **AI Agent tự động** có khả năng xử lý các file PDF chứa thông tin nội bộ (ví dụ: văn bản hướng dẫn, quy định mới). Agent sẽ sử dụng trí tuệ nhân tạo để hiểu nội dung file, xác định đối tượng người dùng phù hợp dựa trên vai trò của họ trong tổ chức, sau đó tự động gửi email chứa tóm tắt nội dung và file PDF gốc đến đúng những người dùng đó thông qua một Mail Control Panel (MCP) Server chuyên dụng.

Hệ thống hoạt động hoàn toàn tự động, được kích hoạt khi có file PDF mới xuất hiện tại một nguồn đầu vào được giám sát (ví dụ: một thư mục nóng).

## Tính năng nổi bật

* **Tự động Phát hiện File:** Theo dõi nguồn đầu vào để nhận biết file PDF mới cần xử lý.
* **Xử lý PDF mạnh mẽ:** Trích xuất văn bản từ các định dạng PDF khác nhau.
* **Phân tích Nội dung Thông minh (sử dụng RAG):**
    * Tóm tắt tự động nội dung chính và các hướng dẫn quan trọng trong PDF.
    * Xác định tự động các vai trò hoặc bộ phận người dùng trong tổ chức mà tài liệu này liên quan.
* **Quản lý Người dùng với MongoDB:** Kết nối và truy vấn cơ sở dữ liệu MongoDB chứa thông tin người dùng (tên, vai trò, email).
* **Đối chiếu Vai trò:** Tìm kiếm và lọc danh sách người dùng dựa trên các vai trò được AI xác định.
* **Tự động Chuẩn bị Email:** Tạo nội dung email bao gồm bản tóm tắt từ AI và file PDF gốc đính kèm cho từng người nhận.
* **Gửi Email đáng tin cậy qua MCP:** Tích hợp với MCP Server để gửi email hàng loạt một cách hiệu quả và chuyên nghiệp.
* **Sử dụng Công nghệ AI hiện đại:** Tận dụng Ollama (cho LLM và Embeddings) và LangChain để xây dựng pipeline xử lý RAG.

## Kiến trúc Tổng thể

Hệ thống bao gồm các thành phần chính sau và tương tác theo luồng:

+-----------------+      +-----------------+      +-------------------+
|   Input Trigger |----->|   AI Agent Core |----->| Module RAG (Ollama, LangChain, Chroma) |
| (Folder Watcher,|      | (Engine Xử lý)  |      |                   |
|    API, etc.)   |      |                 |      |  - Đọc PDF        |
+-----------------+      |                 |      |  - Tạo Vector DB  |
|                 |      |  - Phân tích & Gán Role (qua LLM) |
|                 |      +---------+---------+
|                 |                |
|                 |          Kết quả Phân tích (Tóm tắt, Roles)
|                 |                |
|                 |      +---------+---------+
|                 |----->| Module Truy vấn MongoDB |
|                 |      | (Tìm người dùng theo Role) |
|                 |      +---------+---------+
|                 |                |
|                 |          Danh sách Người dùng mục tiêu
|                 |                |
|                 |      +---------+---------+
|                 |----->| Module Chuẩn bị Email |
|                 |      |                   |
|                 |      +---------+---------+
|                 |                |
|                 |          Email đã hoàn chỉnh
|                 |                |
|                 |      +---------+---------+      +-----------------+
|                 |----->| Module Gửi Email qua MCP |----->|   MCP Server    |
|                 |      |                   |      | (Gửi Email đi)  |
|                 |      +-------------------+      +-----------------+
|                 |
|                 | (Optional)
|                 |      +-----------------+
|                 +----->|   Module Dọn dẹp|
|                      | (Xóa Vector DB tạm) |
|                      +-----------------+


Thành phần độc lập:
* **Cơ sở dữ liệu MongoDB:** Lưu trữ thông tin người dùng, được truy cập bởi Module Truy vấn MongoDB.
* **MCP Server:** Nền tảng gửi email, được kết nối bởi Module Gửi Email qua MCP.

## Luồng Xử lý Tự động Chi tiết

Khi Input Trigger phát hiện một file PDF mới, AI Agent sẽ thực hiện chuỗi các bước sau:

1.  **Phát hiện & Tiếp nhận:** Input Trigger (ví dụ: một script theo dõi thư mục) thông báo cho AI Agent về đường dẫn của file PDF mới. Agent tiếp nhận file này.
2.  **Xử lý File PDF cho RAG:** Agent gọi Module Đọc & Xử lý PDF để mở file, trích xuất toàn bộ nội dung văn bản và chia thành các đoạn nhỏ (chunks).
3.  **Tạo Vector Database tạm thời:** Agent sử dụng Module Tạo & Truy vấn Vector Database (dựa trên ChromaDB) để tạo các vector nhúng (embeddings) cho các chunks văn bản bằng cách gọi Ollama Embeddings (`nomic-embed-text`). Một Vector Database tạm thời cho riêng file PDF này được thiết lập (có thể trên disk hoặc trong bộ nhớ).
4.  **Phân tích Nội dung & Xác định Role bằng RAG:** Agent sử dụng Module Phân tích Nội dung bằng LLM. Nó tạo ra các prompt cụ thể và chạy chúng thông qua LangChain chain kết nối LLM (một model Ollama Chat) với Vector Database tạm thời vừa tạo.
    * **Prompt Tóm tắt:** "Dựa vào tài liệu này, hãy tóm tắt ngắn gọn các ý chính và hướng dẫn quan trọng nhất."
    * **Prompt Xác định Role:** "Dựa vào nội dung của tài liệu này, những vai trò (role) nào trong công ty (ví dụ: Kỹ sư, Nhân sự, Quản lý, Toàn bộ nhân viên) sẽ cần nhận thông tin này? Chỉ liệt kê các role, phân tách bằng dấu phẩy."
    * Agent nhận và xử lý phản hồi từ LLM để lấy ra bản tóm tắt nội dung và một danh sách các `role` liên quan.
5.  **Tìm kiếm Người dùng Mục tiêu:** Agent kết nối đến CSDL MongoDB. Sử dụng danh sách các `role` từ bước 4, nó thực hiện truy vấn trên collection `users` trong MongoDB để lấy thông tin (tên, email) của tất cả người dùng có `role` khớp.
    * *Ví dụ truy vấn:* `db.collection('users').find({ role: { $in: ['RoleA', 'RoleB', ...] } }, { name: 1, email: 1 })`
6.  **Chuẩn bị Email:** Agent lặp qua danh sách người dùng mục tiêu. Với mỗi người dùng, nó tạo ra một cấu trúc email hoàn chỉnh, bao gồm địa chỉ email người nhận, chủ đề, nội dung email (sử dụng bản tóm tắt từ bước 4, có thể cá nhân hóa bằng tên người dùng) và đính kèm file PDF gốc.
7.  **Gửi Email Tự động:** Agent sử dụng Module Gửi Email qua MCP để kết nối đến MCP Server (qua API hoặc SMTP) và gửi từng email đã chuẩn bị ở bước 6 đi. MCP Server xử lý quá trình gửi thực tế.
8.  **(Tùy chọn) Dọn dẹp:** Sau khi gửi email thành công, Agent có thể xóa Vector Database tạm thời liên quan đến file PDF đã xử lý khỏi ChromaDB để giải phóng tài nguyên.

## Vai trò của Kỹ thuật RAG trong Dự án này

Trong hệ thống tự động này, RAG không được dùng để xây dựng giao diện hỏi đáp tương tác trực tiếp với người dùng cuối như trong các ứng dụng RAG thông thường. Thay vào đó, RAG đóng vai trò là một **công cụ phân tích thông minh** bên trong Agent, giúp:

* Đọc hiểu ngữ nghĩa sâu sắc hơn nội dung PDF so với chỉ trích xuất văn bản thô.
* Tự động tạo ra bản tóm tắt chất lượng cao của tài liệu.
* Tự động xác định các vai trò hoặc bộ phận liên quan dựa trên ngữ cảnh của tài liệu, thông qua việc truy vấn Vector Database bằng LLM với các prompt phân loại được thiết kế.

## Các Thành phần Kỹ thuật Chính và Thư viện/Công cụ

Để xây dựng hệ thống này, các thành phần và công cụ chính bao gồm:

* **Ngôn ngữ Lập trình:** Python là lựa chọn phổ biến và phù hợp.
* **Framework AI/ML:**
    * **LangChain:** Để xây dựng và điều phối pipeline xử lý (loading, splitting, embedding, querying, chaining LLM).
    * **Ollama:** Để chạy các mô hình AI cục bộ. Cần ít nhất:
        * Một **Embedding Model** (ví dụ: `nomic-embed-text`) để tạo vector nhúng.
        * Một **Chat Model** (ví dụ: `llama2`, `mistral`, `gemma`) để thực hiện các tác vụ tóm tắt và xác định vai trò thông qua prompt.
* **Vector Database:** **ChromaDB** là một lựa chọn nhẹ nhàng và phù hợp để lưu trữ tạm thời hoặc ngắn hạn các vector nhúng của các file PDF riêng lẻ đang được xử lý.
* **Cơ sở dữ liệu Người dùng:** **MongoDB** để lưu trữ thông tin người dùng.
* **MCP Server:** Nền tảng hoặc dịch vụ gửi email (cần có quyền truy cập và thông tin xác thực: API Key, SMTP details...).
* **Thư viện xử lý PDF:** Các thư viện Python như `PyPDF2`, `PyMuPDF` (fitz), hoặc `pdfminer.six` để đọc và trích xuất nội dung từ file PDF. `unstructured` hoặc `pdfplumber` cũng có thể hữu ích (như trong code mẫu).
* **Thư viện kết nối MongoDB:** `pymongo` để tương tác với MongoDB.
* **Thư viện gửi Email:** `smtplib` (nếu dùng SMTP) hoặc thư viện client cụ thể cho API của MCP Server.
* **Cơ chế Input Trigger:**
    * Theo dõi thư mục: Thư viện như `watchdog`.
    * API Endpoint: Sử dụng framework web nhẹ như Flask hoặc FastAPI để nhận file qua HTTP request.
    * Message Queue Client: Tương tác với Kafka, RabbitMQ, v.v.

## Yêu cầu & Cài đặt

1.  Cài đặt **Python** (phiên bản 3.8+).
2.  Cài đặt và chạy **Ollama** với các model cần thiết (`ollama pull nomic-embed-text`, `ollama pull <chat_model_name>`).
3.  Cài đặt và chạy **MongoDB Server**.
4.  Có quyền truy cập vào **MCP Server** và các thông tin xác thực cần thiết.
5.  Cài đặt các thư viện Python: `pip install langchain-core langchain-community langchain-ollama chromadb pymongo PyPDF2 "unstructured[pdf]" watchdog python-dotenv` (hoặc các thư viện tương đương tùy chọn).
6.  Thiết lập nguồn đầu vào (ví dụ: tạo thư mục `input_pdfs`).

## Cấu hình

Hệ thống cần được cấu hình các thông số sau, nên được lưu trữ trong một file cấu hình riêng biệt (ví dụ: `.env`, `config.yaml`):

* Thông tin kết nối MongoDB (URI, username, password, database name).
* Thông tin kết nối MCP Server (API Key, Endpoint URL, SMTP host, port, username, password...).
* Tên model Ollama cho Embeddings và Chat.
* Đường dẫn thư mục đầu vào được theo dõi (nếu dùng Folder Watcher).
* Các prompt template cho tác vụ tóm tắt và xác định role (có thể tinh chỉnh).
* Cấu hình chunking cho RecursiveCharacterTextSplitter (kích thước chunk, chồng lấp).

## Xử lý Lỗi & Logging

Đây là các khía cạnh cực kỳ quan trọng cho một hệ thống tự động:

* **Xử lý Lỗi:** Cần triển khai các khối `try...except` tại mọi bước có thể xảy ra lỗi (đọc file, kết nối DB, truy vấn CSDL, gọi Ollama, kết nối MCP, gửi mail thất bại). Cần có chiến lược thử lại hoặc thông báo lỗi (ví dụ: chuyển file PDF lỗi sang thư mục `error_pdfs`).
* **Logging:** Ghi lại chi tiết hoạt động của Agent (thời điểm nhận file, tên file, kết quả phân tích, danh sách người nhận, trạng thái gửi email thành công/thất bại) vào file log hoặc hệ thống logging tập trung để dễ dàng giám sát và debug.

## Sử dụng

Sau khi cài đặt và cấu hình, chạy script chính của AI Agent (ví dụ: `python agent_main.py`). Agent sẽ bắt đầu theo dõi nguồn đầu vào. Khi một file PDF mới được đặt vào nguồn đó, Agent sẽ tự động xử lý nó theo luồng đã mô tả và gửi email đến người dùng mục tiêu.

## Thách thức Tiềm năng
* Độ chính xác của việc trích xuất văn bản từ PDF phức tạp hoặc PDF dạng ảnh (cần tích hợp OCR mạnh mẽ).
* Độ chính xác của AI trong việc tóm tắt và xác định vai trò (phụ thuộc vào chất lượng model Ollama và prompt engineering).
* Xử lý số lượng file PDF lớn và số lượng người dùng lớn (hiệu năng xử lý, giới hạn của MCP Server).
* Bảo mật dữ liệu người dùng và thông tin xác thực các dịch vụ.
* Quản lý phiên bản của Vector Database nếu cần lưu trữ lâu dài.


## Luồng xử lý tổng quan

Hệ thống hoạt động theo luồng tự động chính sau:

**Watcher (giám sát thư mục) → Phát hiện PDF mới → Gọi RAG Processor → Trả về Tóm tắt nội dung + Các Role liên quan → Gọi MongoDB Client → Tìm kiếm danh sách Users theo Roles → Gọi Mailer → Gửi Email đến Users → Archive (Lưu trữ/Di chuyển) file PDF đã xử lý.**

## Tính năng chính

* **Tự động hóa hoàn toàn:** Agent chạy nền, tự động xử lý file PDF mới mà không cần can thiệp thủ công.
* **Phân tích Nội dung Thông minh (RAG):**
    * Trích xuất và hiểu ngữ nghĩa nội dung PDF.
    * Tự động tóm tắt nội dung chính của tài liệu.
    * Tự động xác định các vai trò (role) người dùng hoặc bộ phận phù hợp dựa trên nội dung PDF.
* **Quản lý Người dùng:** Tích hợp với cơ sở dữ liệu **MongoDB** để lưu trữ và truy vấn thông tin người dùng (tên, role, email).
* **Phân phối Thông tin Chính xác:** Tìm kiếm và gửi email chỉ đến những người dùng có vai trò liên quan được xác định bởi AI.
* **Email Tự động:** Chuẩn bị và gửi email bao gồm tóm tắt nội dung (do AI tạo) và file PDF gốc.
* **Gửi Mail tin cậy:** Sử dụng **MCP Server** (qua HTTP API) cho việc gửi email hàng loạt hiệu quả, hỗ trợ cả chế độ gửi đồng bộ và bất đồng bộ.
* **Công nghệ AI hiện đại:** Sử dụng **Ollama** cho các mô hình LLM và Embeddings, **LangChain** để xây dựng pipeline RAG, và **ChromaDB** để lưu trữ vector tạm thời.
* **Giao diện thử nghiệm (Streamlit UI):** Cung cấp giao diện web đơn giản để tải file thủ công, xem kết quả phân tích (tóm tắt, role), và xem bảng trạng thái gửi email.
* **Thiết kế Module hóa:** Cấu trúc mã nguồn rõ ràng với các module riêng biệt cho từng chức năng (Watcher, RAG, DB, Mailer, Logging, UI).

## Cấu trúc thư mục

.
├── .env.example              # File mẫu cấu hình biến môi trường
├── requirements.txt          # Danh sách thư viện Python cần cài đặt
├── watcher.py                # Module giám sát thư mục đầu vào và kích hoạt quy trình
├── rag_processor.py          # Module xử lý RAG: đọc PDF, build vector DB, tóm tắt, xác định roles
├── db_client.py              # Module tương tác với MongoDB để tìm kiếm người dùng
├── mailer.py                 # Module gửi email thông qua MCP Server (HTTP API)
├── streamlit_app.py          # Giao diện người dùng Streamlit cho mục đích test và hiển thị kết quả
└── utils/                    # Thư mục chứa các tiện ích chung
└── logger.py             # Module cấu hình và sử dụng logging

Có thể thêm các thư mục khác cho file đầu vào, file đã xử lý, file lỗi, etc.
├── input_pdfs/
├── processed_pdfs/
└── error_pdfs/

## Các Module Chính và Vai trò

* `watcher.py`:
    * Chức năng: Giám sát một thư mục được cấu hình. Khi phát hiện file PDF mới, nó sẽ kích hoạt luồng xử lý chính bằng cách gọi các module khác (`rag_processor`, `db_client`, `mailer`).
    * Sử dụng thư viện như `watchdog` để giám sát hiệu quả.
* `rag_processor.py`:
    * Chức năng: Xử lý nội dung file PDF sử dụng pipeline RAG.
    * Các bước thực hiện: Đọc file PDF (dùng thư viện như `unstructured` hoặc `pdfplumber`), chia nhỏ văn bản thành các chunks (dùng `RecursiveCharacterTextSplitter`), tạo vector nhúng cho các chunks bằng Ollama Embeddings (`nomic-embed-text`), lưu trữ vector vào Vector Database tạm thời (ChromaDB).
    * Sử dụng LangChain chains để kết nối Ollama Chat Model với Vector Database tạm thời nhằm thực hiện các truy vấn đặc biệt:
        * Prompt tóm tắt nội dung.
        * Prompt xác định các `role` liên quan dựa trên ngữ cảnh.
    * Trả về bản tóm tắt và danh sách các `role` đã xác định.
* `db_client.py`:
    * Chức năng: Quản lý kết nối và tương tác với cơ sở dữ liệu MongoDB.
    * Cung cấp phương thức để tìm kiếm danh sách người dùng từ collection `users` dựa trên danh sách các `role` được cung cấp bởi `rag_processor`.
    * Sử dụng thư viện `pymongo`.
* `mailer.py`:
    * Chức năng: Gửi email thông qua kết nối đến MCP Server.
    * Triển khai sử dụng HTTP API của MCP Server (nếu có) hoặc giao thức SMTP.
    * Cung cấp các hàm gửi email, bao gồm cả `send_email_async` (để gửi không đồng bộ, không chặn luồng chính của Agent) và `send_email_sync` (một wrapper hoặc hàm gửi đồng bộ đơn giản).
    * Cần cấu hình các thông tin kết nối và xác thực của MCP.
* `streamlit_app.py`:
    * Chức năng: Cung cấp giao diện người dùng đồ họa đơn giản để:
        * Tải lên file PDF thủ công.
        * Xem bản tóm tắt nội dung và danh sách `role` do `rag_processor` xử lý từ file đã tải.
        * Hiển thị danh sách người dùng được tìm thấy từ MongoDB dựa trên `role` đó.
        * Hiển thị bảng kết quả gửi mail cho từng người dùng (status, preview nội dung email).
    * Đây là công cụ hỗ trợ test và demo, không phải giao diện chính cho Agent chạy tự động.
* `utils/logger.py`:
    * Chức năng: Cấu hình hệ thống logging tập trung cho toàn bộ dự án.
    * Giúp ghi lại các thông tin quan trọng, cảnh báo, và lỗi xảy ra trong quá trình hoạt động của Agent.

## Yêu cầu Hệ thống

* Python 3.8+
* Ollama Server đang chạy và có các model cần thiết (embedding model: `nomic-embed-text`, ít nhất một chat model).
* MongoDB Server đang chạy.
* Truy cập đến MCP Server (qua HTTP API hoặc SMTP) với thông tin xác thực hợp lệ.
* Các thư viện Python được liệt kê trong `requirements.txt`.

## Cài đặt

1.  Clone repository về máy cục bộ của bạn.
2.  Điều hướng đến thư mục gốc của dự án.
3.  Cài đặt các thư viện Python cần thiết:
    ```bash
    pip install -r requirements.txt
    ```
4.  Cấu hình biến môi trường: Tạo một file `.env` trong thư mục gốc dựa trên file

## Sử dụng
### Có hai cách để chạy hệ thống:
Chế độ Tự động (Production):
Chạy watcher script:
```bash
python watcher.py
```
Agent sẽ chạy nền, giám sát thư mục đầu vào. Khi bạn đặt file PDF vào thư mục đó, quy trình xử lý tự động sẽ được kích hoạt. Kết quả (log, trạng thái gửi mail) sẽ được ghi vào log file (được cấu hình trong utils/logger.py).
Chế độ Thủ công / Thử nghiệm (Streamlit UI):
Chạy ứng dụng Streamlit:
```Bash
streamlit run streamlit_app.py
```
---
