# 第一阶段：构建前端
FROM node:20-alpine AS frontend-builder

# 设置工作目录
WORKDIR /app/web

# 复制前端依赖文件
COPY web/package.json web/package-lock.json* ./

# 安装前端依赖
RUN npm ci --no-progress

# 复制前端源代码
COPY web/ .

# 构建前端应用
RUN npm run build

# 第二阶段：构建后端
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制后端依赖文件
COPY server/requirements.txt .

# 安装后端依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端源代码
COPY server/ .

# 从第一阶段复制前端构建产物到后端的static目录
COPY --from=frontend-builder /app/web/dist/ static/

# 创建必要的目录
RUN mkdir -p static

# 暴露端口
EXPOSE 8080

# 设置环境变量为生产环境
ENV APP_ENV=prod

# 启动命令
CMD ["python", "main.py", "--env", "prod"]