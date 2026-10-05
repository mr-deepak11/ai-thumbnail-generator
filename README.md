# 🎨 AI Thumbnail Generator

Generate professional YouTube thumbnails using AI.

An AI-powered thumbnail generation platform built with **React**, **FastAPI**, **Pollinations AI**, and **ImageKit**. Users can enter a video idea, choose a thumbnail style, and generate visually appealing thumbnails instantly.

---

## ✨ Features

- 🎯 AI-powered thumbnail generation
- 🎨 Multiple thumbnail styles
- ⚡ FastAPI backend
- 🖥️ Modern React frontend
- ☁️ ImageKit image hosting
- 📱 Responsive user interface
- 🚀 Fast generation workflow
- 🔄 Async thumbnail processing

---

## 📸 Preview

### Homepage
_Add your screenshot here_

### Generated Thumbnails
_Add your screenshot here_

---

## 🛠️ Tech Stack

### Frontend
- React
- Vite
- JavaScript
- CSS

### Backend
- FastAPI
- SQLModel
- Python
- SQLite

### AI & Storage
- Pollinations AI
- ImageKit

---

## 🏗️ Architecture

```text
User
 │
 ▼
React Frontend
 │
 ▼
FastAPI Backend
 │
 ├── Pollinations AI
 │      │
 │      ▼
 │   Generated Image
 │
 └── ImageKit
        │
        ▼
     Image URL
```

---

## 📂 Project Structure

```text
ai-thumbnail-generator/
│
├── backend/
│   ├── services/
│   │   ├── pollinations_service.py
│   │   ├── imagekit_service.py
│   │   └── generator.py
│   │
│   ├── main.py
│   ├── routes.py
│   ├── models.py
│   ├── database.py
│   └── config.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── .gitignore
└── README.md
```

---

## 🚀 Installation

### Clone Repository

```bash
git clone https://github.com/mr-deepak11/ai-thumbnail-generator.git
cd ai-thumbnail-generator
```

### Backend Setup

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file inside the backend folder:

```env
IMAGEKIT_PRIVATE_KEY=your_private_key
IMAGEKIT_PUBLIC_KEY=your_public_key
IMAGEKIT_URL_ENDPOINT=your_endpoint
```

### Run Backend

```bash
uvicorn main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

---

### Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

---

## 🔥 Workflow

1. User enters video topic
2. User selects thumbnail style
3. FastAPI sends prompt to Pollinations AI
4. AI generates thumbnail image
5. Image uploaded to ImageKit
6. URL returned to frontend
7. User views generated thumbnails

---

## 🎯 Future Improvements

- User authentication
- Thumbnail editor
- Custom text overlay support
- More AI models
- Download in multiple formats
- Thumbnail history
- Cloud deployment

---

## 👨‍💻 Author

**Deepak Kumar**

Computer Science Engineering Student

GitHub: https://github.com/mr-deepak11

---

## ⭐ Support

If you found this project useful, consider giving it a star on GitHub.

---

## 📄 License

This project is available for educational and portfolio purposes.
