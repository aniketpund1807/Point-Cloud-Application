
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTabWidget, QWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QPixmap
from passlib.hash import django_pbkdf2_sha256
from database import DatabaseHandler

# Folder and file paths
USER_FOLDER = r"E:\3D_Tool\user"
LAST_LOGIN_FILE = os.path.join(USER_FOLDER, "last_login.json")
os.makedirs(USER_FOLDER, exist_ok=True)


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login / Register")
        self.setModal(True)
        self.resize(850, 550)
        self.setMinimumSize(1000, 800)

        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2E1B47, stop:0.5 #5D3A9B, stop:1 #8A2BE2);
                border-radius: 10px;
            }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # LEFT SIDEBAR
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

        title = QLabel("Welcome")
        title.setStyleSheet("color: white; font-size: 36px; font-weight: bold; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title, alignment=Qt.AlignCenter)

        # Logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(180, 180)
        self.logo_label.setStyleSheet("background: transparent;")
        logo_path = r"C:\Users\hp\OneDrive\Documents\milogo\MI_logo.png"
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("LOGO")
            self.logo_label.setStyleSheet("""
                color: rgba(255,255,255,0.8); font-size: 28px; font-weight: bold;
                background-color: rgba(255,255,255,0.1); border-radius: 90px;
            """)
        sidebar_layout.addWidget(self.logo_label, alignment=Qt.AlignCenter)

        app_name = QLabel("Micro Integrated")
        app_name.setStyleSheet("color: white; font-size: 32px; font-weight: bold; background: transparent;")
        app_name.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(app_name, alignment=Qt.AlignCenter)

        subtitle = QLabel("3D Point Cloud")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 28px; font-weight: bold; background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(subtitle, alignment=Qt.AlignCenter)

        sidebar_layout.addStretch(1)

        # RIGHT CONTENT
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

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: rgba(255,255,255,0.1); border-radius: 8px; }
            QTabBar::tab { padding: 15px; margin-right: 5px; font-size: 13px; font-weight: bold;
                           background: rgba(255,255,255,0.2); color: white; border-top-left-radius: 8px;
                           border-top-right-radius: 8px; min-width: 100px; }
            QTabBar::tab:selected { background: rgba(255,255,255,0.3); }
            QTabBar::tab:!selected { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.8); }
            QTabBar::tab:hover { background: rgba(255,255,255,0.25); }
        """)
        self.tabs.addTab(self.create_login_tab(), "Login")
        self.tabs.addTab(self.create_register_tab(), "Register")
        right_layout.addWidget(self.tabs)

        main_layout.addWidget(self.left_sidebar)
        main_layout.addWidget(self.right_frame, stretch=1)

        self.logged_in_username = None
        self.load_last_login()

    def load_last_login(self):
        if not os.path.exists(LAST_LOGIN_FILE):
            return
        try:
            with open(LAST_LOGIN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                username = data.get("username", "")
                if username:
                    self.login_username.setText(username)
                    self.tabs.setCurrentIndex(0)
        except:
            pass

    def save_last_login(self, username):
        try:
            data = {"username": username, "saved_at": datetime.now().isoformat()}
            with open(LAST_LOGIN_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except:
            pass

    def create_login_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 30, 20, 30)

        title = QLabel("<h2 style='color:white;'>Login to Your Account</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(QLabel("Username:", styleSheet="color:white; font-size:14px;"))
        self.login_username = QLineEdit(placeholderText="Enter username")
        self.login_username.setStyleSheet("font-size:14px; padding:10px; background:rgba(255,255,255,0.9); border:1px solid rgba(255,255,255,0.3); border-radius:5px;")
        layout.addWidget(self.login_username)

        layout.addWidget(QLabel("Password:", styleSheet="color:white; font-size:14px;"))
        self.login_password = QLineEdit(placeholderText="Enter password")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setStyleSheet("font-size:14px; padding:10px; background:rgba(255,255,255,0.9); border:1px solid rgba(255,255,255,0.3); border-radius:5px;")
        layout.addWidget(self.login_password)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("background:#3498db; color:white; padding:12px; font-size:16px; border-radius:6px;")
        login_btn.clicked.connect(self.do_login)
        btn_layout.addWidget(login_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        register_link = QLabel('<a href="#" style="color:#3498db;">New here? <strong>Register</strong></a>')
        register_link.setAlignment(Qt.AlignCenter)
        register_link.linkActivated.connect(lambda: self.tabs.setCurrentIndex(1))
        layout.addWidget(register_link)

        layout.addStretch()
        return widget

    def create_register_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 30, 20, 30)

        title = QLabel("<h2 style='color:white;'>Create New Account</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.reg_full_name = QLineEdit(placeholderText="Enter full name")
        self.reg_email = QLineEdit(placeholderText="Enter email")
        self.reg_username = QLineEdit(placeholderText="Choose a username")
        self.reg_mobile = QLineEdit(placeholderText="Enter mobile number")
        self.reg_password = QLineEdit(placeholderText="Create a password")
        self.reg_confirm = QLineEdit(placeholderText="Confirm your password")

        fields = [
            ("Full Name:", self.reg_full_name, False),
            ("Email:", self.reg_email, False),
            ("Username:", self.reg_username, False),
            ("Mobile Number:", self.reg_mobile, False),
            ("Password:", self.reg_password, True),
            ("Confirm Password:", self.reg_confirm, True),
        ]

        for label_text, field_widget, is_password in fields:
            layout.addWidget(QLabel(label_text, styleSheet="color:white; font-size:14px;"))
            if is_password:
                field_widget.setEchoMode(QLineEdit.Password)
            field_widget.setStyleSheet("font-size:14px; padding:10px; background:rgba(255,255,255,0.9); border:1px solid rgba(255,255,255,0.3); border-radius:5px;")
            layout.addWidget(field_widget)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        reg_btn = QPushButton("Register")
        reg_btn.setStyleSheet("background:#27ae60; color:white; padding:12px; font-size:16px; border-radius:6px;")
        reg_btn.clicked.connect(self.do_register)
        btn_layout.addWidget(reg_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()
        return widget

    def do_register(self):
        full_name = self.reg_full_name.text().strip()
        email = self.reg_email.text().strip()
        username = self.reg_username.text().strip()
        mobile = self.reg_mobile.text().strip()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()

        if not all([full_name, email, username, mobile, password]):
            QMessageBox.warning(self, "Error", "All fields are required!")
            return
        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match!")
            return
        if len(password) < 4:
            QMessageBox.warning(self, "Error", "Password must be at least 4 characters!")
            return
        if '@' not in email or '.' not in email:
            QMessageBox.warning(self, "Error", "Invalid email format!")
            return
        if len(mobile) != 10 or not mobile.isdigit():
            QMessageBox.warning(self, "Error", "Mobile number must be 10 digits!")
            return

        db = DatabaseHandler()
        if not db.connect():
            QMessageBox.critical(self, "Error", "Cannot connect to database.")
            return

        try:
            user_id = db.get_next_id('user_header_all')

            # Check username exists
            db.cursor.execute("SELECT 1 FROM user_header_all WHERE user_username = %s LIMIT 1", (username,))
            if db.cursor.fetchone():
                QMessageBox.warning(self, "Error", "Username already exists!")
                return

            hashed_pw = django_pbkdf2_sha256.hash(password)
            now = datetime.now()
            future = datetime(9999, 12, 31, 23, 59, 59)

            query = """
            INSERT INTO user_header_all (
                user_id, user_full_name, user_email, user_username, user_password,
                user_mobile_no, user_type, status, user_inserted_on, valid_till,
                permitted_operation, mobile_token
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                user_id, full_name, email, username, hashed_pw,
                mobile, 1, 1, now, future,
                1, ''
            )

            db.cursor.execute(query, values)
            db.connection.commit()

            # ========== CREATE USER FOLDER AND CONFIG FILE ==========
            user_folder = os.path.join(USER_FOLDER, user_id)
            os.makedirs(user_folder, exist_ok=True)

            # Create user_config.txt with all registration details
            user_config_file = os.path.join(user_folder, "user_config.txt")
            user_config_data = {
                "user_id": user_id,
                "full_name": full_name,
                "email": email,
                "username": username,
                "mobile_number": mobile,
                "user_type": 1,
                "status": 1,
                "registered_on": now.isoformat(),
                "last_login": now.isoformat(),
                "valid_till": future.isoformat()
            }

            try:
                with open(user_config_file, 'w', encoding='utf-8') as f:
                    json.dump(user_config_data, f, indent=4, ensure_ascii=False)
            except Exception as file_error:
                print(f"Warning: Could not create user config file: {file_error}")

            # Update last_login.json
            self.save_last_login(username)

            QMessageBox.information(self, "Success", f"User '{username}' registered successfully!")
            self.reg_full_name.clear()
            self.reg_email.clear()
            self.reg_username.clear()
            self.reg_mobile.clear()
            self.reg_password.clear()
            self.reg_confirm.clear()
            self.tabs.setCurrentIndex(0)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Registration failed:\n{str(e)}")
        finally:
            db.disconnect()

    def do_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password!")
            return

        db = DatabaseHandler()
        if not db.connect():
            QMessageBox.critical(self, "Error", "Cannot connect to database.")
            return

        try:
            db.cursor.execute(
                "SELECT user_password FROM user_header_all WHERE user_username = %s AND status = 1",
                (username,)
            )
            row = db.cursor.fetchone()
            if row and django_pbkdf2_sha256.verify(password, row['user_password']):
                self.logged_in_username = username
                self.save_last_login(username)
                self.accept()
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login error:\n{str(e)}")
        finally:
            db.disconnect()