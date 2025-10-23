# AI-Powered Mock Interview Platform

This project is an AI-powered application designed to help users practice for interviews without needing a human partner. The system uses specialized AI agents to conduct interviews, review code, and provide detailed, actionable feedback.

## 💡 About The Project

Finding someone to conduct a mock interview is difficult. This application solves that problem by providing a realistic interview experience on-demand. It's built for anyone interested in mock interviews, especially for tech roles.

The system uses AI agents tailored to specific job descriptions, can review code submissions, and even includes an AI proctor to monitor the session for a more realistic test environment.

## ✨ Features

Here are the key features planned for the application:

* **🤖 AI Interview Agents:** Get interviewed by an AI that asks relevant questions based on your field.
* **📄 Job-Specific Interviews:** Upload a job description, and the AI will tailor the interview questions to that specific role.
* **💻 Code Review (for IT roles):** Submit code during the interview and get instant feedback on quality, efficiency, and correctness.
* **👁️ AI Proctoring:** An AI agent monitors the interview via your webcam to simulate a real, proctored exam environment.
* **❤️ 5-Lifeline System:** To keep the interview realistic, the proctoring agent allows for 5 "lifelines" (e.g., looking away, background noise). If you exceed 5, the interview is flagged as cheating, and the session ends with feedback to prepare more.
* **📊 Detailed Feedback Metrics:** After a successful interview, you'll receive a comprehensive report highlighting your strengths and, more importantly, areas where you need to improve.

## 🛠️ Tech Stack

* **Backend:** Python, Flask, Flask-SocketIO
* **Real-time & Video:** OpenCV, NumPy, Socket.IO, base64
* **Frontend:** HTML, CSS, JavaScript
* **AI (Planned):** Large Language Models (LLMs) for Q&A, code analysis, and computer vision models for proctoring.

## 🚀 Current Progress

So far, the foundational backend for the **AI Proctoring** feature is in place:

1.  **Flask Server:** A basic Flask web server is up and running.
2.  **Real-time Video Streaming:** The application can successfully capture video frames from a user's webcam in the browser (`video_capture.html`).
3.  **Server-Side Processing:** These video frames are sent from the client to the server in real-time using `Flask-SocketIO`.
4.  **Frame Decoding:** The server receives the `base64`-encoded frames, decodes them, and converts them into **OpenCV** image format (`numpy` array).

This setup is the first crucial step for analyzing the user's video feed for the proctoring feature.

## 🔧 Getting Started (Setup & Installation)

To run the project in its current state:

1.  **Clone the repository:**
    ```bash
    git clone [https://your-repository-url.git](https://your-repository-url.git)
    cd your-project-directory
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # On Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install the required packages:**
    (You may want to create a `requirements.txt` file with these)
    ```bash
    pip install flask flask-socketio opencv-python numpy eventlet
    ```
    *Note: `eventlet` is a recommended production-ready server for Flask-SocketIO.*

4.  **Create your frontend:**
    Create a `templates` folder in your project directory and add the `video_capture.html` file inside it.

5.  **Run the application:**
    (Assuming your Python file is named `app.py`)
    ```bash
    python app.py
    ```

6.  **Open your browser:**
    Navigate to `http://127.0.0.1:5000` to see the video capture in action.

## 🗺️ Roadmap (Future Work)

* [ ] **Proctoring Logic:** Implement the computer vision logic to analyze the OpenCV frames for "cheating" (e.g., eye tracking, multiple faces, phone detection).
* [ ] **Lifeline System:** Build the backend logic to track the 5 lifelines and end the session.
* [ ] **Core AI Agent:** Integrate an LLM (like Gemini, GPT, or an open-source model) to handle the interview Q&A flow.
* [ ] **JD-Specific Agent:** Add a feature to upload a Job Description and use it to generate a specialized system prompt for the AI agent.
* [ ] **Code Review Agent:** Build the UI and backend route to accept code submissions and pipe them to another specialized AI agent for analysis.
* [ ] **Feedback Generation:** Create the logic to score the user's answers and proctoring performance and display the final metrics report.
* [ ] **UI/UX:** Design and build out the full frontend interface for a clean user experience.

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.