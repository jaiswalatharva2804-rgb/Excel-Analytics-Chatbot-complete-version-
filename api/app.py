from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import os
import pandas as pd
import time

from chatbot_api import ChatbotAPI   # make sure this path is correct


# --------------------------------
# APP SETUP
# --------------------------------

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Single chatbot instance
chatbot = ChatbotAPI()


# --------------------------------
# CSV CLEANING FUNCTION
# --------------------------------

def clean_csv(file_path: str) -> str:
    """
    Advanced CSV cleaner:
    - Handles broken quotes/newlines
    - Preserves text columns
    - Normalizes headers
    - Rebuilds safe CSV
    """

    print("Reading CSV in tolerant mode...")

    # STEP 1: Tolerant read
    df = pd.read_csv(
        file_path,
        engine="python",
        sep=",",
        quotechar='"',
        escapechar="\\",
        encoding="utf-8",
        on_bad_lines="warn"
    )

    print("Loaded rows:", len(df))

    # STEP 2: Drop empty columns
    df = df.dropna(axis=1, how="all")

    # STEP 3: Drop mostly empty columns (95%)
    threshold = len(df) * 0.05
    df = df.dropna(axis=1, thresh=threshold)

    # STEP 4: Normalize headers
    new_columns = []

    for i, col in enumerate(df.columns):

        col = str(col).strip()

        if not col or col.lower().startswith("unnamed"):
            name = f"column_{i+1}"
        else:
            name = (
                col.lower()
                .replace(" ", "_")
                .replace("-", "_")
                .replace(".", "")
            )

        new_columns.append(name)

    df.columns = new_columns

    # STEP 5: Clean text columns
    for col in df.columns:
        if df[col].dtype == "object":

            df[col] = (
                df[col]
                .astype(str)
                .str.replace("\n", " ", regex=False)
                .str.replace("\r", " ", regex=False)
                .str.replace("\t", " ", regex=False)
                .str.strip()
            )

    # STEP 6: Export safe CSV
    clean_path = file_path.replace(".csv", "_cleaned.csv")

    df.to_csv(
        clean_path,
        index=False,
        encoding="utf-8",
        quoting=1,      # Quote all text
        escapechar="\\"
    )

    print("Saved:", clean_path)

    return clean_path


# --------------------------------
# ROUTES
# --------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------
# FILE UPLOAD
# --------------------------------

@app.route("/upload", methods=["POST"])
def upload_file():

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"})

    filename = file.filename.lower()
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)

    file.save(filepath)

    try:

        if filename.endswith(".csv"):

            cleaned_path = clean_csv(filepath)
            result = chatbot.load_file(cleaned_path)

        else:

            result = chatbot.load_file(filepath)

        return jsonify(result.to_dict())

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


# --------------------------------
# NORMAL ASK (FULL RESPONSE)
# --------------------------------

@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"success": False, "error": "Empty question"})

    # Determine if the question is asking to show or preview data
    show_keywords = ["show", "preview", "display", "list", "view", "top", "first", "last"]
    is_show_query = any(keyword in question.lower() for keyword in show_keywords)
    
    if is_show_query:
        # For show/preview queries, allow table formatting but keep it clean
        formatted = (
            question
            + "\n\nProvide your answer in a conversational style. "
            + "If showing data, format it as a clean table. "
            + "Do not use markdown symbols like asterisks, hashtags, or bullet points."
        )
    else:
        # For other queries, use plain text conversational style
        formatted = (
            question
            + "\n\nProvide your answer in plain text without markdown formatting, "
            + "bullet points, asterisks, or hashtags. Use a conversational style."
        )

    try:

        result = chatbot.ask(formatted)

        return jsonify(result.to_dict())

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


# --------------------------------
# STREAMING ASK (CHATGPT STYLE)
# --------------------------------

@app.route("/ask_stream", methods=["POST"])
def ask_stream():

    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"success": False, "error": "Empty question"})

    formatted = (
        question
        + "\n\nFormat your answer in Markdown using headings, bullet points, and tables."
    )

    def generate():

        try:

            # Get full response first
            result = chatbot.ask(formatted)

            # Adjust if your API differs
            text = result.text if hasattr(result, "text") else result.to_dict().get("answer", "")

            words = text.split(" ")

            for word in words:
                yield f"data: {word}\n\n"
                time.sleep(0.05)  # typing speed

            yield "data: [DONE]\n\n"

        except Exception as e:

            yield f"data: ERROR: {str(e)}\n\n"


    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable buffering (NGINX)
        }
    )


# --------------------------------
# SCHEMA
# --------------------------------

@app.route("/schema")
def schema():

    try:

        result = chatbot.get_schema()
        return jsonify(result.to_dict())

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


# --------------------------------
# RUN SERVER
# --------------------------------

if __name__ == "__main__":

    # Disable reloader (fix DB lock issues)
    app.run(
        debug=True,
        use_reloader=False,
        threaded=True
    )
