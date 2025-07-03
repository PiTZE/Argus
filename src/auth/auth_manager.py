"""Enhanced authentication and user management."""

import streamlit as st
import streamlit_authenticator as stauth
import logging
from typing import Optional, Dict, Any
from src.core.config import config

logger = logging.getLogger(__name__)

class AuthManager:
    """Enhanced authentication manager with improved security."""
    
    def __init__(self):
        self.authenticator = None
        self._initialize_authenticator()
    
    def _initialize_authenticator(self):
        """Initialize the streamlit authenticator."""
        try:
            auth_config = config.auth_config
            
            if not auth_config or 'credentials' not in auth_config:
                logger.error("Authentication configuration not found")
                st.error("❌ Authentication configuration missing. Please check config.yaml")
                st.stop()
            
            self.authenticator = stauth.Authenticate(
                auth_config['credentials'],
                auth_config['cookie']['name'],
                auth_config['cookie']['key'],
                auth_config['cookie']['expiry_days']
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize authenticator: {e}")
            st.error(f"❌ Authentication initialization failed: {e}")
            st.stop()
    
    def login(self) -> bool:
        """Handle user login with enhanced security."""
        try:
            # Display login form
            name, authentication_status, username = self.authenticator.login()
            
            if authentication_status is False:
                st.error('❌ Username/password is incorrect')
                self._log_failed_login(username)
                return False
            elif authentication_status is None:
                st.warning('⚠️ Please enter your username and password')
                return False
            elif authentication_status:
                self._log_successful_login(username)
                return True
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            st.error(f"❌ Login failed: {e}")
            return False
    
    def logout(self):
        """Handle user logout."""
        try:
            self.authenticator.logout('Logout', 'sidebar')
        except Exception as e:
            logger.error(f"Logout error: {e}")
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user information."""
        if st.session_state.get("authentication_status"):
            return {
                'username': st.session_state.get("username"),
                'name': st.session_state.get("name"),
                'email': self._get_user_email(st.session_state.get("username"))
            }
        return None
    
    def _get_user_email(self, username: str) -> Optional[str]:
        """Get user email from configuration."""
        try:
            auth_config = config.auth_config
            user_config = auth_config['credentials']['usernames'].get(username, {})
            return user_config.get('email')
        except Exception:
            return None
    
    def _log_successful_login(self, username: str):
        """Log successful login attempt."""
        logger.info(f"Successful login: {username}")
    
    def _log_failed_login(self, username: str):
        """Log failed login attempt."""
        logger.warning(f"Failed login attempt: {username}")
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return st.session_state.get("authentication_status") is True
    
    def require_authentication(self):
        """Decorator/function to require authentication."""
        if not self.is_authenticated():
            if not self.login():
                st.stop()
    
    def get_user_display_name(self) -> str:
        """Get display name for current user."""
        user = self.get_current_user()
        if user:
            return user.get('name', user.get('username', 'Unknown'))
        return 'Guest'

# Global auth manager instance
auth_manager = AuthManager()