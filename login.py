# ============================================================================================================================================
#                                                          ** Login Page Code **
# ============================================================================================================================================
import os
import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTabWidget, QWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QPixmap

# Folder and file paths
USER_FOLDER = r"E:\3D_Tool\user"
USER_FILE = os.path.join(USER_FOLDER, "user_config.txt")
LAST_LOGIN_FILE = os.path.join(USER_FOLDER, "last_login.json")  # New file to remember last login

os.makedirs(USER_FOLDER, exist_ok=True)


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login / Register")
        self.setModal(True)
        self.resize(850, 550)
        self.setMinimumSize(800, 450)

        # Set unified gradient background for the entire dialog
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2E1B47, stop:0.5 #5D3A9B, stop:1 #8A2BE2);
                border-radius: 10px;
            }
        """)

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === LEFT SIDEBAR ===
        self.left_sidebar = QFrame()
        self.left_sidebar.setFixedWidth(400)
        self.left_sidebar.setStyleSheet("""
            QFrame {
                background: transparent;
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
            }
        """)

        sidebar_layout = QVBoxLayout(self.left_sidebar)
        sidebar_layout.setContentsMargins(40, 40, 40, 40)
        sidebar_layout.setSpacing(20)

        # Welcome title
        title = QLabel("Welcome")
        title.setStyleSheet("""
            QLabel {
                color: white; 
                font-size: 36px; 
                font-weight: bold;
                background: transparent;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title, alignment=Qt.AlignCenter)

        # === LOGO ===
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(180, 180)
        self.logo_label.setStyleSheet("background: transparent;")

        logo_path = r"C:\Users\hp\OneDrive\Documents\milogo\MI_logo.png"

        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        else:
            self.logo_label.setText("LOGO")
            self.logo_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.8);
                    font-size: 28px;
                    font-weight: bold;
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 90px;
                }
            """)

        sidebar_layout.addWidget(self.logo_label, alignment=Qt.AlignCenter)

        # App name
        app_name = QLabel("Micro Integrated")
        app_name.setStyleSheet("""
            QLabel {
                color: white; 
                font-size: 32px;
                font: bold;
                background: transparent;
            }
        """)
        app_name.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(app_name, alignment=Qt.AlignCenter)

        # Subtitle
        subtitle = QLabel("3D Point Cloud")
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 28px;
                font: bold;
                background: transparent;
            }
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(subtitle, alignment=Qt.AlignCenter)

        sidebar_layout.addStretch(1)
        sidebar_layout.addStretch(1)

        # === RIGHT CONTENT ===
        self.right_frame = QFrame()
        self.right_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)

        right_layout = QVBoxLayout(self.right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget {
                background: transparent;
            }
            QTabWidget::pane { 
                border: none; 
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
            QTabBar {
                spacing: 15px;
            }
            QTabBar::tab {
                padding: 15px 15px;
                margin-right: 5px;
                font-size: 13px;
                font : bold;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: rgba(255, 255, 255, 0.3);
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:!selected {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.8);
            }
            QTabBar::tab:hover {
                background: rgba(255, 255, 255, 0.25);
            }
        """)
        self.tabs.addTab(self.create_login_tab(), "Login")
        self.tabs.addTab(self.create_register_tab(), "Register")

        right_layout.addWidget(self.tabs)

        # Add to main layout
        main_layout.addWidget(self.left_sidebar)
        main_layout.addWidget(self.right_frame, stretch=1)

        # Public attribute to store logged-in username
        self.logged_in_username = None

        # === AUTO-FILL LAST LOGIN ===
        self.load_last_login()

    def load_last_login(self):
        """Load the last successfully logged-in user's credentials and auto-fill the login tab"""
        if not os.path.exists(LAST_LOGIN_FILE):
            return

        try:
            with open(LAST_LOGIN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                last_username = data.get("username", "")
                last_password = data.get("password", "")

                if last_username:
                    self.login_username.setText(last_username)
                    self.login_password.setText(last_password)
                    # Optionally switch to login tab
                    self.tabs.setCurrentIndex(0)
        except Exception as e:
            print(f"Could not load last login info: {e}")

    def save_last_login(self, username, password):
        """Save the current successful login so it can be auto-filled next time"""
        try:
            data = {
                "username": username,
                "password": password,
                "saved_at": __import__('datetime').datetime.now().isoformat()
            }
            with open(LAST_LOGIN_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Could not save last login: {e}")

    def create_login_tab(self):
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 30, 20, 30)

        title_label = QLabel("<h2 style='color: white;'>Login to Your Account</h2>")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("background: transparent;")
        layout.addWidget(title_label)

        # Username field
        username_label = QLabel("Username:")
        username_label.setStyleSheet("color: white; font-size: 14px; background: transparent;")
        layout.addWidget(username_label)
        
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter username")
        self.login_username.setStyleSheet("""
            QLineEdit {
                font-size: 14px; 
                padding: 10px;
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background: white;
            }
        """)
        layout.addWidget(self.login_username)

        # Password field
        password_label = QLabel("Password:")
        password_label.setStyleSheet("color: white; font-size: 14px; background: transparent;")
        layout.addWidget(password_label)
        
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Enter password")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setStyleSheet("""
            QLineEdit {
                font-size: 14px; 
                padding: 10px;
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background: white;
            }
        """)
        layout.addWidget(self.login_password)

        # Login button
        btn_layout = QHBoxLayout()
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px;
                font-size: 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
        """)
        login_btn.clicked.connect(self.do_login)
        btn_layout.addStretch()
        btn_layout.addWidget(login_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Register link
        self.register_link = QLabel(
            '<a href="#" style="color: rgba(255, 255, 255, 0.9); text-decoration: none; font-size: 14px;">New here? <strong style="color: #3498db;">Register</strong></a>'
        )
        self.register_link.setAlignment(Qt.AlignCenter)
        self.register_link.setOpenExternalLinks(False)
        self.register_link.linkActivated.connect(self.switch_to_register_tab)
        self.register_link.setCursor(QCursor(Qt.PointingHandCursor))
        self.register_link.setStyleSheet("background: transparent;")
        layout.addWidget(self.register_link)
        
        layout.addStretch()

        return widget

    def switch_to_register_tab(self):
        self.tabs.setCurrentIndex(1)

    def create_register_tab(self):
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 30, 20, 30)

        title_label = QLabel("<h2 style='color: white;'>Create New Account</h2>")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("background: transparent;")
        layout.addWidget(title_label)

        # Username field
        username_label = QLabel("Username:")
        username_label.setStyleSheet("color: white; font-size: 14px; background: transparent;")
        layout.addWidget(username_label)
        
        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Choose a username")
        self.reg_username.setStyleSheet("""
            QLineEdit {
                font-size: 14px; 
                padding: 10px;
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #27ae60;
                background: white;
            }
        """)
        layout.addWidget(self.reg_username)

        # Password field
        password_label = QLabel("Password:")
        password_label.setStyleSheet("color: white; font-size: 14px; background: transparent;")
        layout.addWidget(password_label)
        
        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("Create a password")
        self.reg_password.setEchoMode(QLineEdit.Password)
        self.reg_password.setStyleSheet("""
            QLineEdit {
                font-size: 14px; 
                padding: 10px;
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #27ae60;
                background: white;
            }
        """)
        layout.addWidget(self.reg_password)

        # Confirm password field
        confirm_label = QLabel("Confirm Password:")
        confirm_label.setStyleSheet("color: white; font-size: 14px; background: transparent;")
        layout.addWidget(confirm_label)
        
        self.reg_confirm = QLineEdit()
        self.reg_confirm.setPlaceholderText("Confirm your password")
        self.reg_confirm.setEchoMode(QLineEdit.Password)
        self.reg_confirm.setStyleSheet("""
            QLineEdit {
                font-size: 14px; 
                padding: 10px;
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #27ae60;
                background: white;
            }
        """)
        layout.addWidget(self.reg_confirm)

        # Register button
        btn_layout = QHBoxLayout()
        reg_btn = QPushButton("Register")
        reg_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px;
                font-size: 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        reg_btn.clicked.connect(self.do_register)
        btn_layout.addStretch()
        btn_layout.addWidget(reg_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        layout.addStretch()

        return widget

    def do_register(self):
        username = self.reg_username.text().strip()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password are required!")
            return
        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match!")
            return
        if len(password) < 4:
            QMessageBox.warning(self, "Error", "Password must be at least 4 characters!")
            return

        if self.user_exists(username):
            QMessageBox.warning(self, "Error", "Username already exists!")
            return

        user_data = {
            "username": username,
            "password": password,  # TODO: Hash in production!
            "registered_at": __import__('datetime').datetime.now().isoformat()
        }

        try:
            with open(USER_FILE, 'a', encoding='utf-8') as f:
                json.dump(user_data, f)
                f.write('\n')
            QMessageBox.information(self, "Success", f"User '{username}' registered successfully!")
            self.reg_username.clear()
            self.reg_password.clear()
            self.reg_confirm.clear()
            self.tabs.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save user: {e}")

    def do_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password!")
            return

        if self.check_credentials(username, password):
            # SUCCESS
            self.logged_in_username = username
            self.save_last_login(username, password)  # Remember this login
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password!")

    def user_exists(self, username):
        if not os.path.exists(USER_FILE):
            return False
        with open(USER_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("username", "").lower() == username.lower():
                            return True
                    except:
                        continue
        return False

    def check_credentials(self, username, password):
        if not os.path.exists(USER_FILE):
            return False
        with open(USER_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if (data.get("username", "").lower() == username.lower() and
                                data.get("password") == password):
                            return True
                    except:
                        continue
        return False