# main.py
import sys
import os

from PyQt5.QtWidgets import QApplication

from pointcloudviewer import PointCloudViewer

from login import LoginDialog


def main():
    app = QApplication(sys.argv)

    # Show login dialog first
    login_dlg = LoginDialog()
    if login_dlg.exec_() != LoginDialog.Accepted:
        # User cancelled login
        sys.exit(0)
    # Login successful → open main application
    window = PointCloudViewer()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()