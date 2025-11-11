# Mail Notice

## 项目简介
定时收取电子邮件，并发送通知

## 运行方法

### 后端运行方法
1. 进入server目录:
```bash
cd server
```

2. （推荐）创建并激活虚拟环境:
   - Windows:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. 安装依赖:
```bash
pip install -r requirements.txt
```

5. 启动后端服务器:
```bash
python main.py
```

### 前端运行方法
1. 进入web目录:
```bash
cd web
```

2. 安装依赖:
```bash
npm install
```

3. 启动前端:
```bash
npm run dev
```

4. 访问应用
后端启动后，通过浏览器访问 `http://localhost:8080`
默认密码存储在.password文件中，第一次创建会生成密码并输出在日志中
