# Mail Notice

## Project introduction
Automatically fetch emails at scheduled times and send notifications.

## Running Instructions

### Docker Usage

#### Pull and Run from GitHub Registry

docker run -d --name mailnotice -p 8080:8080 -v $PWD/data:/app/data ghcr.io/lonzoen/mailnotice:latest

### Backend Instructions
1. Navigate to the server directory:
```bash
cd server
```

2. (Recommended) Create and activate a virtual environment:
- Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the backend server:
```bash
python main.py
```

### Frontend Instructions
1. Navigate to the web directory:
```bash
cd web
```

2. Install dependencies:
```bash
npm install
```

3. Start the frontend development server:
```bash
npm run dev
```

4. Access the application
After starting the backend, open a web browser and visit `http://localhost:8080`
The default password is stored in the .password file. The first time it is created, a password will be generated and output in the logs.

## License
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)