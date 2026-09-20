# MushroomShed-01 · 菇房出菇台账

食用菌菇房「出菇室环境记录与采收台账」种子项目（非库存 / 电商 / 医院 / 考勤）。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.11 · Flask · SQLAlchemy 2 · Marshmallow · Flask-JWT-Extended · passlib(bcrypt) · gunicorn |
| 前端 | SolidJS · Vite · TypeScript · @solidjs/router |
| 数据库 | MySQL 8（协议兼容原 MariaDB 设计） |
| 部署 | docker-compose · 前端 Nginx 反代 `/api` |

## 端口与账号

| 服务 | 端口 |
| --- | --- |
| 前端 | **3800** |
| 后端 API | **8800** |
| MySQL | **3310** |

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `123456` | admin（场长） |
| `fruiter` | `123456` | fruiter（出菇员） |

数据库：`mushroomshed` / `mushroomshed`，库名 `mushroomshed`。JWT 密钥环境变量 **`JWT_SECRET`**。

## 一键启动

```bash
cd MushroomShed-01
docker compose up --build
```

启动后访问：

- 前端：http://localhost:3800
- 后端健康检查：http://localhost:8800/api/health

后端 entrypoint 流程：等待 MySQL 就绪 → `create_all` 建表 → seed 初始数据 → 启动 gunicorn。

## 功能模块

1. **Auth**：JWT 登录（OAuth2 表单或 JSON），`/api/auth/login`、`/api/auth/me`，`Authorization: Bearer`
2. **Shed 菇房**：`name`、`location`、`notes`；`GET /api/sheds` 每行带 `openHandover`（该棚未关闭的交接班口令，无则 `null`）
3. **Room 出菇室**：`shedId`、`roomCode`、`species`、`capacityBags`、`status(fruiting|idle|sanitize)`；同菇房 `roomCode` 唯一；`PATCH /api/rooms/:id` 可改 `status`
4. **ClimateLog 环境记录**：`roomId`、`recordedAt`、`tempC`、`humidityPct`、`co2Ppm`、`notes`；`humidityPct ∈ [1,100]`，否则 **400**
5. **FlushHarvest 采收**：`roomId`、`harvestedAt`、`flushNo(≥1)`、`weightKg`、`grade(A|B|C)`、`operatorName`；`weightKg > 0`，否则 **400**
6. **Dashboard**：`shedTotal`、`fruitingRoomCount`、`climateLast24h`、`harvestKgLast7d`
7. **ShiftHandover 交接班口令**：`shedId`、`workDate`、`phrase`、`handedBy`、`takenBy`、`closedAt(可空)`

各实体 API：`GET/POST` 列表与创建、`DELETE` 按 ID 删除；出菇室另有 `PATCH /api/rooms/:id` 改状态。

## 交接班口令（ShiftHandover）

- **归日**：`workDate` 由服务端按**东八区（UTC+8）自然日**生成，不设三班分钟表，也不按潮次切班。
- **同棚同日仅一张**：再开返回 **409** 并带回 `existingId`；该棚存在未关闭交接时再开同样 **409**。
- **口令**：`phrase` 去掉全部空白后长度须为 **4–12** 字，否则 **400**；`handedBy` 与 `takenBy` 不得是同一个登录名（**400**）。`handedBy` 缺省取当前登录名。
- **权限**：
  - 开交接 `POST /api/shift-handovers`：登录即可（`admin`、`fruiter` 都可开）。
  - 关交接 `POST /api/shift-handovers/:id/close`：**仅 admin**，其他人 **403**；重复关闭 **409**。
- **未关闭时的 status 限制**：该棚存在 `closedAt` 为空的交接时，其下属出菇室**不准把 `status` 写成 `fruiting`**（新建或 `PATCH` 改写均 **409**，响应带 `handoverId`）；关闭之后才放行。
- **计数一致**：`GET /api/sheds` 每行的 `openHandover` 与 `GET /api/shift-handovers/open-check` 返回的 `total` 共用同一计数来源（`closed_at IS NULL` 查询），两边必然一致。
- 种子数据在「松木岭一号菇房」留一张**未关闭**交接（口令 `松针落筐`，`fruiter → admin`）。

## 前端页面

Login · Dashboard · Sheds · Rooms · ClimateLogs · FlushHarvests（侧边栏布局）

## 本地开发（可选）

```bash
# 数据库（或用 compose 只起 db）
docker compose up -d db

# 后端
cd backend
pip install -r requirements.txt
set DATABASE_URL=mysql+pymysql://mushroomshed:mushroomshed@localhost:3310/mushroomshed
set JWT_SECRET=local-dev-secret
python -c "from app.database import Base, engine; from app import models; Base.metadata.create_all(bind=engine)"
python -c "from app.seed import seed; seed()"
gunicorn wsgi:app --bind 0.0.0.0:8800 --reload

# 前端
cd frontend
npm install
npm run dev
```

## 目录结构

```
MushroomShed-01/
├── docker-compose.yml
├── README.md
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   ├── wsgi.py
│   └── app/
│       ├── __init__.py
│       ├── config.py
│       ├── database.py
│       ├── auth.py
│       ├── seed.py
│       ├── utils.py
│       ├── models/
│       ├── schemas/
│       └── routes/
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── pages/
        ├── components/
        └── api/
```
