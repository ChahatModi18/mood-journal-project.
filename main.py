from textblob import TextBlob
import mysql.connector
from datetime import datetime
import re

# ------------------ DATABASE SETUP ------------------

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="chahat"  # 🔁 Replace with your MySQL password
)
cursor = conn.cursor()

# Create DB and table
cursor.execute("CREATE DATABASE IF NOT EXISTS moodjournal_db")
cursor.execute("USE moodjournal_db")

# Drop old table and create fresh with required columns
cursor.execute("DROP TABLE IF EXISTS user_inputs")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_inputs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        input_text TEXT,
        mood VARCHAR(50),
        sentiment_polarity FLOAT,
        sentiment_subjectivity FLOAT,
        timestamp DATETIME
    )
""")

# ------------------ MOOD CATEGORIZATION ------------------

def categorize_mood(text, polarity):
    text = text.lower()
    message = ""

    # Special moods based on keywords
    if any(word in text for word in ["anxious", "nervous", "panicky", "overthinking", "restless"]):
        message = "⚠️ You seem anxious. Please take deep breaths. Talking to a counselor may help."
        return "Anxious", message

    if any(word in text for word in ["crying", "teary", "emotional", "sensitive", "sentimental"]):
        message = "🧸 It's okay to feel emotional. You might feel better after sharing with someone you trust."
        return "Emotional", message

    if any(word in text for word in ["help", "can't handle", "tired of life", "give up", "support", "alone", "worthless", "no one cares"]):
        message = "💬 You might be going through a lot. Please reach out to a counselor or someone you trust. You're not alone."
        return "Need Help", message

    sarcasm_patterns = [r"\bsure\b", r"\byeah right\b", r"\bwhatever\b", r"\bgreat\b", r"\bnot really\b", r"\.\.\."]
    if any(re.search(p, text) for p in sarcasm_patterns):
        return "Sarcastic/Irritated", ""

    if "..." in text or "ugh" in text or "meh" in text:
        return "Uncertain/Tired", ""

    # Mood by polarity
    if polarity > 0.5:
        return "Very Happy", ""
    elif polarity > 0:
        if any(word in text for word in ["calm", "grateful", "peace"]):
            return "Peaceful", ""
        return "Happy", ""
    elif polarity < -0.5:
        return "Very Sad", ""
    elif polarity < 0:
        if any(word in text for word in ["angry", "irritated", "frustrated"]):
            return "Angry", ""
        return "Sad", ""
    else:
        return "Neutral", ""

# ------------------ USER INPUT & ANALYSIS ------------------

# Input from user
text = input("📝 Enter your thoughts or mood: ")
blob = TextBlob(text)
sentiment = blob.sentiment
polarity = sentiment.polarity
subjectivity = sentiment.subjectivity
timestamp = datetime.now()

mood, message = categorize_mood(text, polarity)

# Insert into DB
cursor.execute("""
    INSERT INTO user_inputs (input_text, mood, sentiment_polarity, sentiment_subjectivity, timestamp)
    VALUES (%s, %s, %s, %s, %s)
""", (text, mood, polarity, subjectivity, timestamp))

conn.commit()

# ------------------ OUTPUT CURRENT MOOD ------------------

print("\n🧠 Sentiment Analysis:")
print(f"Polarity: {polarity}")
print(f"Subjectivity: {subjectivity}")
print(f"Mood Detected: {mood}")
if message:
    print(f"\n📢 Note: {message}")

# ------------------ PAST ENTRIES ------------------

print("\n📚 Previous Entries Summary:\n")

cursor.execute("SELECT input_text, mood, timestamp FROM user_inputs ORDER BY timestamp DESC")
entries = cursor.fetchall()

if entries:
    for entry in entries:
        mood_text = f"[{entry[2].strftime('%Y-%m-%d %H:%M')}] - Mood: {entry[1]}"
        print(f"{mood_text}\nThought: {entry[0]}\n")
else:
    print("No previous entries found.")

# ------------------ FILTER BY MOOD ------------------

filter_choice = input("\n🔍 Do you want to filter past entries by a specific mood? (yes/no): ").strip().lower()

if filter_choice == "yes":
    selected_mood = input("Enter the mood to filter (e.g., Happy, Anxious, Sad, Emotional, etc.): ").strip().capitalize()
    cursor.execute("SELECT input_text, timestamp FROM user_inputs WHERE mood = %s ORDER BY timestamp DESC", (selected_mood,))
    filtered = cursor.fetchall()
    
    print(f"\n📋 Entries with mood '{selected_mood}':")
    if filtered:
        for f in filtered:
            print(f"[{f[1].strftime('%Y-%m-%d %H:%M')}]: {f[0]}")
    else:
        print("No entries found for this mood.")

# ------------------ CLOSE CONNECTION ------------------

conn.close()
