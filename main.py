import sys
from PyQt5.QtWidgets import QApplication
from pointcloudviewer import PointCloudViewer 
#from pointcloudviewer import PointCloudViewer 

def main():
    app = QApplication(sys.argv)
    window = PointCloudViewer()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()