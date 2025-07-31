from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from db import get_db_connection
import psycopg2
import os

app = Flask(__name__)
CORS(app)

# === Register Route ===
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    codename = data.get("codename")
    nickname = data.get("nickname")
    fullname = data.get("fullname")
    password = data.get("password")
    gmail = data.get("gmail")
    phone = data.get("phone")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (codename, nickname, fullname, password, gmail, phone)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (codename, nickname, fullname, password, gmail, phone))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Registration successful"})
    except Exception as e:
        return jsonify({"message": "Registration failed", "error": str(e)}), 500

# === Login Route ===
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    codename = data.get("codename")
    password = data.get("password")

    # Check for admin account first (hardcoded)
    if codename == "fouie" and password == "fouie4477":
        return jsonify({
            "success": True, 
            "message": "Admin login successful", 
            "codename": codename,
            "userType": "admin"
        })

    # Regular user login (database check)
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE codename = %s", (codename,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and result[0] == password:
            return jsonify({
                "success": True, 
                "message": "Login successful", 
                "codename": codename,
                "userType": "user"
            })
        else:
            return jsonify({"success": False, "message": "Invalid codename or password"})

    except Exception as e:
        return jsonify({"success": False, "message": "Login failed", "error": str(e)}), 500

# === Get Profile Info ===
@app.route("/profile/<codename>", methods=["GET"])
def get_profile(codename):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT codename, nickname, fullname, gmail, phone
            FROM users WHERE codename = %s
        """, (codename,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            return jsonify({
                "codename": result[0],
                "nickname": result[1],
                "fullname": result[2],
                "gmail": result[3],
                "phone": result[4]
            })
        else:
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Upload Profile Photo ===
@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    codename = request.form.get("codename")
    file = request.files.get("photo")

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    file_data = file.read()

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET profile_photo = %s WHERE codename = %s", (psycopg2.Binary(file_data), codename))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Photo uploaded successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Serve Profile Photo ===
@app.route("/profile_photo/<codename>", methods=["GET"])
def serve_profile_photo(codename):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT profile_photo FROM users WHERE codename = %s", (codename,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and result[0]:
            return Response(result[0], mimetype='image/jpeg')  # You can dynamically detect mimetype if needed
        else:
            return '', 204  # No Content

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/users")
def get_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT codename, nickname FROM users")
        users = [{"codename": row[0], "nickname": row[1]} for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Admin Routes ===
@app.route("/admin/change-password", methods=["POST"])
def admin_change_password():
    data = request.get_json()
    codename = data.get("codename")
    new_password = data.get("newPassword")
    
    if not codename or not new_password:
        return jsonify({"success": False, "message": "Missing codename or password"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password = %s WHERE codename = %s", (new_password, codename))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Password updated successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": "Database error", "error": str(e)}), 500

@app.route("/admin/delete-user", methods=["DELETE"])
def admin_delete_user():
    data = request.get_json()
    codename = data.get("codename")
    
    if not codename:
        return jsonify({"success": False, "message": "Missing codename"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE codename = %s", (codename,))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "User deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": "Database error", "error": str(e)}), 500

# === Announcement Routes ===
@app.route("/announcements", methods=["POST"])
def create_announcement():
    data = request.get_json()
    title = data.get("title")
    content = data.get("content")
    priority = data.get("priority", "normal")
    author = data.get("author", "Admin")
    
    if not title or not content:
        return jsonify({"success": False, "message": "Title and content are required"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                priority VARCHAR(20) DEFAULT 'normal',
                author VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            INSERT INTO announcements (title, content, priority, author)
            VALUES (%s, %s, %s, %s)
        """, (title, content, priority, author))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Announcement created successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": "Database error", "error": str(e)}), 500

@app.route("/announcements", methods=["GET"])
def get_announcements():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                priority VARCHAR(20) DEFAULT 'normal',
                author VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            SELECT id, title, content, priority, author, created_at
            FROM announcements
            ORDER BY created_at DESC
        """)
        
        announcements = []
        for row in cur.fetchall():
            announcements.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "priority": row[3],
                "author": row[4],
                "created_at": row[5].isoformat() if row[5] else None
            })
        
        cur.close()
        conn.close()
        return jsonify(announcements)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Delete Announcement ===
@app.route("/announcements/<int:announcement_id>", methods=["DELETE"])
def delete_announcement(announcement_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if announcement exists
        cur.execute("SELECT id FROM announcements WHERE id = %s", (announcement_id,))
        if not cur.fetchone():
            return jsonify({"success": False, "message": "Announcement not found"}), 404
        
        # Delete the announcement
        cur.execute("DELETE FROM announcements WHERE id = %s", (announcement_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Announcement deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": "Database error", "error": str(e)}), 500

# === Get Single Announcement ===
@app.route("/announcements/<int:announcement_id>", methods=["GET"])
def get_announcement(announcement_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, title, content, priority, author, created_at
            FROM announcements WHERE id = %s
        """, (announcement_id,))
        
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Announcement not found"}), 404
        
        announcement = {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "priority": row[3],
            "author": row[4],
            "created_at": row[5].isoformat() if row[5] else None
        }
        
        cur.close()
        conn.close()
        return jsonify(announcement)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Update Announcement ===
@app.route("/announcements/<int:announcement_id>", methods=["PUT"])
def update_announcement(announcement_id):
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        priority = data.get('priority', 'normal')
        
        if not title or not content:
            return jsonify({"success": False, "message": "Title and content are required"}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if announcement exists
        cur.execute("SELECT id FROM announcements WHERE id = %s", (announcement_id,))
        if not cur.fetchone():
            return jsonify({"success": False, "message": "Announcement not found"}), 404
        
        # Update the announcement
        cur.execute("""
            UPDATE announcements 
            SET title = %s, content = %s, priority = %s
            WHERE id = %s
        """, (title, content, priority, announcement_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Announcement updated successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": "Database error", "error": str(e)}), 500

@app.route("/update_profile", methods=["POST"])
def update_profile():
    try:
        data = request.get_json()
        codename = data.get('codename')
        nickname = data.get('nickname')
        phone = data.get('phone')
        gmail = data.get('gmail')
        password = data.get('password')
        
        if not codename:
            return jsonify({"success": False, "message": "Codename is required"}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build update query dynamically based on provided fields
        update_fields = []
        values = []
        
        if nickname is not None:
            update_fields.append("nickname = %s")
            values.append(nickname)
            
        if phone is not None:
            update_fields.append("phone = %s")
            values.append(phone)
            
        if gmail is not None:
            update_fields.append("gmail = %s")
            values.append(gmail)
            
        if password:
            update_fields.append("password = %s")
            values.append(password)
        
        if not update_fields:
            return jsonify({"success": False, "message": "No fields to update"}), 400
        
        values.append(codename)  # for WHERE clause
        
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE codename = %s"
        cur.execute(query, values)
        
        if cur.rowcount == 0:
            return jsonify({"success": False, "message": "User not found"}), 404
            
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Profile updated successfully"})
        
    except Exception as e:
        return jsonify({"success": False, "message": "Database error", "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
