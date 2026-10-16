# 前端 · 智面未来（Vue 3 + Vite + Element Plus）

「智面未来」AI岗位胜任力评估智能体的比赛展示前端，包含首页介绍、简历分析、
AI面试对话与胜任力报告四个页面。

- 框架：Vue 3（`<script setup>` SFC）
- 构建：Vite
- UI：Element Plus
- 图表：ECharts（能力雷达图）
- 状态：Pinia
- 路由：Vue Router
- 请求：Axios（统一封装于 `src/api/http.js`）

## 目录结构

```text
src/
├── api/          接口封装（http 拦截器、resume、interview、report、jobs）
├── assets/       静态资源
├── components/   AppLayout、PageHeading 等通用组件
├── router/       路由表
├── stores/       Pinia 状态（app.js）
├── views/        Home 首页 / Resume 简历分析 / Interview AI面试 / Report 评估报告
├── App.vue
├── main.js
└── style.css
```

## 本地开发

```bash
npm install
npm run dev
```

默认地址 `http://localhost:5173`。

开发服务器已在 `vite.config.js` 中把 `/api` 代理到 `http://localhost:8000`，
因此**请先启动后端**：

```bash
cd ../backend
uvicorn app.main:app --reload --port 8000
```

## 构建

```bash
npm run build     # 产物输出到 dist/
npm run preview   # 本地预览构建产物
```

## 接口地址配置

请求基地址默认为 `/api`（走 Vite 代理或生产环境 Nginx 反向代理）。
如需直连后端，在项目根目录新建 `.env.local`：

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

## 生产部署

`Dockerfile` 采用两阶段构建：Node 构建静态资源 → Nginx 托管。
`nginx.conf` 已配置：

- `try_files` 回退到 `index.html`，支持前端路由刷新不 404；
- `/api/` 反向代理至 `backend:8000`（配合根目录 `docker-compose.yml` 使用）。

在仓库根目录执行 `docker compose up --build` 即可同时启动前后端。
