import sys
from PyQt5.QtWidgets import QApplication
from pointcloudviewer import PointCloudViewer
# from pointcloudviewer_new import PointCloudViewer

def main():
    app = QApplication(sys.argv)
    viewer = PointCloudViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()