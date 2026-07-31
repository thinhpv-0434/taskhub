# TaskHub API

TaskHub là REST API quản lý workspace, project và task, xây dựng bằng FastAPI,
SQLAlchemy async và JWT authentication.

## Tính năng

- Đăng ký, đăng nhập, refresh token và thông tin người dùng.
- Workspace membership với các role `OWNER`, `EDITOR`, `VIEWER`.
- Phân quyền hệ thống `ADMIN` và phân quyền theo từng workspace.
- Quản lý Project và Task.
- Lọc Task theo status, priority, assignee; hỗ trợ page và limit.
- Gắn Label và thêm Comment vào Task.
- PostgreSQL và Redis khi chạy bằng Docker Compose.
- SQLite mặc định khi chạy local.
- Request logging với `X-Request-ID` và `X-Process-Time`.
- Ruff lint.

## Yêu cầu

### Chạy bằng Docker

- Docker Desktop hoặc OrbStack.
- Docker Compose v2.

### Chạy local

- Python 3.11 trở lên.
- `pip` hoặc `uv`.

## Cách 1: Chạy bằng Docker Compose

Đây là cách setup nhanh nhất. Stack gồm:

| Service | Công nghệ | Port |
| --- | --- | --- |
| `app` | FastAPI/Uvicorn | `${APP_PORT}` → container `8000` |
| `db` | PostgreSQL 16 | Chỉ truy cập trong Docker network |
| `redis` | Redis 7 | Chỉ truy cập trong Docker network |

### 1. Tạo file environment

```bash
cp .env.example .env
```

Nội dung mặc định:

```dotenv
APP_PORT=8000
POSTGRES_DB=taskhub
POSTGRES_USER=taskhub
POSTGRES_PASSWORD=taskhub
SECRET_KEY=replace-with-a-long-random-secret
LOG_LEVEL=INFO
```

Đổi `SECRET_KEY` trước khi dùng ngoài môi trường development. Nếu port 8000 đã
được sử dụng, đổi `APP_PORT`, ví dụ:

```dotenv
APP_PORT=8001
```

### 2. Build và khởi động stack

```bash
docker compose up --build -d
```

Compose sẽ chờ PostgreSQL và Redis healthy trước khi khởi động API.

### 3. Kiểm tra container

```bash
docker compose ps
docker compose logs -f app
```

Cả ba container cần có trạng thái `healthy`.

### 4. Truy cập API

Với `APP_PORT=8000`:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

Nếu đã thay `APP_PORT`, sử dụng port tương ứng trong các URL trên.

Kiểm tra nhanh:

```bash
curl http://localhost:8000/openapi.json
```

### 5. Dừng stack

Giữ lại dữ liệu PostgreSQL và Redis:

```bash
docker compose down
```

Xóa cả container, network và dữ liệu trong named volumes:

```bash
docker compose down --volumes
```

> `--volumes` sẽ xóa dữ liệu local và không thể khôi phục bằng Docker Compose.

## Cách 2: Chạy local với SQLite

Khi không khai báo `DATABASE_URL`, ứng dụng tự dùng file
`app/taskhub.db`. Redis là optional nếu không khai báo `REDIS_URL`.

### 1. Tạo virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Cài dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Hoặc dùng `uv`:

```bash
uv pip install --python .venv/bin/python -r requirements.txt
```

### 3. Khai báo environment tùy chọn

Ứng dụng có thể chạy ngay với cấu hình mặc định. Để thay đổi cấu hình trong
terminal hiện tại:

```bash
export SECRET_KEY="replace-with-a-long-random-secret"
export LOG_LEVEL="INFO"
```

Windows PowerShell:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:LOG_LEVEL = "INFO"
```

### 4. Khởi động API

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Mở <http://localhost:8000/docs>.

Ứng dụng tự khởi tạo các bảng chưa tồn tại khi startup.

## Biến môi trường

| Biến | Mặc định local | Mô tả |
| --- | --- | --- |
| `DATABASE_URL` | SQLite tại `app/taskhub.db` | SQLAlchemy async database URL |
| `REDIS_URL` | Không sử dụng Redis | Redis connection URL |
| `SECRET_KEY` | `secret-key` | Khóa ký JWT; phải đổi ngoài development |
| `JWT_ALGORITHM` | `HS256` | Thuật toán ký JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Thời hạn access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Thời hạn refresh token |
| `LOG_LEVEL` | `INFO` | Mức log: DEBUG, INFO, WARNING, ERROR |
| `APP_PORT` | `8000` | Host port của app trong Docker Compose |
| `POSTGRES_DB` | `taskhub` | Tên database PostgreSQL trong Compose |
| `POSTGRES_USER` | `taskhub` | User PostgreSQL trong Compose |
| `POSTGRES_PASSWORD` | `taskhub` | Password PostgreSQL trong Compose |

Ví dụ URL khi chạy ngoài Compose:

```dotenv
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/taskhub
REDIS_URL=redis://localhost:6379/0
```

## Kiểm tra chất lượng code

Chạy Ruff:

```bash
ruff check .
```

Tự động sửa các lỗi an toàn:

```bash
ruff check . --fix
```

Kiểm tra Python compile:

```bash
python -m compileall -q app alembic
```

## Lệnh Docker thường dùng

Build lại riêng image app:

```bash
docker compose build app
```

Khởi động lại app sau khi đổi environment:

```bash
docker compose up -d app
```

Xem log:

```bash
docker compose logs -f app
docker compose logs -f db
docker compose logs -f redis
```

Mở shell trong app container:

```bash
docker compose exec app sh
```

Kiểm tra PostgreSQL:

```bash
docker compose exec db psql -U taskhub -d taskhub
```

Kiểm tra Redis:

```bash
docker compose exec redis redis-cli ping
```

Kết quả mong đợi:

```text
PONG
```

## Phân quyền

| Role | Quyền |
| --- | --- |
| `ADMIN` | Toàn quyền trên mọi workspace và resource |
| `OWNER` | Quản lý member và CRUD Project/Task trong workspace |
| `EDITOR` | CRUD Project/Task, Label, Comment; không quản lý member |
| `VIEWER` | Chỉ đọc resource trong workspace |

User không thuộc workspace không được đọc hoặc thay đổi resource của workspace.

## Cấu trúc chính

```text
app/
├── api/v1/       # FastAPI routers
├── core/         # Config, auth, permission, logging, middleware
├── db/           # SQLAlchemy models và session
├── schemas/      # Pydantic request/response schemas
└── services/     # Business logic và database operations
alembic/          # Database migration scripts
Dockerfile        # Multi-stage application image
docker-compose.yml
```

## Xử lý lỗi thường gặp

### Không kết nối được Docker daemon

Khởi động Docker Desktop hoặc OrbStack, sau đó kiểm tra:

```bash
docker info
```

### Port đã được sử dụng

Kiểm tra port:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

Đổi `APP_PORT` trong `.env`, sau đó recreate app:

```bash
docker compose up -d app
```

### App không healthy

```bash
docker compose ps
docker compose logs --tail=200 app
```

Kiểm tra riêng dependency:

```bash
docker compose exec db pg_isready -U taskhub -d taskhub
docker compose exec redis redis-cli ping
```
