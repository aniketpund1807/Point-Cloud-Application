import numpy as np
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QGridLayout, QGroupBox, QCheckBox, 
    QTextEdit, QComboBox, QDoubleSpinBox, QRadioButton, QButtonGroup, QWidget, QFileDialog, QInputDialog, QMessageBox,
    QScrollArea, QMenu, QAction
)
from PyQt5.QtCore import Qt
import os
import json

from datetime import datetime
import glob

# ===========================================================================================================================
# ** ZERO LINE DIALOG **
# ===========================================================================================================================
class ZeroLineDialog(QDialog):
    def __init__(self, point1=None, point2=None, km1=None, chain1=None, km2=None, chain2=None, interval=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zero Line Configuration")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #e6e6fa, stop:1 #e6e6fa);
                border-radius: 20px;
            }
            QLabel {
                color: black;
                font-weight: 500;
            }
            QFrame {
                background-color: rgba(255,255,255,0.2);
                border-radius: 10px;
                margin: 5px;
                padding: 10px;
            }
            QGroupBox {
                border: 2px solid #7B1FA2;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 10px;
                font-weight: bold;
                color: #4A148C;
                background-color: rgba(255,255,255,0.3);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 3px 8px;
                font-size: 12px;
            }
            QLineEdit {
                border: 2px solid #9C27B0;
                border-radius: 8px;
                padding: 8px;
                background-color: white;
                selection-background-color: #CE93D8;
                font-weight: 500;
            }
            QLineEdit:focus {
                border: 2px solid #7B1FA2;
                background-color: #F3E5F5;
            }
            QPushButton {
                border-radius: 20px;
                padding: 10px;
                font-weight: bold;
                min-width: 120px;
                border: none;
            }
            QPushButton#saveBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #9C27B0, stop:1 #6A1B9A);
                color: white;
            }
            QPushButton#saveBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #AB47BC, stop:1 #4A148C);
            }
            QPushButton#saveBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #6A1B9A, stop:1 #4A148C);
                padding: 12px 10px 8px 10px;
            }
            QPushButton#cancelBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #E1BEE7, stop:1 #CE93D8);
                color: #333333;
            }
            QPushButton#cancelBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #D1C4E9, stop:1 #BA68C8);
            }
            QPushButton#cancelBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #CE93D8, stop:1 #8E24AA);
                padding: 12px 10px 8px 10px;
            }
        """)
        layout = QVBoxLayout()
        # Point 1 coordinates - editable
        group_p1 = QGroupBox("Point 1 Coordinates")
        layout_p1 = QGridLayout(group_p1)
        layout_p1.addWidget(QLabel("X:"), 0, 0)
        self.x1_edit = QLineEdit(f"{point1[0]:.3f}" if point1 is not None else "0.000")
        layout_p1.addWidget(self.x1_edit, 0, 1)
        layout_p1.addWidget(QLabel("Y:"), 0, 2)
        self.y1_edit = QLineEdit(f"{point1[1]:.3f}" if point1 is not None else "0.000")
        layout_p1.addWidget(self.y1_edit, 0, 3)
        layout_p1.addWidget(QLabel("Z:"), 1, 0)
        self.z1_edit = QLineEdit(f"{point1[2]:.3f}" if point1 is not None else "0.000")
        layout_p1.addWidget(self.z1_edit, 1, 1)
        layout.addWidget(group_p1)
        # Point 1 KM and Chainage
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Point 1 KM:"))
        self.km1_edit = QLineEdit(str(km1) if km1 is not None else "")
        row1.addWidget(self.km1_edit)
        row1.addWidget(QLabel("Chainage:"))
        self.chain1_edit = QLineEdit(str(chain1) if chain1 is not None else "")
        row1.addWidget(self.chain1_edit)
        layout.addLayout(row1)
        # Point 2 coordinates - editable
        group_p2 = QGroupBox("Point 2 Coordinates")
        layout_p2 = QGridLayout(group_p2)
        layout_p2.addWidget(QLabel("X:"), 0, 0)
        self.x2_edit = QLineEdit(f"{point2[0]:.3f}" if point2 is not None else "0.000")
        layout_p2.addWidget(self.x2_edit, 0, 1)
        layout_p2.addWidget(QLabel("Y:"), 0, 2)
        self.y2_edit = QLineEdit(f"{point2[1]:.3f}" if point2 is not None else "0.000")
        layout_p2.addWidget(self.y2_edit, 0, 3)
        layout_p2.addWidget(QLabel("Z:"), 1, 0)
        self.z2_edit = QLineEdit(f"{point2[2]:.3f}" if point2 is not None else "0.000")
        layout_p2.addWidget(self.z2_edit, 1, 1)
        layout.addWidget(group_p2)
        # Point 2 KM and Chainage
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Point 2 KM:"))
        self.km2_edit = QLineEdit(str(km2) if km2 is not None else "")
        row2.addWidget(self.km2_edit)
        row2.addWidget(QLabel("Chainage:"))
        self.chain2_edit = QLineEdit(str(chain2) if chain2 is not None else "")
        row2.addWidget(self.chain2_edit)
        layout.addLayout(row2)
        # Interval
        row_int = QHBoxLayout()
        row_int.addWidget(QLabel("Interval (m):"))
        self.interval_edit = QLineEdit(str(interval) if interval is not None else "20")
        row_int.addWidget(self.interval_edit)
        layout.addLayout(row_int)
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Zero Line")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    def get_points(self):
        try:
            p1 = np.array([float(self.x1_edit.text()), float(self.y1_edit.text()), float(self.z1_edit.text())])
            p2 = np.array([float(self.x2_edit.text()), float(self.y2_edit.text()), float(self.z2_edit.text())])
            return p1, p2
        except ValueError:
            return None, None

# ===========================================================================================================================
# ** CURVE DIALOG **
# ===========================================================================================================================
class CurveDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Curve Configuration")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #e6e6fa, stop:1 #e6e6fa);
                border-radius: 20px;
            }
            QLabel {
                color: black;
                font-weight: 500;
            }
            QCheckBox {
                color: black;
                font-weight: 500;
                spacing: 10px;
            }
            QLineEdit {
                border: 2px solid #9C27B0;
                border-radius: 8px;
                padding: 8px;
                background-color: white;
                selection-background-color: #CE93D8;
                font-weight: 500;
            }
            QLineEdit:focus {
                border: 2px solid #7B1FA2;
                background-color: #F3E5F5;
            }
            QPushButton {
                border-radius: 20px;
                padding: 10px;
                font-weight: bold;
                min-width: 80px;
                border: none;
            }
            QPushButton#okBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #9C27B0, stop:1 #6A1B9A);
                color: white;
            }
            QPushButton#okBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #AB47BC, stop:1 #4A148C);
            }
            QPushButton#okBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #6A1B9A, stop:1 #4A148C);
                padding: 12px 10px 8px 10px;
            }
            QPushButton#cancelBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #E1BEE7, stop:1 #CE93D8);
                color: #333333;
            }
            QPushButton#cancelBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #D1C4E9, stop:1 #BA68C8);
            }
            QPushButton#cancelBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #CE93D8, stop:1 #8E24AA);
                padding: 12px 10px 8px 10px;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Inner & Outer Curve checkboxes in one row
        checkbox_layout = QHBoxLayout()
        self.outer_checkbox = QCheckBox("Outer Curve")
        self.inner_checkbox = QCheckBox("Inner Curve")
        checkbox_layout.addWidget(self.outer_checkbox)
        checkbox_layout.addWidget(self.inner_checkbox)
        checkbox_layout.addStretch()
        layout.addLayout(checkbox_layout)
        
        # Single angle input below the checkboxes
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel("Angle:"))
        self.angle_edit = QLineEdit("0.0")
        self.angle_edit.setFixedWidth(80)
        angle_layout.addWidget(self.angle_edit)
        angle_layout.addStretch()
        layout.addLayout(angle_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setObjectName("okBtn")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def get_configuration(self):
        return {
            'outer_curve': self.outer_checkbox.isChecked(),
            'inner_curve': self.inner_checkbox.isChecked(),
            'angle': float(self.angle_edit.text() or 0.0)
        }

# ===========================================================================================================================
# ** CONSTRUCTION CONFIG DIALOG **
# ===========================================================================================================================
class ConstructionConfigDialog(QDialog):
    def __init__(self, chainage_label="", parent=None):
        super().__init__(parent)

        self.setWindowTitle("Construction Configuration")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #e6e6fa, stop:1 #e6e6fa);
                border-radius: 20px;
            }
            QLabel {
                color: black;
                font-weight: 500;
            }
            QFrame {
                background-color: rgba(255,255,255,0.2);
                border-radius: 10px;
                margin: 5px;
                padding: 10px;
            }
            QGroupBox {
                border: 2px solid #7B1FA2;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 10px;
                font-weight: bold;
                color: #4A148C;
                background-color: rgba(255,255,255,0.3);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 3px 8px;
                font-size: 12px;
            }
            QCheckBox {
                color: black;
                font-weight: 500;
                spacing: 10px;
            }
            QLineEdit {
                border: 2px solid #9C27B0;
                border-radius: 8px;
                padding: 8px;
                background-color: white;
                selection-background-color: #CE93D8;
                font-weight: 500;
            }
            QLineEdit:focus {
                border: 2px solid #7B1FA2;
                background-color: #F3E5F5;
            }
            QPushButton {
                border-radius: 20px;
                padding: 10px;
                font-weight: bold;
                min-width: 80px;
                border: none;
            }
            QPushButton#saveBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #9C27B0, stop:1 #6A1B9A);
                color: white;
            }
            QPushButton#saveBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #AB47BC, stop:1 #4A148C);
            }
            QPushButton#saveBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #6A1B9A, stop:1 #4A148C);
                padding: 12px 10px 8px 10px;
            }
            QPushButton#editBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #2196F3, stop:1 #1976D2);
                color: white;
            }
            QPushButton#editBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #42A5F5, stop:1 #1565C0);
            }
            QPushButton#editBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #1976D2, stop:1 #0D47A1);
                padding: 12px 10px 8px 10px;
            }
            QPushButton#cancelBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #E1BEE7, stop:1 #CE93D8);
                color: #333333;
            }
            QPushButton#cancelBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #D1C4E9, stop:1 #BA68C8);
            }
            QPushButton#cancelBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #CE93D8, stop:1 #8E24AA);
                padding: 12px 10px 8px 10px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ---------------- Title with chainage ----------------
        title = QLabel(f"CONSTRUCTION CONFIGURATION\nChainage {chainage_label}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #4A148C;
                padding: 10px;
                background-color: rgba(232, 245, 233, 0.7);
                border-radius: 5px;
                border: 1px solid #A5D6A7;
            }
        """)
        main_layout.addWidget(title)

        # ================= TOP: PILLAR POSITIONS =================
        pos_layout = QHBoxLayout()
        pos_label = QLabel("Pillar Positions:")
        pos_label.setStyleSheet("font-weight: bold;")
        pos_layout.addWidget(pos_label)

        self.cb_over_water = QCheckBox("Over the water")
        self.cb_under_water = QCheckBox("Under the water")
        pos_layout.addWidget(self.cb_over_water)
        pos_layout.addStretch()
        pos_layout.addWidget(self.cb_under_water)
        pos_layout.addStretch()

        main_layout.addLayout(pos_layout)

        # make Over/Under mutually exclusive
        self._make_exclusive_group([self.cb_over_water, self.cb_under_water])

        # ================= MIDDLE: SHAPES =================
        shapes_row_layout = QHBoxLayout()

        # --- Base (shape) ---
        base_group = QGroupBox("Base (shape)")
        base_layout = QVBoxLayout(base_group)
        self.cb_base_rectangle = QCheckBox("Rectangle")
        self.cb_base_square = QCheckBox("Square")
        self.cb_base_other = QCheckBox("Other")
        base_layout.addWidget(self.cb_base_rectangle)
        base_layout.addWidget(self.cb_base_square)
        base_layout.addWidget(self.cb_base_other)
        self._make_exclusive_group(
            [self.cb_base_rectangle, self.cb_base_square, self.cb_base_other]
        )
        shapes_row_layout.addWidget(base_group)

        # --- Pillar (shape) ---
        pillar_group = QGroupBox("Pillar (shape)")
        pillar_layout = QVBoxLayout(pillar_group)
        self.cb_pillar_circular = QCheckBox("Circular")
        self.cb_pillar_rectangular = QCheckBox("Rectangular")
        self.cb_pillar_other = QCheckBox("Other")
        pillar_layout.addWidget(self.cb_pillar_circular)
        pillar_layout.addWidget(self.cb_pillar_rectangular)
        pillar_layout.addWidget(self.cb_pillar_other)
        self._make_exclusive_group(
            [self.cb_pillar_circular, self.cb_pillar_rectangular, self.cb_pillar_other]
        )
        shapes_row_layout.addWidget(pillar_group)

        # --- Span (shape) ---
        span_shape_group = QGroupBox("Span (shape)")
        span_shape_layout = QVBoxLayout(span_shape_group)
        self.cb_span_vert = QCheckBox("Vert. shape")
        self.cb_span_flat = QCheckBox("Flat shape")
        self.cb_span_other = QCheckBox("Other")
        span_shape_layout.addWidget(self.cb_span_vert)
        span_shape_layout.addWidget(self.cb_span_flat)
        span_shape_layout.addWidget(self.cb_span_other)
        self._make_exclusive_group(
            [self.cb_span_vert, self.cb_span_flat, self.cb_span_other]
        )
        shapes_row_layout.addWidget(span_shape_group)

        main_layout.addLayout(shapes_row_layout)

        # ================= LOWER: DIMENSIONS =================
        dims_row_layout = QHBoxLayout()

        # --- Base dimension ---
        base_dim_group = QGroupBox("Base dimension")
        base_dim_layout = QGridLayout(base_dim_group)
        base_dim_layout.addWidget(QLabel("Width:"), 0, 0)
        self.le_base_width = QLineEdit()
        self.le_base_width.setPlaceholderText("______")
        base_dim_layout.addWidget(self.le_base_width, 0, 1)

        base_dim_layout.addWidget(QLabel("Length:"), 1, 0)
        self.le_base_length = QLineEdit()
        self.le_base_length.setPlaceholderText("______")
        base_dim_layout.addWidget(self.le_base_length, 1, 1)

        base_dim_layout.addWidget(QLabel("Height:"), 2, 0)
        self.le_base_height = QLineEdit()
        self.le_base_height.setPlaceholderText("______")
        base_dim_layout.addWidget(self.le_base_height, 2, 1)

        dims_row_layout.addWidget(base_dim_group)

        # --- Pillar Dimension ---
        pillar_dim_group = QGroupBox("Pillar Dimension")
        pillar_dim_layout = QGridLayout(pillar_dim_group)
        pillar_dim_layout.addWidget(QLabel("Radius:"), 0, 0)
        self.le_pillar_radius = QLineEdit()
        self.le_pillar_radius.setPlaceholderText("______")
        pillar_dim_layout.addWidget(self.le_pillar_radius, 0, 1)

        pillar_dim_layout.addWidget(QLabel("Height:"), 1, 0)
        self.le_pillar_height = QLineEdit()
        self.le_pillar_height.setPlaceholderText("______")
        pillar_dim_layout.addWidget(self.le_pillar_height, 1, 1)

        dims_row_layout.addWidget(pillar_dim_group)

        # --- Span Dimension ---
        span_dim_group = QGroupBox("Span Dimension")
        span_dim_layout = QGridLayout(span_dim_group)
        span_dim_layout.addWidget(QLabel("Height:"), 0, 0)
        self.le_span_height = QLineEdit()
        self.le_span_height.setPlaceholderText("______")
        span_dim_layout.addWidget(self.le_span_height, 0, 1)

        span_dim_layout.addWidget(QLabel("Width:"), 1, 0)
        self.le_span_width = QLineEdit()
        self.le_span_width.setPlaceholderText("______")
        span_dim_layout.addWidget(self.le_span_width, 1, 1)

        dims_row_layout.addWidget(span_dim_group)

        main_layout.addLayout(dims_row_layout)

        # ================= BOTTOM BUTTONS =================
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("saveBtn")
        self.btn_save.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_save)

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setObjectName("editBtn")
        self.btn_edit.clicked.connect(self.on_edit_clicked)
        btn_layout.addWidget(self.btn_edit)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("cancelBtn")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(btn_layout)

        self.chainage = chainage_label
        
    def on_edit_clicked(self):
        """Handle Edit button click - allows editing of saved configuration"""
        # You can implement edit functionality here
        # For now, we'll just close the dialog with a special result code
        self.done(2)  # Use 2 for edit mode

    # -------- helper for exclusive checkboxes --------
    def _make_exclusive_group(self, checkboxes):
        """Make checkboxes behave like radio buttons within the group"""
        def on_state_changed(checked_cb):
            if checked_cb.isChecked():
                for cb in checkboxes:
                    if cb is not checked_cb:
                        cb.blockSignals(True)
                        cb.setChecked(False)
                        cb.blockSignals(False)

        for cb in checkboxes:
            cb.stateChanged.connect(lambda _state, c=cb: on_state_changed(c))

    # ================= PUBLIC API =================
    def get_configuration(self):
        """Return all configuration values as a dict"""

        def selected_from_group(group_checks):
            for cb in group_checks:
                if cb.isChecked():
                    return cb.text()
            return None

        # Water position
        if self.cb_over_water.isChecked():
            water_pos = "Over the water"
        elif self.cb_under_water.isChecked():
            water_pos = "Under the water"
        else:
            water_pos = None

        base_shape = selected_from_group(
            [self.cb_base_rectangle, self.cb_base_square, self.cb_base_other]
        )
        pillar_shape = selected_from_group(
            [self.cb_pillar_circular, self.cb_pillar_rectangular, self.cb_pillar_other]
        )
        span_shape = selected_from_group(
            [self.cb_span_vert, self.cb_span_flat, self.cb_span_other]
        )

        return {
            "chainage": self.chainage,
            "water_position": water_pos,
            "base_shape": base_shape,
            "pillar_shape": pillar_shape,
            "span_shape": span_shape,
            "base_width": self.le_base_width.text(),
            "base_length": self.le_base_length.text(),
            "base_height": self.le_base_height.text(),
            "pillar_radius": self.le_pillar_radius.text(),
            "pillar_height": self.le_pillar_height.text(),
            "span_height": self.le_span_height.text(),
            "span_width": self.le_span_width.text(),
        }
    
# ===========================================================================================================================
# ** MATERIAL LINE DIALOG ** 
# ===========================================================================================================================    
class MaterialLineDialog(QDialog):
    def __init__(self, material_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Construction Layer")
        #self.setGeometry(300, 130, 500, 600)
        self.setModal(True)
        self.setFixedSize(500, 650)
        
        self.material_data = material_data if material_data else {
            'name': '',
            'description': '',
            'from_another': False,
            'material_layer': True,
            'ref_layer': '',
            'ref_line': '',
            'initial_filling': 0.0,
            'final_compressed': 0.0
        }
        
        self.setup_ui()
        self.load_material_data()
        self.update_ui_visibility()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Centered Title
        title_label = QLabel("Material line Configuration")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #000000;
            padding-bottom: 15px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Material Line Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Material line name:")
        name_label.setFixedWidth(150)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter material line name")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input, 1)
        layout.addLayout(name_layout)
        
        # Material Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Material Description:")
        desc_label.setFixedWidth(150)
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setPlaceholderText("Enter material description")
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input, 1)
        layout.addLayout(desc_layout)

        type_layout = QHBoxLayout()
        type_label = QLabel("Material Type:")
        type_label.setFixedWidth(150)
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("Enter material type")
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_input, 1)   
        layout.addLayout(type_layout)
        
        # Add spacer
        layout.addSpacing(10)
        
        # Material lines reference layers section
        ref_label = QLabel("Material lines reference layers")
        ref_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(ref_label)
        
        # Radio buttons section - only two buttons
        self.from_another_radio = QRadioButton("Material Line referring from Baselines")
        self.material_layer_radio = QRadioButton("Material Line referring from Material layer")
        
        # Set default selection to Material layer
        self.material_layer_radio.setChecked(True)
        
        # Connect radio buttons to update UI visibility
        self.from_another_radio.toggled.connect(self.update_ui_visibility)
        self.material_layer_radio.toggled.connect(self.update_ui_visibility)
        
        # Create button group
        self.ref_layer_group = QButtonGroup()
        self.ref_layer_group.addButton(self.from_another_radio)
        self.ref_layer_group.addButton(self.material_layer_radio)
        
        # Add radio buttons to layout
        radio_layout = QVBoxLayout()
        radio_layout.setSpacing(8)
        radio_layout.addWidget(self.from_another_radio)
        radio_layout.addWidget(self.material_layer_radio)
        layout.addLayout(radio_layout)
        
        # Add spacer
        layout.addSpacing(15)
        
        # Select Reference layer (dropdown) - hidden by default
        self.ref_layer_layout = QHBoxLayout()
        ref_layer_label = QLabel("Select Reference Baseline:")
        ref_layer_label.setFixedWidth(150)
        self.ref_layer_combo = QComboBox()
        self.ref_layer_combo.addItems(["None", "Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 5"])
        self.ref_layer_layout.addWidget(ref_layer_label)
        self.ref_layer_layout.addWidget(self.ref_layer_combo, 1)
        
        # Create container widget for reference layer
        self.ref_layer_widget = QWidget()
        self.ref_layer_widget.setLayout(self.ref_layer_layout)
        self.ref_layer_widget.setVisible(False)
        layout.addWidget(self.ref_layer_widget)
        
        # Select Reference line (dropdown) - visible by default
        self.ref_line_layout = QHBoxLayout()
        ref_line_label = QLabel("Select Reference Material line:")
        ref_line_label.setFixedWidth(150)
        self.ref_line_combo = QComboBox()
        self.ref_line_combo.addItems(["None", "Line 1", "Line 2", "Line 3", "Line 4", "Line 5"])
        self.ref_line_layout.addWidget(ref_line_label)
        self.ref_line_layout.addWidget(self.ref_line_combo, 1)
        
        # Create container widget for reference line
        self.ref_line_widget = QWidget()
        self.ref_line_widget.setLayout(self.ref_line_layout)
        self.ref_line_widget.setVisible(True)
        layout.addWidget(self.ref_line_widget)
        
        # Add spacer
        layout.addSpacing(15)
        
        # Define thickness section
        thickness_label = QLabel("Define thickness.")
        thickness_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(thickness_label)
        
        # Initial Filling thickness
        initial_layout = QHBoxLayout()
        initial_label = QLabel("Initial Filling thickness (mm):")
        initial_label.setFixedWidth(200)
        self.initial_spin = QDoubleSpinBox()
        self.initial_spin.setRange(0.0, 1000.0)
        self.initial_spin.setValue(0.0)
        self.initial_spin.setSingleStep(1.0)
        self.initial_spin.setSuffix(" mm")
        initial_layout.addWidget(initial_label)
        initial_layout.addWidget(self.initial_spin, 1)
        layout.addLayout(initial_layout)
        
        # Final Compressed thickness
        final_layout = QHBoxLayout()
        final_label = QLabel("Final Compressed thickness (mm):")
        final_label.setFixedWidth(200)
        self.final_spin = QDoubleSpinBox()
        self.final_spin.setRange(0.0, 1000.0)
        self.final_spin.setValue(0.0)
        self.final_spin.setSingleStep(1.0)
        self.final_spin.setSuffix(" mm")
        final_layout.addWidget(final_label)
        final_layout.addWidget(self.final_spin, 1)
        layout.addLayout(final_layout)
        
        # Add spacer
        layout.addStretch()
        
        # Save Button
        save_button = QPushButton("Save")
        save_button.setFixedSize(100, 35)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #005A9E; }
            QPushButton:pressed { background-color: #004578; }
        """)
        save_button.clicked.connect(self.accept)
        
        # Center the save button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def update_ui_visibility(self):
        """Show/hide dropdowns based on radio button selection"""
        if self.from_another_radio.isChecked():
            self.ref_layer_widget.setVisible(True)
            self.ref_line_widget.setVisible(False)
        else:  # Material layer is checked
            self.ref_layer_widget.setVisible(False)
            self.ref_line_widget.setVisible(True)
    
    def load_material_data(self):
        """Load material data into form fields"""
        if self.material_data:
            self.name_input.setText(self.material_data.get('name', ''))
            self.desc_input.setText(self.material_data.get('description', ''))
            
            # Set radio button states
            from_another = self.material_data.get('from_another', False)
            material_layer = self.material_data.get('material_layer', True)
            
            if from_another:
                self.from_another_radio.setChecked(True)
            else:
                self.material_layer_radio.setChecked(True)
            
            # Set dropdown values
            ref_layer = self.material_data.get('ref_layer', '')
            if ref_layer:
                index = self.ref_layer_combo.findText(ref_layer)
                if index >= 0:
                    self.ref_layer_combo.setCurrentIndex(index)
            
            ref_line = self.material_data.get('ref_line', '')
            if ref_line:
                index = self.ref_line_combo.findText(ref_line)
                if index >= 0:
                    self.ref_line_combo.setCurrentIndex(index)
            
            # Set thickness values
            initial_filling = self.material_data.get('initial_filling', 0.0)
            final_compressed = self.material_data.get('final_compressed', 0.0)
            
            # If values are in meters (old format), convert to mm
            if initial_filling < 1.0 and initial_filling > 0.0:
                initial_filling *= 1000
            if final_compressed < 1.0 and final_compressed > 0.0:
                final_compressed *= 1000
                
            self.initial_spin.setValue(initial_filling)
            self.final_spin.setValue(final_compressed)
    
    def get_material_data(self):
        """Return the material data entered in the dialog"""
        return {
            'name': self.name_input.text() or "Material Line",
            'description': self.desc_input.toPlainText(),
            'from_another': self.from_another_radio.isChecked(),
            'material_layer': self.material_layer_radio.isChecked(),
            'ref_layer': self.ref_layer_combo.currentText() if self.from_another_radio.isChecked() else '',
            'ref_line': self.ref_line_combo.currentText() if self.material_layer_radio.isChecked() else '',
            'initial_filling': self.initial_spin.value(),
            'final_compressed': self.final_spin.value()
        }
    
# ==========================================================================================================================================
#                                                    ** MEASUREMENT DIALOG **
# ==========================================================================================================================================

class MeasurementDialog(QDialog):
    def __init__(self, parent=None, show_presized=False):
        super().__init__(parent)
        self.setWindowTitle("Measurement Configuration")
        self.setModal(True)
        self.setMinimumWidth(520)

        # show_presized = True → we are in the “second” dialog after a vertical line is finished
        self.show_presized = show_presized

        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #f0e6fa, stop:1 #e6e6fa);
                border-radius: 18px;
            }
            QLabel {
                color: #2d1b3d;
                font-weight: 600;
                font-size: 13px;
            }
            QGroupBox {
                border: 2px solid #9C27B0;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: bold;
                color: #4A148C;
                background-color: rgba(255, 255, 255, 0.4);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 10px;
                background-color: #E1BEE7;
                border-radius: 6px;
            }
            QRadioButton, QCheckBox {
                font-weight: 500;
                spacing: 8px;
            }
            QComboBox, QLineEdit {
                border: 2px solid #BA68C8;
                border-radius: 8px;
                padding: 8px;
                background-color: white;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 2px solid #8E24AA;
                background-color: #F8E8FF;
            }
            QPushButton {
                border-radius: 20px;
                padding: 11px;
                font-weight: bold;
                min-width: 100px;
                border: none;
            }
            QPushButton#startBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #AB47BC, stop:1 #8E24AA);
                color: white;
            }
            QPushButton#startBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #9C27B0, stop:1 #7B1FA2);
            }
            QPushButton#cancelBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #E1BEE7, stop:1 #CE93D8);
                color: #333;
            }
            QPushButton#cancelBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #D1C4E9, stop:1 #BA68C8);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        # Title
        title = QLabel("Start New Measurement Session" if not show_presized else "Vertical Line Finished")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4A148C; padding: 10px;")
        layout.addWidget(title)

        # ------------------------------------------------------------------
        # LINE button with submenu (Vertical / Horizontal)
        # ------------------------------------------------------------------
        self.line_button = QPushButton("Line")
        self.line_menu = QMenu(self)
        self.vertical_action   = QAction("Vertical Line", self)
        self.horizontal_action = QAction("Horizontal Line", self)
        self.line_menu.addAction(self.vertical_action)
        self.line_menu.addAction(self.horizontal_action)
        self.line_button.setMenu(self.line_menu)
        layout.addWidget(self.line_button)

        # ------------------------------------------------------------------
        # PRESIZED button – visible only on the second dialog
        # ------------------------------------------------------------------
        self.presized_button = QPushButton("Presized")
        self.presized_button.setVisible(self.show_presized)
        layout.addWidget(self.presized_button)

        # ------------------------------------------------------------------
        # Polygon & Stockpile buttons (unchanged)
        # ------------------------------------------------------------------
        self.polygon_button = QPushButton("Polygon")
        layout.addWidget(self.polygon_button)

        self.stockpile_polygon_button = QPushButton("Stockpile Polygon")
        layout.addWidget(self.stockpile_polygon_button)

        self.complete_polygon_button = QPushButton("Complete Polygon")
        self.complete_polygon_button.setVisible(False)
        layout.addWidget(self.complete_polygon_button)

        # ------------------------------------------------------------------
        # Units
        # ------------------------------------------------------------------
        units_group = QGroupBox("Units")
        units_layout = QHBoxLayout(units_group)
        units_layout.addWidget(QLabel("Display Units:"))
        self.units_combo = QComboBox()
        self.units_combo.addItems(["Meter", "Centimeter", "Millimeter"])
        self.units_combo.setCurrentText("Meter")
        units_layout.addWidget(self.units_combo)
        layout.addWidget(units_group)

        # ------------------------------------------------------------------
        # Buttons (Start / Cancel)
        # ------------------------------------------------------------------
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.start_btn = QPushButton("Start Measurement" if not show_presized else "Continue")
        self.start_btn.setObjectName("startBtn")
        btn_layout.addWidget(self.start_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    # ----------------------------------------------------------------------
    # Helper – which action was chosen ?
    # ----------------------------------------------------------------------
    def get_selected_action(self):
        """Returns a string that tells the caller what the user really wants"""
        if self.vertical_action.isChecked():
            return "vertical_line"
        if self.horizontal_action.isChecked():
            return "horizontal_line"
        if self.presized_button.isVisible() and self.presized_button.isDown():
            return "presized_vertical"
        return None
    

# ===========================================================================================================================
# DESIGN NEW LAYER DIALOG – With Dynamic Dropdown Based on Road/Bridge Selection
# ===========================================================================================================================
class DesignNewDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Design Layer")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #f0e6fa, stop:1 #e6e6fa);
                border-radius: 18px;
            }
            QLabel {
                color: #2d1b3d;
                font-weight: 600;
                font-size: 13px;
            }
            QGroupBox {
                border: 2px solid #9C27B0;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: bold;
                color: #4A148C;
                background-color: rgba(255, 255, 255, 0.4);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 10px;
                background-color: #E1BEE7;
                border-radius: 6px;
            }
            QRadioButton, QCheckBox {
                font-weight: 500;
                spacing: 8px;
                font-size: 13px;
            }
            QComboBox {
                border: 2px solid #BA68C8;
                border-radius: 8px;
                padding: 8px;
                background-color: white;
                font-size: 13px;
            }
            QComboBox:focus {
                border: 2px solid #8E24AA;
                background-color: #F8E8FF;
            }
            QLineEdit {
                border: 2px solid #BA68C8;
                border-radius: 8px;
                padding: 8px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #8E24AA;
                background-color: #F8E8FF;
            }
            QPushButton {
                border-radius: 20px;
                padding: 11px;
                font-weight: bold;
                min-width: 100px;
                border: none;
            }
            QPushButton#okBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #AB47BC, stop:1 #8E24AA);
                color: white;
            }
            QPushButton#okBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #9C27B0, stop:1 #7B1FA2);
            }
            QPushButton#cancelBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #E1BEE7, stop:1 #CE93D8);
                color: #333;
            }
            QPushButton#cancelBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #D1C4E9, stop:1 #BA68C8);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        # Title
        title = QLabel("Create New Design Layer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4A148C; padding: 10px;")
        layout.addWidget(title)

        # ------------------ Layer Name -----------------
        layer_name_label = QLabel("Layer Name:")
        layer_name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(layer_name_label)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter unique layer name (required)")
        layout.addWidget(self.name_edit)
        
        # === Layer Dimension (3D / 2D) ===
        dim_group = QGroupBox("Layer Type")
        dim_layout = QVBoxLayout(dim_group)
        self.radio_3d = QRadioButton("3D")
        self.radio_2d = QRadioButton("2D")
        self.radio_3d.setChecked(True)  # Default to 3D
        dim_layout.addWidget(self.radio_3d)
        dim_layout.addWidget(self.radio_2d)
        layout.addWidget(dim_group)

        # === Road / Bridge Checkboxes (mutually exclusive) ===
        self.cb_road = QCheckBox("Road")
        self.cb_bridge = QCheckBox("Bridge")

        def toggle_exclusive(checked_cb):
            if checked_cb.isChecked():
                other = self.cb_bridge if checked_cb == self.cb_road else self.cb_road
                other.blockSignals(True)
                other.setChecked(False)
                other.blockSignals(False)
            self.update_reference_dropdown()

        self.cb_road.stateChanged.connect(lambda s: toggle_exclusive(self.cb_road) if s else self.update_reference_dropdown())
        self.cb_bridge.stateChanged.connect(lambda s: toggle_exclusive(self.cb_bridge) if s else self.update_reference_dropdown())

        layout.addWidget(self.cb_road)
        layout.addWidget(self.cb_bridge)

        # === Reference Layer Dropdown (Dynamic) ===
        self.ref_layer_group = QGroupBox("Reference Layer")
        ref_layer_layout = QVBoxLayout(self.ref_layer_group)

        self.combo_reference = QComboBox()
        self.combo_reference.setEnabled(False)

        ref_layer_layout.addWidget(QLabel("Select reference Layer 2D:"))
        ref_layer_layout.addWidget(self.combo_reference)
        layout.addWidget(self.ref_layer_group)

        # Initially visible only if 3D
        self.ref_layer_group.setVisible(True)
        self.update_reference_dropdown()

        # Connect dimension change
        self.radio_3d.toggled.connect(self.on_dimension_changed)
        self.radio_2d.toggled.connect(self.on_dimension_changed)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("okBtn")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def on_dimension_changed(self, checked):
        if not checked:
            return
        self.ref_layer_group.setVisible(self.radio_3d.isChecked())
        self.update_reference_dropdown()

    def update_reference_dropdown(self):
        self.combo_reference.clear()
        self.combo_reference.setEnabled(False)

        if not self.radio_3d.isChecked():
            return

        if self.cb_road.isChecked():
            items = ["Road_Layer_1", "Road_Layer_2", "Road_Layer_3"]
            self.ref_layer_group.setTitle("Reference Layer - Road")
        elif self.cb_bridge.isChecked():
            items = ["Bridge_Layer_1", "Bridge_Layer_2", "Bridge_Layer_3"]
            self.ref_layer_group.setTitle("Reference Layer - Bridge")
        else:
            self.ref_layer_group.setTitle("Reference Layer")
            return

        self.combo_reference.addItems(items)
        self.combo_reference.setCurrentIndex(0)
        self.combo_reference.setEnabled(True)

    def get_configuration(self):
        layer_name = self.name_edit.text().strip()
        if not layer_name:
            raise ValueError("Layer name is required!")

        reference_type = None
        reference_line = None

        if self.radio_3d.isChecked():
            if self.cb_road.isChecked():
                reference_type = "Road"
                reference_line = self.combo_reference.currentText()
            elif self.cb_bridge.isChecked():
                reference_type = "Bridge"
                reference_line = self.combo_reference.currentText()
        else:  # 2D
            if self.cb_road.isChecked():
                reference_type = "Road"
            elif self.cb_bridge.isChecked():
                reference_type = "Bridge"

        return {
            "layer_name": layer_name,
            "dimension": "3D" if self.radio_3d.isChecked() else "2D",
            "reference_type": reference_type,
            "reference_line": reference_line
        }


# ===========================================================================================================================
#                                                ** HELP Dialog Box **
# ===========================================================================================================================
class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>Point Cloud Viewer - Help</h2>
        <p>Welcome to the Point Cloud Viewer application. This tool allows you to visualize and analyze 3D point cloud data.</p>
        <h3>Features:</h3>
        <ul>
            <li>Load and display point cloud files in various formats.</li>
            <li>Measure distances, areas, and volumes within the point cloud.</li>
            <li>Create and manage design layers for construction projects.</li>
            <li>Generate worksheets to document measurements and designs.</li>
        </ul>
        <h3>Getting Started:</h3>
        <ol>
            <li>Use the 'File' menu to load a point cloud file.</li>
            <li>Navigate the 3D view using mouse controls (rotate, pan, zoom).</li>
            <li>Select measurement tools from the toolbar to start measuring.</li>
            <li>Create new design layers using the 'Design' menu.</li>
            <li>Generate worksheets from the 'Worksheet' menu.</li>
        </ol>
        <h3>Support:</h3>
        <p>If you encounter any issues or have questions, please contact our support team at
        <a href="mailto:
                          """)
        #help_text.setOpenExternalLinks(True)
        layout.addWidget(help_text)
        support_email = "info@microintegrated.in"
        help_text.append("{}.".format(support_email))

        # Close Button
        close_button = QPushButton("Close")
        close_button.setFixedSize(100, 35)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #005A9E; }
            QPushButton:pressed { background-color: #004578; }
        """)
        close_button.clicked.connect(self.accept)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

# ===========================================================================================================================
# NEW DIALOG: Construction Layer Creation Dialog (as shown in your image)
# ===========================================================================================================================
class ConstructionNewDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Construction Layer")
        self.setFixedSize(380, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F5F5;
                font-family: Segoe UI;
            }
            QLabel { font-size: 13px; color: #333; }
            QLineEdit {
                padding: 8px;
                border: 2px solid #BBB;
                border-radius: 6px;
                font-size: 13px;
            }
            QRadioButton { font-size: 13px; spacing: 8px; }
            QPushButton {
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 90px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("Create New Construction Layer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4A148C;")
        layout.addWidget(title)

        # Layer Name
        layout.addWidget(QLabel("Layer Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter layer name")
        layout.addWidget(self.name_edit)

        # Type Selection
        type_group = QGroupBox("Type")
        type_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        type_layout = QHBoxLayout()
        self.road_radio = QRadioButton("Road")
        self.bridge_radio = QRadioButton("Bridge")
        # self.road_radio.setChecked(True)    
        type_layout.addWidget(self.road_radio)            
        type_layout.addWidget(self.bridge_radio)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Reference layer
        layout.addWidget(QLabel("Reference Layer of 2D design Layer:"))
        self.ref_layer_combo = QComboBox()
        self.ref_layer_combo.setEditable(True)
        self.ref_layer_combo.addItems(["None", "Design_Layer_01", "Design_Layer_02", "Design_Layer_03"])
        layout.addWidget(self.ref_layer_combo)

        # Base lines
        layout.addWidget(QLabel("2D Layer refer to Base lines :"))
        self.base_lines_combo = QComboBox()
        self.base_lines_combo.setEditable(True)
        layout.addWidget(self.base_lines_combo)

        # ------------------------------------------------------------------
        self.road_base_lines  = ["None", "Zero Line", "Surface Line", "Construction Line", "Road Surface Line"]
        self.bridge_base_lines = ["None", "Zero Line", "Projection Line", "Construction Dots", "Deck Line"]
        self.update_base_lines()

        self.road_radio.toggled.connect(self.update_base_lines)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet("background-color:#7B1FA2;color:white;")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("background-color:#B0BEC5;color:#333;")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

    def update_base_lines(self):
        cur = self.base_lines_combo.currentText()
        self.base_lines_combo.clear()
        items = self.road_base_lines if self.road_radio.isChecked() else self.bridge_base_lines
        self.base_lines_combo.addItems(items)
        idx = self.base_lines_combo.findText(cur)
        self.base_lines_combo.setCurrentIndex(idx if idx != -1 else 0)

    # ------------------------------------------------------------------
    # This method is now used by open_construction_layer_dialog()
    def get_data(self):
        return {
            'layer_name'      : self.name_edit.text().strip(),
            'is_road'         : self.road_radio.isChecked(),
            'is_bridge'       : self.bridge_radio.isChecked(),
            'reference_layer' : self.ref_layer_combo.currentText(),
            'base_lines_layer': self.base_lines_combo.currentText()
        }
    

# ===========================================================================================================================
# ** CREATE PROJECT DIALOG - IMPROVED VERSION (Supports File + Folder Selection) **
# ===========================================================================================================================

class CreateProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setFixedWidth(500)
        #self.setFixedSize(600, 600)
        self.setModal(True)

        # EXACT STYLE MATCHING YOUR IMAGE
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #E8DAF8, stop:1 #D7B8F3);
                border: 1px solid #BB86FC;
                border-radius: 12px;
            }
            QLabel {
                color: #4A148C;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }
            QLabel[accessibleName="title"] {
                font-size: 20px;
                font-weight: bold;
                color: #4A148C;
                margin: 10px;
            }
            QLineEdit, QComboBox {
                padding: 10px;
                border: 2px solid #CF9FFF;
                border-radius: 10px;
                background-color: white;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #9C27B0;
            }
            QComboBox::drop-down {
                border: 0px;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);  /* optional: add a purple arrow icon */
                width: 12px;
                height: 12px;
            }
            QTextEdit {
                padding: 12px;
                border: 2px solid #CF9FFF;
                border-radius: 10px;
                background-color: white;
                font-size: 13px;
                color: #555;
            }
            QPushButton {
                padding: 12px 20px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton#okBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #AB47BC, stop:1 #8E24AA);
                color: white;
                border: none;
            }
            QPushButton#okBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #9C27B0, stop:1: #7B1FA2);
            }
            QPushButton#cancelBtn {
                background-color: #E0C3FC;
                color: #4A148C;
                border: 2px solid #CF9FFF;
            }
            QPushButton#cancelBtn:hover {
                background-color: #D8B8F8;
            }
            QPushButton#browseFileBtn {
                background-color: #7C4DFF;
                color: white;
            }
            QPushButton#browseFileBtn:hover {
                background-color: #651FFF;
            }
            QPushButton#browseFolderBtn {
                background-color: #9C27B0;
                color: white;
            }
            QPushButton#browseFolderBtn:hover {
                background-color: #7B1FA2;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(5)

        # Title
        title = QLabel("Create New Project")
        title.setAccessibleName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Project Name
        layout.addWidget(QLabel("Project Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter project name")
        layout.addWidget(self.name_edit)


        # Point Cloud Files Section
        layout.addWidget(QLabel("Link 3D Point Cloud Data:"))

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.browse_file_btn = QPushButton("Choose File(s)")
        self.browse_file_btn.setObjectName("browseFileBtn")
        self.browse_file_btn.clicked.connect(self.browse_files)

        self.browse_folder_btn = QPushButton("Choose Folder")
        self.browse_folder_btn.setObjectName("browseFolderBtn")
        self.browse_folder_btn.clicked.connect(self.browse_folder)

        btn_layout.addWidget(self.browse_file_btn)
        btn_layout.addWidget(self.browse_folder_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # File Display
        self.files_display = QTextEdit()
        self.files_display.setReadOnly(True)
        self.files_display.setFixedHeight(140)
        self.files_display.setPlaceholderText("No files selected yet...")
        layout.addWidget(self.files_display)

        # File counter
        self.file_count_label = QLabel("0 files selected")
        self.file_count_label.setStyleSheet("color: #6A1B9A; font-style: italic;")
        layout.addWidget(self.file_count_label)

        # Project Category
        layout.addWidget(QLabel("Project Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["None", "Design", "Construction", "Measurement", "Other"])
        layout.addWidget(self.category_combo)

        # OK / Cancel Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("okBtn")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

        # Store selected files
        self.selected_files = []

    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Point Cloud Files",
            "",
            "Point Cloud Files (*.las *.laz *.ply *.pts *.xyz *.pcd *.bin);;All Files (*)"
        )
        if files:
            self.selected_files = files
            self.update_file_display()

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing Point Cloud Files")
        if folder:
            supported_exts = {'.las', '.laz', '.ply', '.pts', '.xyz', '.pcd', '.bin'}
            found = []
            for root, _, fs in os.walk(folder):
                for f in fs:
                    if os.path.splitext(f)[1].lower() in supported_exts:
                        found.append(os.path.join(root, f))
            if not found:
                QMessageBox.information(self, "No Files", "No supported point cloud files found.")
                return
            self.selected_files = found
            self.update_file_display()

    def update_file_display(self):
        count = len(self.selected_files)
        self.file_count_label.setText(f"{count} file{'s' if count != 1 else ''} selected")

        if count == 0:
            self.files_display.setPlainText("No files selected yet...")
        elif count <= 12:
            self.files_display.setPlainText("\n".join(os.path.basename(f) for f in self.selected_files))
        else:
            sample = "\n".join(os.path.basename(f) for f in self.selected_files[:10])
            self.files_display.setPlainText(f"{sample}\n... and {count - 10} more files")

    def get_data(self):
        return {
            "project_name": self.name_edit.text().strip(),
            "pointcloud_files": self.selected_files.copy(),
            "category": self.category_combo.currentText(),
            "file_count": len(self.selected_files)
        }


# ===========================================================================================================================
# ** EXISTING WORKSHEET DIALOG - SCANS FOLDERS AND LOADS worksheet_config.txt **
# ===========================================================================================================================
class ExistingWorksheetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open Existing Worksheet")
        self.setModal(True)
        self.resize(700, 550)
        self.selected_worksheet = None

        # Get the base worksheets directory from parent (PointCloudViewer)
        if parent and hasattr(parent, 'WORKSHEETS_BASE_DIR'):
            self.base_dir = parent.WORKSHEETS_BASE_DIR
        else:
            self.base_dir = r"E:\3D_Tool\user\worksheets"  # fallback

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title = QLabel("Select an Existing Worksheet")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #4A148C;
            padding: 10px;
            background-color: #E8EAF6;
            border-radius: 8px;
        """)
        main_layout.addWidget(title)

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid #BA68C8;
                border-radius: 10px;
                background-color: white;
            }
        """)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        scroll_layout.setSpacing(12)
        scroll_layout.setAlignment(Qt.AlignTop)

        # Group box
        self.radio_group_box = QGroupBox("Available Worksheets")
        self.radio_group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #4A148C;
                border: 2px solid #9C27B0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background-color: white;
            }
        """)

        radio_layout = QVBoxLayout(self.radio_group_box)
        radio_layout.setSpacing(10)
        radio_layout.setContentsMargins(10, 10, 10, 10)

        # Button group for mutual exclusivity
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)

        self.worksheets = []
        self.radio_buttons = []

        # === SCAN WORKSHEET FOLDERS ===
        if not os.path.exists(self.base_dir):
            no_dir_label = QLabel(f"Worksheets directory not found:\n{self.base_dir}")
            no_dir_label.setStyleSheet("color: red; font-style: italic;")
            radio_layout.addWidget(no_dir_label)
        else:
            found_any = False
            for folder_name in sorted(os.listdir(self.base_dir)):
                folder_path = os.path.join(self.base_dir, folder_name)
                if not os.path.isdir(folder_path):
                    continue

                config_path = os.path.join(folder_path, "worksheet_config.txt")
                if not os.path.exists(config_path):
                    continue  # Skip if no config file

                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    found_any = True
                    self.worksheets.append(data)

                    name = data.get("worksheet_name", folder_name)
                    proj = data.get("project_name", "No Project")
                    if proj == "None" or not proj:
                        proj = "No Project"

                    date_str = data.get("created_at", "")
                    if date_str:
                        try:
                            # Handle ISO format with or without Z
                            date_str = date_str.replace("Z", "+00:00")
                            date = datetime.fromisoformat(date_str).strftime("%Y-%m-%d %H:%M")
                        except:
                            date = date_str[:19] if len(date_str) >= 19 else date_str
                    else:
                        date = "Unknown"

                    # Create radio button with rich info
                    radio = QRadioButton()
                    label_text = f"<b>{name}</b><br>"
                    label_text += f"<small>Project: <i>{proj}</i> | Created: {date}<br>"
                    label_text += f"Folder: {folder_name}</small>"

                    label = QLabel(label_text)
                    label.setWordWrap(True)
                    label.setStyleSheet("""
                        QLabel {
                            background-color: #F8E8FF;
                            padding: 14px;
                            border-radius: 10px;
                            border: 1px solid #E1BEE7;
                        }
                    """)

                    # Container widget
                    item_widget = QWidget()
                    item_layout = QHBoxLayout(item_widget)
                    item_layout.setContentsMargins(0, 0, 0, 0)
                    item_layout.addWidget(radio)
                    item_layout.addWidget(label, 1)

                    radio_layout.addWidget(item_widget)

                    # Add to button group
                    self.button_group.addButton(radio)
                    self.radio_buttons.append((radio, data))

                except Exception as e:
                    error_item = QLabel(f"⚠ Error loading {folder_name}: {str(e)}")
                    error_item.setStyleSheet("color: orange; font-size: 12px;")
                    radio_layout.addWidget(error_item)

            if not found_any:
                no_ws_label = QLabel("No worksheets found in the directory.")
                no_ws_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
                radio_layout.addWidget(no_ws_label)

        scroll_layout.addWidget(self.radio_group_box)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        open_btn = QPushButton("Open Selected")
        open_btn.setFixedWidth(140)
        open_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #AB47BC, stop:1 #8E24AA);
                color: white;
                border: none;
                padding: 12px;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #9C27B0, stop:1 #7B1FA2);
            }
        """)
        open_btn.clicked.connect(self.open_selected_worksheet)
        btn_layout.addWidget(open_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #E1BEE7, stop:1 #CE93D8);
                color: #333;
                border: none;
                padding: 12px;
                border-radius: 20px;
                font-weight: bold;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        main_layout.addLayout(btn_layout)

    def open_selected_worksheet(self):
        """Handle opening the selected worksheet"""
        selected_button = self.button_group.checkedButton()
        if not selected_button:
            QMessageBox.information(self, "No Selection", "Please select a worksheet to open.")
            return

        for radio, data in self.radio_buttons:
            if radio is selected_button:
                self.selected_worksheet = data
                self.accept()
                return

        QMessageBox.warning(self, "Error", "Could not retrieve selected worksheet data.")




# =================================================================================================================================================================
#                                                                    ** Updated WorksheetNewDialog (Layer Name - No Fallback) **
# =================================================================================================================================================================
class WorksheetNewDialog(QDialog):
    """Multi-page dialog for creating a new worksheet with conditional Baseline Type selection (only for 2D)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Worksheet")
        self.setModal(True)
        self.resize(560, 520)

        self.parent = parent  # Reference to main window

        # ------------------------------------------------------------------
        # Style (consistent with DesignNewDialog)
        # ------------------------------------------------------------------
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #f0e6fa, stop:1 #e6e6fa);
                border-radius: 18px;
            }
            QLabel {
                color: #2d1b3d;
                font-weight: 600;
                font-size: 13px;
            }
            QLineEdit, QComboBox {
                border: 2px solid #BA68C8;
                border-radius: 8px;
                padding: 8px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #8E24AA;
                background-color: #F8E8FF;
            }
            QGroupBox {
                border: 2px solid #9C27B0;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: bold;
                color: #4A148C;
                background-color: rgba(255, 255, 255, 0.4);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 10px;
                background-color: #E1BEE7;
                border-radius: 6px;
            }
            QCheckBox {
                font-weight: 500;
                spacing: 8px;
                font-size: 13px;
            }
            QRadioButton {
                padding: 6px;
                color: #2d1b3d;
                font-weight: normal;
            }
            QPushButton {
                border-radius: 20px;
                padding: 11px;
                font-weight: bold;
                min-width: 110px;
                border: none;
            }
            QPushButton#nextBtn, QPushButton#okBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #AB47BC, stop:1 #8E24AA);
                color: white;
            }
            QPushButton#nextBtn:hover, QPushButton#okBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #9C27B0, stop:1 #7B1FA2);
            }
            QPushButton#backBtn, QPushButton#cancelBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #E1BEE7, stop:1 #CE93D8);
                color: #333;
            }
            QPushButton#backBtn:hover, QPushButton#cancelBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #D1C4E9, stop:1 #BA68C8);
            }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # Stacked pages
        self.page1 = QWidget()
        self.page2 = QWidget()
        self.setup_page1()
        self.setup_page2()

        self.main_layout.addWidget(self.page1)
        self.main_layout.addWidget(self.page2)
        self.page2.setVisible(False)

        # Data storage
        self.reference_type = None

    # ------------------------------------------------------------------
    # Page 1: Basic worksheet info
    # ------------------------------------------------------------------
    def setup_page1(self):
        layout = QVBoxLayout(self.page1)
        layout.setSpacing(15)

        title = QLabel("Create New Worksheet")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 19px; font-weight: bold; color: #4A148C; padding: 8px;")
        layout.addWidget(title)

        form = QVBoxLayout()
        form.setSpacing(12)

        # Worksheet Name
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Worksheet Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter worksheet name")
        row1.addWidget(self.name_edit)
        form.addLayout(row1)

        # Project
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Project Name:"))
        self.project_combo = QComboBox()
        self.project_combo.addItem("None")
        self.load_projects_from_folders()
        self.project_combo.currentTextChanged.connect(self.on_project_changed)
        row2.addWidget(self.project_combo)
        form.addLayout(row2)

        layout.addLayout(form)
        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("nextBtn")
        self.next_btn.clicked.connect(self.go_to_page2)
        btn_layout.addWidget(self.next_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Page 2: Layer & Baseline Configuration
    # ------------------------------------------------------------------
    def setup_page2(self):
        layout = QVBoxLayout(self.page2)
        layout.setSpacing(18)

        title = QLabel("Worksheet Configuration")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 19px; font-weight: bold; color: #4A148C; padding: 8px;")
        layout.addWidget(title)

        # === Enter Layer Name ===
        layer_name_row = QHBoxLayout()
        layer_name_row.addWidget(QLabel("Enter Layer Name:"))
        self.layer_name_edit = QLineEdit()
        self.layer_name_edit.setPlaceholderText("e.g. Base Layer, Design Layer 1")
        layer_name_row.addWidget(self.layer_name_edit)
        layout.addLayout(layer_name_row)

        # === Dimension ===
        dim_group = QGroupBox("Layer Type")
        dim_layout = QVBoxLayout(dim_group)
        self.radio_3d = QRadioButton("3D (Measurement)")
        self.radio_2d = QRadioButton("2D (Design)")
        dim_layout.addWidget(self.radio_3d)
        dim_layout.addWidget(self.radio_2d)
        layout.addWidget(dim_group)

        # === Baseline Type (Road / Bridge / Other) - Only visible for 2D ===
        self.baseline_group = QGroupBox("Baseline Type")
        baseline_layout = QVBoxLayout(self.baseline_group)

        self.cb_road = QCheckBox("Road")
        self.cb_bridge = QCheckBox("Bridge")
        self.cb_other = QCheckBox("Other")

        # Mutually exclusive between Road and Bridge
        def toggle_exclusive(checked_cb):
            if checked_cb.isChecked():
                other = self.cb_bridge if checked_cb == self.cb_road else self.cb_road
                other.blockSignals(True)
                other.setChecked(False)
                other.blockSignals(False)

        self.cb_road.stateChanged.connect(lambda s: toggle_exclusive(self.cb_road) if s else None)
        self.cb_bridge.stateChanged.connect(lambda s: toggle_exclusive(self.cb_bridge) if s else None)

        baseline_layout.addWidget(self.cb_road)
        baseline_layout.addWidget(self.cb_bridge)
        baseline_layout.addWidget(self.cb_other)

        layout.addWidget(self.baseline_group)
        self.baseline_group.setVisible(False)

        # === Point Cloud Selection ===
        pc_group = QGroupBox("Select Point Cloud File (optional)")
        pc_layout = QHBoxLayout(pc_group)
        self.pc_combo = QComboBox()
        self.pc_combo.addItem("No file selected")
        pc_layout.addWidget(QLabel("File:"))
        pc_layout.addWidget(self.pc_combo, 1)
        layout.addWidget(pc_group)

        # Connect dimension change
        self.radio_3d.toggled.connect(self.on_dimension_changed)
        self.radio_2d.toggled.connect(self.on_dimension_changed)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        back_btn = QPushButton("Back")
        back_btn.setObjectName("backBtn")
        back_btn.clicked.connect(self.go_to_page1)
        btn_layout.addWidget(back_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("okBtn")
        ok_btn.clicked.connect(self.final_accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def go_to_page2(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Input Required", "Please enter a worksheet name.")
            return
        self.page1.setVisible(False)
        self.page2.setVisible(True)
        self.on_project_changed()
        self.on_dimension_changed()

    def go_to_page1(self):
        self.page2.setVisible(False)
        self.page1.setVisible(True)

    def on_dimension_changed(self):
        is_2d = self.radio_2d.isChecked()
        self.baseline_group.setVisible(is_2d)

    def on_project_changed(self):
        project_name = self.project_combo.currentText()
        self.pc_combo.clear()
        self.pc_combo.addItem("No file selected")

        if project_name == "None":
            self.pc_combo.setEnabled(False)
            return

        project_folder = os.path.join(r"E:\3D_Tool\projects", project_name)
        config_path = os.path.join(project_folder, "project_config.txt")

        if not os.path.exists(config_path):
            self.pc_combo.addItem("Project config not found")
            self.pc_combo.setEnabled(False)
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            files = data.get("pointcloud_files", [])
            if not files:
                self.pc_combo.addItem("No point cloud files linked")
            else:
                for f in files:
                    self.pc_combo.addItem(os.path.basename(f), f)
                self.pc_combo.setEnabled(True)
        except Exception as e:
            self.pc_combo.addItem(f"Error reading config: {e}")
            self.pc_combo.setEnabled(False)

    def load_projects_from_folders(self):
        import glob
        BASE_DIR = r"E:\3D_Tool\projects"
        if not os.path.exists(BASE_DIR):
            return
        config_files = glob.glob(os.path.join(BASE_DIR, "*", "project_config.txt"))
        for cfg in config_files:
            try:
                with open(cfg, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    name = data.get("project_name", "Unknown")
                    self.project_combo.addItem(name)
            except:
                pass
        self.project_combo.model().sort(0)

    # ------------------------------------------------------------------
    # Final accept
    # ------------------------------------------------------------------
    def final_accept(self):
        worksheet_name = self.name_edit.text().strip()
        if not worksheet_name:
            QMessageBox.warning(self, "Error", "Worksheet name is required.")
            return

        if self.radio_2d.isChecked():
            if self.cb_road.isChecked():
                category = "Road"
            elif self.cb_bridge.isChecked():
                category = "Bridge"
            elif self.cb_other.isChecked():
                category = "Other"
            else:
                category = "None"
        else:
            category = "None"

        self.reference_type = category
        self.accept()

    # ------------------------------------------------------------------
    # get_data() – returns all needed info
    # ------------------------------------------------------------------
    def get_data(self):
        worksheet_name = self.name_edit.text().strip()
        project_name = self.project_combo.currentText() if self.project_combo.currentText() != "None" else ""
        dimension = "3D" if self.radio_3d.isChecked() else "2D"
        worksheet_type = "Measurement" if dimension == "3D" else "Design"

        # Use exactly what user entered — no fallback
        layer_name = self.layer_name_edit.text().strip()

        selected_pc_path = self.pc_combo.currentData()
        point_cloud_file = selected_pc_path if selected_pc_path else None

        return {
            "worksheet_name": worksheet_name,
            "project_name": project_name,
            "worksheet_type": worksheet_type,
            "worksheet_category": self.reference_type or "None",
            "dimension": dimension,
            "initial_layer_name": layer_name,  # Exactly as entered by user
            "reference_type": self.reference_type,
            "reference_line": None,
            "point_cloud_file": point_cloud_file
        }