import streamlit as st
import sqlite3
import os
from datetime import datetime
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="Groove Media Hub",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Database & Directory Setup ---
DB_FILE = "groove_media.db"
UPLOAD_DIR = "static/uploads"
PROFILE_DIR = "static/profiles"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    chapter TEXT,
                    role TEXT,
                    school TEXT,
                    gka_name TEXT,
                    bio TEXT,
                    profile_pic TEXT,
                    status TEXT DEFAULT 'Active',
                    is_admin INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    event_id INTEGER,
                    uploaded_by TEXT NOT NULL,
                    timestamp TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    posted_by TEXT NOT NULL,
                    timestamp TEXT NOT NULL)''')
    
    c.execute("SELECT * FROM members WHERE username='Admin'")
    if not c.fetchone():
        c.execute('''INSERT INTO members 
                     (username, password, name, chapter, role, school, gka_name, bio, profile_pic, is_admin) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  ('Admin', 'Admin1962', 'System Administrator', 'National', 'President / Admin', '', '', 'App Administrator', '', 1))
    
    conn.commit()
    conn.close()

init_db()

def run_query(query, params=(), fetch=True):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        result = c.fetchall()
        conn.close()
        return result
    conn.commit()
    conn.close()

# --- Session State Management ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'name' not in st.session_state:
    st.session_state['name'] = ''
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = 0

# ==========================================
# 🔐 AUTHENTICATION (LOGIN / REGISTER)
# ==========================================
if not st.session_state['logged_in']:
    st.title("🎬 Groove Media Hub - Portal")
    
    tab1, tab2 = st.tabs(["Login", "Register New Member"])
    
    with tab1:
        st.subheader("Member Login")
        login_user = st.text_input("Username", key="log_user")
        login_pass = st.text_input("Password", type="password", key="log_pass")
        if st.button("Log In"):
            user_data = run_query("SELECT name, is_admin, status FROM members WHERE username=? AND password=?", (login_user, login_pass))
            if user_data:
                if user_data[0][2] == 'Suspended':
                    st.error("This account has been suspended by an administrator.")
                else:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = login_user
                    st.session_state['name'] = user_data[0][0]
                    st.session_state['is_admin'] = user_data[0][1]
                    st.rerun()
            else:
                st.error("Invalid Username or Password.")
                
    with tab2:
        st.subheader("Register Profile")
        with st.form("register_form"):
            reg_user = st.text_input("Choose a Username*")
            reg_pass = st.text_input("Choose a Password*", type="password")
            reg_name = st.text_input("Full Name*")
            reg_chapter = st.text_input("Chapter Affiliation")
            reg_role = st.selectbox("Media Role", ["Photographer", "Videographer", "Graphic Designer", "Editor", "Director"])
            reg_school = st.text_input("School Attended")
            reg_gka = st.text_input("GKA Name")
            reg_bio = st.text_area("Short Bio")
            
            # --- NEW: Profile Picture Uploader ---
            reg_pic = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])
            
            submit_reg = st.form_submit_button("Register Account")
            if submit_reg:
                if reg_user and reg_pass and reg_name:
                    pic_path = ""
                    # Save the uploaded picture if provided
                    if reg_pic:
                        pic_filename = f"{reg_user}_{reg_pic.name}"
                        pic_path = os.path.join(PROFILE_DIR, pic_filename)
                        with open(pic_path, "wb") as f:
                            f.write(reg_pic.getbuffer())

                    try:
                        run_query('''INSERT INTO members (username, password, name, chapter, role, school, gka_name, bio, profile_pic) 
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                  (reg_user, reg_pass, reg_name, reg_chapter, reg_role, reg_school, reg_gka, reg_bio, pic_path), fetch=False)
                        st.success("Account created! Please log in.")
                    except sqlite3.IntegrityError:
                        st.error("Username already exists. Choose another.")
                else:
                    st.error("Please fill in all required fields (*).")

else:
    # ==========================================
    # 🧭 MAIN APPLICATION (LOGGED IN)
    # ==========================================
    st.sidebar.title(f"Welcome, {st.session_state['name']}")
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.session_state['is_admin'] = 0
        st.rerun()
        
    st.sidebar.markdown("---")
    
    nav_options = ["📊 Dashboard", "📁 Media Repository", "📅 Annual Calendar", "👥 Team Roster", "📢 Announcements"]
    if st.session_state['is_admin'] == 1:
        nav_options.append("⚙️ Admin Controls")
        
    menu = st.sidebar.radio("Navigation", nav_options)
    st.sidebar.markdown("---")
    st.sidebar.info("Groove Phi Groove Social Fellowship Inc. — Media Team")

    # ==========================================
    # 📊 DASHBOARD
    # ==========================================
    if menu == "📊 Dashboard":
        st.title("Command Center Dashboard")
        
        col1, col2, col3 = st.columns(3)
        members_count = len(run_query("SELECT id FROM members WHERE is_admin=0"))
        events_count = len(run_query("SELECT id FROM events"))
        media_count = len(run_query("SELECT id FROM media"))
        
        col1.metric("Active Team Members", members_count)
        col2.metric("Scheduled Events", events_count)
        col3.metric("Stored Media Assets", media_count)
        
        st.markdown("---")
        st.subheader("📢 Recent Announcements")
        announcements = run_query("SELECT title, content, posted_by, timestamp FROM announcements ORDER BY id DESC LIMIT 3")
        if announcements:
            for title, content, posted_by, timestamp in announcements:
                with st.expander(f"📌 {title} (By: {posted_by} on {timestamp})"):
                    st.write(content)
        else:
            st.write("No recent announcements.")

    # ==========================================
    # 📁 MEDIA REPOSITORY
    # ==========================================
    elif menu == "📁 Media Repository":
        st.title("Media Asset Repository")
        
        with st.expander("📤 Upload New Media Asset"):
            events = run_query("SELECT id, title FROM events")
            event_options = {e[1]: e[0] for e in events}
            event_options["None (General Asset)"] = None
            
            selected_event_title = st.selectbox("Link to Event (Optional)", list(event_options.keys()))
            uploaded_file = st.file_uploader("Choose an image or video", type=["png", "jpg", "jpeg", "mp4", "mov"])
            
            if st.button("Upload to Repository"):
                if uploaded_file:
                    filename = uploaded_file.name
                    file_path = os.path.join(UPLOAD_DIR, filename)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    event_id = event_options[selected_event_title]
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    run_query("INSERT INTO media (filename, file_path, event_id, uploaded_by, timestamp) VALUES (?, ?, ?, ?, ?)",
                              (filename, file_path, event_id, st.session_state['name'], timestamp), fetch=False)
                    st.success(f"Uploaded {filename} successfully!")
                    st.rerun()

        st.markdown("---")
        st.subheader("📂 Asset Gallery")
        media_items = run_query("SELECT id, filename, file_path, uploaded_by, timestamp FROM media ORDER BY id DESC")
        
        if media_items:
            cols = st.columns(3)
            for idx, (m_id, filename, file_path, uploader, ts) in enumerate(media_items):
                with cols[idx % 3]:
                    st.image(file_path, caption=f"{filename}\nBy: {uploader}", use_container_width=True)
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as file:
                            st.download_button("Download", data=file, file_name=filename, key=f"dl_{m_id}")
        else:
            st.write("No media files found.")

    # ==========================================
    # 📅 ANNUAL CALENDAR
    # ==========================================
    elif menu == "📅 Annual Calendar":
        st.title("Annual Event Calendar")
        
        with st.expander("➕ Add New Event"):
            with st.form("event_form"):
                e_title = st.text_input("Event Title")
                e_date = st.date_input("Event Date")
                e_category = st.selectbox("Category", ["Tailgate & Homecoming", "Chapter Meeting", "Community Outreach", "Fundraiser", "National Event"])
                e_status = st.selectbox("Status", ["Planning", "Media Needed", "Assets In Progress", "Approved / Ready"])
                if st.form_submit_button("Save Event") and e_title:
                    run_query("INSERT INTO events (title, date, category, status) VALUES (?, ?, ?, ?)",
                              (e_title, str(e_date), e_category, e_status), fetch=False)
                    st.success("Event added!")
                    st.rerun()
                    
        st.markdown("---")
        events = run_query("SELECT title, date, category, status FROM events ORDER BY date ASC")
        if events:
            st.dataframe(pd.DataFrame(events, columns=["Title", "Date", "Category", "Status"]), use_container_width=True)

    # ==========================================
    # 👥 TEAM ROSTER (EXPANDED PROFILES)
    # ==========================================
    elif menu == "👥 Team Roster":
        st.title("Media Team Directory")
        
        # --- NEW: Fetches and displays profile_pic ---
        members = run_query("SELECT username, name, chapter, role, school, gka_name, bio, status, profile_pic FROM members WHERE is_admin=0")
        if members:
            for username, name, chapter, role, school, gka_name, bio, status, profile_pic in members:
                with st.container():
                    st.markdown(f"### {name} ({role})")
                    col_pic, col_info1, col_info2 = st.columns([1, 2, 2])
                    
                    with col_pic:
                        # Check if a picture exists and display it, else show a placeholder
                        if profile_pic and os.path.exists(profile_pic):
                            st.image(profile_pic, use_container_width=True)
                        else:
                            st.info("No Photo Uploaded")
                            
                    with col_info1:
                        st.markdown(f"**GKA Name:** {gka_name if gka_name else 'N/A'}")
                        st.markdown(f"**Status:** {status}")
                    with col_info2:
                        st.markdown(f"**Chapter:** {chapter} | **School:** {school}")
                        st.markdown(f"**Bio:** {bio}")
                    st.markdown("---")
        else:
            st.write("No members registered yet.")

    # ==========================================
    # 📢 ANNOUNCEMENTS
    # ==========================================
    elif menu == "📢 Announcements":
        st.title("Announcements & Reminders")
        
        with st.expander("📢 Post New Announcement"):
            with st.form("announcement_form"):
                a_title = st.text_input("Announcement Title")
                a_content = st.text_area("Content / Details")
                if st.form_submit_button("Publish Announcement") and a_title:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                    run_query("INSERT INTO announcements (title, content, posted_by, timestamp) VALUES (?, ?, ?, ?)",
                              (a_title, a_content, st.session_state['name'], ts), fetch=False)
                    st.success("Announcement published!")
                    st.rerun()
                    
        st.markdown("---")
        announcements = run_query("SELECT title, content, posted_by, timestamp FROM announcements ORDER BY id DESC")
        for title, content, posted_by, timestamp in announcements:
            st.markdown(f"#### {title}")
            st.caption(f"Posted by **{posted_by}** on {timestamp}")
            st.write(content)
            st.markdown("---")

    # ==========================================
    # ⚙️ ADMIN CONTROLS
    # ==========================================
    elif menu == "⚙️ Admin Controls":
        st.title("System Administration")
        st.warning("You are in the Admin Panel. Actions taken here are permanent.")
        
        tab1, tab2 = st.tabs(["Manage Members", "Manage Media"])
        
        with tab1:
            st.subheader("Member Access Control")
            members = run_query("SELECT id, username, name, status, profile_pic FROM members WHERE is_admin=0")
            if members:
                for m_id, user, name, status, pic in members:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"**{name}** (@{user}) - Status: {status}")
                    
                    if status == 'Active':
                        if col2.button("Suspend", key=f"susp_{m_id}"):
                            run_query("UPDATE members SET status='Suspended' WHERE id=?", (m_id,), fetch=False)
                            st.rerun()
                    else:
                        if col2.button("Reactivate", key=f"react_{m_id}"):
                            run_query("UPDATE members SET status='Active' WHERE id=?", (m_id,), fetch=False)
                            st.rerun()
                            
                    if col3.button("Delete", key=f"del_user_{m_id}", type="primary"):
                        run_query("DELETE FROM members WHERE id=?", (m_id,), fetch=False)
                        # Clean up profile picture file if it exists
                        if pic and os.path.exists(pic):
                            try:
                                os.remove(pic)
                            except:
                                pass
                        st.rerun()
            else:
                st.write("No standard members found.")
                
        with tab2:
            st.subheader("Delete Media Assets")
            media_files = run_query("SELECT id, filename, uploaded_by, file_path FROM media")
            if media_files:
                for m_id, filename, uploader, file_path in media_files:
                    col1, col2 = st.columns([4, 1])
                    col1.write(f"{filename} (Uploaded by: {uploader})")
                    if col2.button("Delete File", key=f"del_media_{m_id}", type="primary"):
                        run_query("DELETE FROM media WHERE id=?", (m_id,), fetch=False)
                        if file_path and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except:
                                pass
                        st.rerun()
            else:
                st.write("No media files to manage.")