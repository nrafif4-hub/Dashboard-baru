"""
Modul autentikasi sederhana — One Ummah Foundation.
Menggunakan streamlit-authenticator v0.4.x.
"""

import os
import yaml
import streamlit as st

AUTH_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def _load_auth_config():
    if not os.path.exists(AUTH_CONFIG_PATH):
        return None
    with open(AUTH_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_login():
    """Tampilkan form login. Return True jika sudah login."""
    config = _load_auth_config()
    if config is None:
        st.session_state["auth_role"] = "admin"
        st.session_state["auth_name"] = "Developer"
        st.session_state["auth_username"] = "dev"
        return True

    try:
        import streamlit_authenticator as stauth
    except ImportError:
        st.warning("⚠ `streamlit-authenticator` belum terpasang. Mode development (tanpa login).")
        st.session_state["auth_role"] = "admin"
        st.session_state["auth_name"] = "Developer"
        st.session_state["auth_username"] = "dev"
        return True

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        auto_hash=False,
    )

    # v0.4.x login() — returns tuple & sets session_state
    try:
        authenticator.login(location="main")
    except Exception:
        try:
            authenticator.login("Login", "main")
        except Exception:
            authenticator.login()

    status = st.session_state.get("authentication_status")

    if status is True:
        username = st.session_state.get("username", "")
        user_data = config["credentials"]["usernames"].get(username, {})
        st.session_state["auth_role"] = user_data.get("role", "viewer")
        st.session_state["auth_name"] = user_data.get("name", username)
        st.session_state["auth_username"] = username
        st.session_state["_authenticator"] = authenticator
        return True
    elif status is False:
        st.error("❌ Username atau password salah.")
        return False
    else:
        return False


def get_user_role():
    return st.session_state.get("auth_role", "viewer")

def get_user_name():
    return st.session_state.get("auth_name", "Unknown")

def get_username():
    return st.session_state.get("auth_username", "unknown")

def is_admin():
    return get_user_role() == "admin"

def can_access_page(page_title):
    config = _load_auth_config()
    if config is None:
        return True
    role = get_user_role()
    roles_config = config.get("roles", {})
    role_config = roles_config.get(role, {})
    allowed = role_config.get("pages", [])
    if "all" in allowed:
        return True
    return page_title in allowed


def show_logout_button():
    if st.session_state.get("authentication_status"):
        role = get_user_role().replace("_", " ").title()
        st.sidebar.markdown(f"👤 **{get_user_name()}** · {role}")
        auth = st.session_state.get("_authenticator")
        if auth:
            try:
                auth.logout("🚪 Logout", "sidebar")
            except Exception:
                if st.sidebar.button("🚪 Logout"):
                    for key in ["authentication_status", "username", "name",
                                "auth_role", "auth_name", "auth_username", "_authenticator"]:
                        st.session_state.pop(key, None)
                    st.rerun()
        else:
            if st.sidebar.button("🚪 Logout"):
                for key in ["authentication_status", "username", "name",
                            "auth_role", "auth_name", "auth_username"]:
                    st.session_state.pop(key, None)
                st.rerun()
