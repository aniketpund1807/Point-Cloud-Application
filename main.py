# main.py
import sys
import os

from PyQt5.QtWidgets import QApplication

from pointcloudviewer import PointCloudViewer

from login import LoginDialog


# main.py (updated)
def main():
    app = QApplication(sys.argv)

    # Show login dialog first
    login_dlg = LoginDialog()
    if login_dlg.exec_() != LoginDialog.Accepted:
        # User cancelled login
        sys.exit(0)

    username = login_dlg.logged_in_username  # This attribute was already set in login.py

    window = PointCloudViewer(username=username)  # Pass username
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()