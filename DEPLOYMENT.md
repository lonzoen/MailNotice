# 自动化构建与部署指南

本文档说明如何使用GitHub Actions自动构建前端、移动静态文件到后端并打包成Docker镜像。

## 准备工作

### 1. GitHub仓库配置

确保你的项目已上传到GitHub仓库，并完成以下配置：

1. 在GitHub仓库中设置Docker Hub凭证：
   - 进入仓库 → Settings → Secrets and variables → Actions
   - 添加以下密钥：
     - `DOCKER_HUB_USERNAME`：你的Docker Hub用户名
     - `DOCKER_HUB_ACCESS_TOKEN`：你的Docker Hub访问令牌（在Docker Hub设置中生成）

2. 可选：如果需要自动部署到服务器，添加SSH凭证：
   - `SSH_PRIVATE_KEY`：用于连接服务器的私钥
   - `SERVER_HOST`：服务器地址
   - `SERVER_USER`：服务器用户名

### 2. 文件说明

本项目已包含以下配置文件：

- **Dockerfile**：定义Docker镜像的构建过程，包括前端构建和后端部署
- **docker-compose.yml**：用于本地或服务器上运行Docker容器
- **.github/workflows/build-and-deploy.yml**：GitHub Actions工作流配置

## GitHub Actions工作流程

GitHub Actions工作流会在以下情况下触发：
- 推送到`main`或`master`分支
- 向`main`或`master`分支提交Pull Request

工作流程执行以下步骤：

1. **检出代码**：获取最新的代码
2. **设置Docker Buildx**：准备Docker构建环境
3. **登录Docker Hub**：使用配置的凭证登录
4. **提取元数据**：生成Docker镜像标签等信息
5. **构建并推送镜像**：
   - Pull Request时仅构建镜像
   - 推送到主分支时构建并推送镜像
6. **运行测试**：可选步骤，可添加测试命令
7. **部署到服务器**：可选步骤，可配置自动部署

## 本地测试Docker构建

在将代码推送到GitHub之前，建议在本地测试Docker构建：

```bash
# 构建Docker镜像
docker build -t mailnotice .

# 运行Docker容器
docker run -p 8080:8080 mailnotice

# 或者使用docker-compose
docker-compose up --build
```

## 部署流程说明

### 前端构建与静态文件处理

1. GitHub Actions工作流使用Node.js环境构建前端
2. 构建完成后，前端静态文件会被复制到后端的`static`目录
3. Docker镜像中包含了整个应用，包括后端API和前端静态文件

### 容器运行时

- 容器暴露8080端口
- 使用SQLite数据库，数据文件通过卷挂载持久化
- 密码文件同样通过卷挂载持久化

## 注意事项

1. 确保修改了前端API配置，使用相对路径：
   - 已将`API_BASE_URL`从`http://localhost:8080/api`改为`/api`

2. 在生产环境中，建议：
   - 使用更强的安全措施保护密码文件
   - 配置适当的日志轮转
   - 考虑使用更强大的数据库替代SQLite（如需要）

3. 如需自定义Docker镜像名称，请修改：
   - `.github/workflows/build-and-deploy.yml`中的`images: your-dockerhub-username/mailnotice`
   - 替换为你的Docker Hub用户名和镜像名称

## 故障排除

1. **构建失败**：检查GitHub Actions日志，查看具体错误信息
2. **镜像推送失败**：确认Docker Hub凭证正确配置
3. **运行时错误**：检查容器日志，使用`docker logs [container_id]`
4. **API连接问题**：确保前端使用的是相对路径，而不是硬编码的localhost地址