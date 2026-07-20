import streamlit as st
import requests

# ─── Configuration ───────────────────────────────────────────────

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="MentorMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Session State Initialization ────────────────────────────────

def init_session_state():
    defaults = {
        "authenticated": False,
        "token": None,
        "student_id": None,
        "student_name": None,
        "messages": [],
        "mastery_scores": {},
        "auth_page": "login",  # "login" or "register"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ─── API Helper ──────────────────────────────────────────────────

def api_request(method, endpoint, json_data=None, auth=True):
    """Make an API request with optional JWT authentication."""
    headers = {}
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=30)
        else:
            resp = requests.post(url, json=json_data, headers=headers, timeout=60)
        return resp
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.RequestException:
        return None


# ─── Authentication Pages ────────────────────────────────────────

def show_login_page():
    """Render the login form."""
    st.markdown(
        "<h1 style='text-align: center;'>🧠 MentorMind AI</h1>"
        "<p style='text-align: center; color: #888;'>"
        "Your personal AI tutor with long-term memory</p>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Login")

        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="you@example.com")
            password = st.text_input(
                "🔑 Password", type="password", placeholder="Your password"
            )
            submitted = st.form_submit_button(
                "Login", use_container_width=True, type="primary"
            )

            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    resp = api_request(
                        "POST",
                        "/students/login",
                        {"email": email, "password": password},
                        auth=False,
                    )
                    if resp is None:
                        st.error(
                            "❌ Cannot connect to the backend. "
                            "Make sure the API server is running."
                        )
                    elif resp.status_code == 200:
                        data = resp.json()
                        st.session_state.authenticated = True
                        st.session_state.token = data["access_token"]
                        st.session_state.student_id = data["student_id"]
                        st.session_state.student_name = data["name"]
                        st.session_state.messages = []
                        st.rerun()
                    else:
                        detail = resp.json().get("detail", "Login failed")
                        st.error(f"❌ {detail}")

        st.markdown("---")
        st.markdown(
            "<p style='text-align: center;'>Don't have an account?</p>",
            unsafe_allow_html=True,
        )
        if st.button(
            "Create Account", use_container_width=True, key="go_register"
        ):
            st.session_state.auth_page = "register"
            st.rerun()


def show_register_page():
    """Render the registration form."""
    st.markdown(
        "<h1 style='text-align: center;'>🧠 MentorMind AI</h1>"
        "<p style='text-align: center; color: #888;'>"
        "Create your account to start learning</p>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 📝 Register")

        with st.form("register_form"):
            name = st.text_input("👤 Full Name", placeholder="Your name")
            email = st.text_input("📧 Email", placeholder="you@example.com")
            password = st.text_input(
                "🔑 Password", type="password", placeholder="Choose a password"
            )
            confirm_password = st.text_input(
                "🔑 Confirm Password",
                type="password",
                placeholder="Repeat your password",
            )
            submitted = st.form_submit_button(
                "Create Account", use_container_width=True, type="primary"
            )

            if submitted:
                if not name or not email or not password:
                    st.error("Please fill in all fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    resp = api_request(
                        "POST",
                        "/students/register",
                        {
                            "name": name,
                            "email": email,
                            "password": password,
                        },
                        auth=False,
                    )
                    if resp is None:
                        st.error(
                            "❌ Cannot connect to the backend. "
                            "Make sure the API server is running."
                        )
                    elif resp.status_code == 200:
                        data = resp.json()
                        st.session_state.authenticated = True
                        st.session_state.token = data["access_token"]
                        st.session_state.student_id = data["student_id"]
                        st.session_state.student_name = data["name"]
                        st.session_state.messages = []
                        st.success("✅ Account created! Redirecting...")
                        st.rerun()
                    else:
                        detail = resp.json().get(
                            "detail", "Registration failed"
                        )
                        st.error(f"❌ {detail}")

        st.markdown("---")
        st.markdown(
            "<p style='text-align: center;'>Already have an account?</p>",
            unsafe_allow_html=True,
        )
        if st.button(
            "Back to Login", use_container_width=True, key="go_login"
        ):
            st.session_state.auth_page = "login"
            st.rerun()


# ─── Sidebar: Profile & Mastery Dashboard ────────────────────────

def show_sidebar():
    """Render the sidebar with student info and mastery dashboard."""
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.student_name}")
        st.caption(f"ID: {st.session_state.student_id[:8]}...")

        st.markdown("---")

        # Fetch and display mastery scores
        st.markdown("### 📊 Mastery Dashboard")

        mastery = st.session_state.get("mastery_scores", {})
        if mastery:
            for topic, score in sorted(
                mastery.items(), key=lambda x: x[1], reverse=True
            ):
                # Color-code the progress bar
                if score >= 0.7:
                    label = f"🟢 {topic}"
                elif score >= 0.4:
                    label = f"🟡 {topic}"
                else:
                    label = f"🔴 {topic}"
                st.progress(score, text=f"{label}: {score:.0%}")
        else:
            st.info(
                "No mastery data yet.\nStart chatting to build your profile!"
            )

        st.markdown("---")

        # Refresh mastery scores
        if st.button("🔄 Refresh Mastery", use_container_width=True):
            resp = api_request("GET", "/students/me/mastery")
            if resp and resp.status_code == 200:
                data = resp.json()
                mastery_raw = data.get("mastery_scores", {})
                st.session_state.mastery_scores = {
                    t: info["score"] for t, info in mastery_raw.items()
                }
                st.rerun()

        st.markdown("---")

        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ─── Main Chat Interface ─────────────────────────────────────────

def show_chat():
    """Render the main chat interface."""
    st.title("🧠 MentorMind AI Tutor")
    st.markdown(
        f"Welcome back, **{st.session_state.student_name}**! "
        f"I remember our past conversations and adapt to your learning style."
    )

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "topic" in message:
                st.caption(f"📚 Topic: {message['topic']}")

    # Chat input
    if prompt := st.chat_input(
        "Ask a question (e.g. What is Newton's Second Law?)"
    ):
        # Display user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        # Generate response
        with st.spinner("🧠 MentorMind is thinking & recalling memories..."):
            resp = api_request(
                "POST", "/chat", {"question": prompt}
            )

            if resp is None:
                answer = (
                    "❌ Cannot connect to the backend. "
                    "Make sure the API server is running."
                )
                topic = "error"
            elif resp.status_code == 200:
                data = resp.json()
                answer = data.get("answer", "No answer received.")
                topic = data.get("topic", "general")

                # Update mastery scores in session state
                new_mastery = data.get("mastery_scores", {})
                st.session_state.mastery_scores.update(new_mastery)
            elif resp.status_code == 401:
                answer = "🔒 Session expired. Please log in again."
                topic = "error"
                st.session_state.authenticated = False
                st.rerun()
            else:
                detail = resp.json().get("detail", "Unknown error")
                answer = f"❌ Error: {detail}"
                topic = "error"

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(answer)
            if topic != "error":
                st.caption(f"📚 Topic: {topic}")

        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "topic": topic}
        )

        # Rerun to update sidebar mastery
        st.rerun()


# ─── Main App Flow ───────────────────────────────────────────────

if not st.session_state.authenticated:
    if st.session_state.auth_page == "register":
        show_register_page()
    else:
        show_login_page()
else:
    show_sidebar()
    show_chat()
