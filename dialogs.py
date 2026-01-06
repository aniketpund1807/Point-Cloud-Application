import numpy as np
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QGridLayout, QGroupBox, QCheckBox, 
    QTextEdit, QComboBox, QDoubleSpinBox, QRadioButton, QButtonGroup, QWidget, QFileDialog, QInputDialog, QMessageBox,
    QScrollArea, QMenu, QAction, QListWidget, QMainWindow
)

from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper
from vtkmodules.vtkFiltersSources import vtkPlaneSource
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator

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

        layout = QVBoxLayout(self)

        # Point 1 coordinates
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
        self.km1_edit.setPlaceholderText("e.g. 101")
        row1.addWidget(self.km1_edit)
        row1.addWidget(QLabel("Chainage:"))
        self.chain1_edit = QLineEdit(str(chain1) if chain1 is not None else "")
        self.chain1_edit.setPlaceholderText("Optional")
        row1.addWidget(self.chain1_edit)
        layout.addLayout(row1)

        # Point 2 coordinates
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
        self.km2_edit.setPlaceholderText("e.g. 102")
        row2.addWidget(self.km2_edit)
        row2.addWidget(QLabel("Chainage:"))
        self.chain2_edit = QLineEdit(str(chain2) if chain2 is not None else "")
        self.chain2_edit.setPlaceholderText("Optional")
        row2.addWidget(self.chain2_edit)
        layout.addLayout(row2)

        # Interval
        from PyQt5.QtGui import QIntValidator

        # Replace the interval line with this:
        row_int = QHBoxLayout()
        row_int.addWidget(QLabel("Interval (m):"))
        self.interval_edit = QLineEdit(str(int(interval)) if interval is not None else "20")
        self.interval_edit.setValidator(QIntValidator(1, 10000))  # Only positive integers
        self.interval_edit.setPlaceholderText("e.g. 20")
        row_int.addWidget(self.interval_edit)
        layout.addLayout(row_int)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Zero Line")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self.on_save_clicked)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    # -------------------------------------------------
    # Custom save button handler with full validation
    # -------------------------------------------------
    def on_save_clicked(self):
        if self.validate_all_inputs():
            self.accept()  # Only accept if everything is valid

    # -------------------------------------------------
    # Full input validation
    # -------------------------------------------------
    def validate_all_inputs(self):
        errors = []

        # Validate coordinates (must be valid floats and not empty)
        coord_fields = [
            ("Point 1 X", self.x1_edit),
            ("Point 1 Y", self.y1_edit),
            ("Point 1 Z", self.z1_edit),
            ("Point 2 X", self.x2_edit),
            ("Point 2 Y", self.y2_edit),
            ("Point 2 Z", self.z2_edit),
        ]

        for label, edit in coord_fields:
            text = edit.text().strip()
            if not text:
                errors.append(f"{label} cannot be empty.")
                continue
            try:
                float(text)
            except ValueError:
                errors.append(f"{label} must be a valid number (e.g., 387211.438).")

        # Validate KM fields (optional, but must be integer if filled)
        for label, edit in [("Point 1 KM", self.km1_edit), ("Point 2 KM", self.km2_edit)]:
            text = edit.text().strip()
            if text:
                if not text.isdigit():
                    errors.append(f"{label} must be a whole number (e.g., 101).")

        # Validate interval
        interval_text = self.interval_edit.text().strip()
        if not interval_text:
            errors.append("Interval cannot be empty.")
        else:
            try:
                interval_val = float(interval_text)
                if interval_val <= 0:
                    errors.append("Interval must be greater than 0.")
            except ValueError:
                errors.append("Interval must be a valid number (e.g., 20 or 20.5).")

        if errors:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please correct the following errors:\n\n" + "\n".join(f"• {e}" for e in errors)
            )
            return False

        return True

    # -------------------------------------------------
    # Safe extraction of coordinates
    # -------------------------------------------------
    def get_points(self):
        """Returns (p1, p2) as numpy arrays. Guaranteed valid due to validation."""
        try:
            p1 = np.array([
                float(self.x1_edit.text().strip()),
                float(self.y1_edit.text().strip()),
                float(self.z1_edit.text().strip())
            ])
            p2 = np.array([
                float(self.x2_edit.text().strip()),
                float(self.y2_edit.text().strip()),
                float(self.z2_edit.text().strip())
            ])
            return p1, p2
        except Exception:
            return None, None  # Should never reach here due to validation

    # -------------------------------------------------
    # Optional: Helper to get KM and interval safely
    # -------------------------------------------------
    def get_configuration(self):
        """Returns full config including KM and interval"""
        km1 = self.km1_edit.text().strip()
        km2 = self.km2_edit.text().strip()
        interval = float(self.interval_edit.text().strip())
        self.zero_interval = int(self.interval_edit.text().strip() or 20)

        return {
            'km1': int(km1) if km1 else None,
            'km2': int(km2) if km2 else None,
            'interval': interval
        }
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
# ** MATERIAL LINE DIALOG ** (FINAL CORRECTED VERSION – ONLY SHOWS SELECTED BASELINES)
# ===========================================================================================================================
class MaterialLineDialog(QDialog):
    def __init__(self, material_data=None, construction_layer_path=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Material Line")
        self.setModal(True)
        self.setFixedSize(500, 500)

        self.construction_layer_path = construction_layer_path
        self.parent_app = parent
        self.material_data = material_data if material_data else {
            'name': '',
            'description': '',
            'material_type': '',
            'ref_layer': 'None'  # Selected baseline name
        }

        self.setup_ui()
        self.load_material_data()
        self.load_available_baselines()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Title
        title_label = QLabel("Material Line Configuration")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000; padding-bottom: 15px;")
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

        # Material Type
        type_layout = QHBoxLayout()
        type_label = QLabel("Material Type:")
        type_label.setFixedWidth(150)
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("Enter material type (e.g., GSB, WMM)")
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_input, 1)
        layout.addLayout(type_layout)

        layout.addSpacing(20)

        # Reference Baseline Section
        ref_label = QLabel("Reference Baseline")
        ref_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(ref_label)

        ref_layer_layout = QHBoxLayout()
        ref_layer_label = QLabel("Select Reference Baseline:")
        ref_layer_label.setFixedWidth(150)
        self.ref_layer_combo = QComboBox()
        self.ref_layer_combo.addItem("None")
        ref_layer_layout.addWidget(ref_layer_label)
        ref_layer_layout.addWidget(self.ref_layer_combo, 1)
        layout.addLayout(ref_layer_layout)

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
        save_button.clicked.connect(self.on_save)
        layout.addWidget(save_button, alignment=Qt.AlignCenter)

    def on_save(self):
        material_name = self.name_input.text().strip()
        if not material_name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid material line name.")
            return

        selected_baseline = self.ref_layer_combo.currentText()
        if selected_baseline == "None":
            QMessageBox.warning(self, "No Baseline", "Please select a reference baseline.")
            return

        # No folder creation, no file writing — just accept the dialog
        QMessageBox.information(self, "Success", f"Material line '{material_name}' configured successfully!")
        self.accept()  # This will make dialog.exec_() return QDialog.Accepted

    def load_available_baselines(self):
        """Load only the selected baselines from Construction_Layer_config.txt"""
        self.ref_layer_combo.clear()
        self.ref_layer_combo.addItem("None")

        if not self.construction_layer_path or not os.path.exists(self.construction_layer_path):
            self.ref_layer_combo.addItem("Construction layer path not available")
            return

        config_path = os.path.join(self.construction_layer_path, "Construction_Layer_config.txt")
        if not os.path.exists(config_path):
            self.ref_layer_combo.addItem("Construction_Layer_config.txt not found")
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            selected_baselines = config.get("base_lines_reference", [])
            reference_layer_2d = config.get("reference_layer_2d")

            if not selected_baselines:
                self.ref_layer_combo.addItem("No baselines selected in construction layer")
                return

            if not reference_layer_2d:
                self.ref_layer_combo.addItem("No reference design layer defined")
                return

            worksheet_root = os.path.abspath(os.path.join(self.construction_layer_path, "..", ".."))
            designs_folder = os.path.join(worksheet_root, "designs")
            design_layer_path = os.path.join(designs_folder, reference_layer_2d)

            if not os.path.exists(design_layer_path):
                self.ref_layer_combo.addItem(f"Design layer folder not found: {reference_layer_2d}")
                return

            found_count = 0
            for baseline_filename in selected_baselines:
                file_path = os.path.join(design_layer_path, baseline_filename)
                if os.path.exists(file_path):
                    display_name = os.path.basename(baseline_filename).replace("_baseline.json", "")
                    self.ref_layer_combo.addItem(display_name)
                    found_count += 1
                else:
                    self.ref_layer_combo.addItem(f"[Missing] {os.path.basename(baseline_filename)}")

            if found_count == 0:
                self.ref_layer_combo.addItem("Selected baselines not found in design layer")

        except Exception as e:
            self.ref_layer_combo.addItem(f"Error loading config: {str(e)}")

    def load_material_data(self):
        if not self.material_data:
            return
        self.name_input.setText(self.material_data.get('name', ''))
        self.type_input.setText(self.material_data.get('material_type', ''))
        ref_layer = self.material_data.get('ref_layer', 'None')
        index = self.ref_layer_combo.findText(ref_layer)
        if index >= 0:
            self.ref_layer_combo.setCurrentIndex(index)

    def get_material_data(self):
        return {
            'name': self.name_input.text().strip(),
            'material_type': self.type_input.text().strip(),
            'ref_layer': self.ref_layer_combo.currentText() if self.ref_layer_combo.currentText() != "None" else ''
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
# DESIGN NEW LAYER DIALOG – With Dynamic Dropdown Based on Road/Bridge Selection + NO OVERWRITE
# ===========================================================================================================================
class DesignNewDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Design Layer")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.parent = parent  # To access base directories and current worksheet
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
        self.radio_3d.setChecked(True)
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
        ok_btn.clicked.connect(self.validate_and_accept)
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

    def validate_and_accept(self):
        layer_name = self.name_edit.text().strip()
        if not layer_name:
            QMessageBox.warning(self, "Input Required", "Layer name is required!")
            return

        # === Check if layer already exists in current worksheet ===
        if not hasattr(self.parent, 'current_worksheet_name') or not self.parent.current_worksheet_name:
            QMessageBox.warning(self, "No Worksheet", "No active worksheet found.")
            return

        base_designs_path = os.path.join(self.parent.WORKSHEETS_BASE_DIR, self.parent.current_worksheet_name, "designs")
        layer_folder = os.path.join(base_designs_path, layer_name)

        if os.path.exists(layer_folder):
            QMessageBox.warning(self, "Name Exists",
                                "A design layer with this name already exists.\n"
                                "Please enter a different name.")
            return  # Do NOT accept — user must change name

        # If all good, accept dialog
        self.accept()

    def get_configuration(self):
        layer_name = self.name_edit.text().strip()
        reference_type = None
        reference_line = None
        if self.radio_3d.isChecked():
            if self.cb_road.isChecked():
                reference_type = "Road"
                reference_line = self.combo_reference.currentText()
            elif self.cb_bridge.isChecked():
                reference_type = "Bridge"
                reference_line = self.combo_reference.currentText()
        else:
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
# FINAL UPDATED: Construction Layer Creation Dialog (Multiple Baseline Selection + Preview)
# ===========================================================================================================================
class ConstructionNewDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Construction Layer")
        self.setFixedSize(380, 500)
        self.parent = parent
       
        self.current_worksheet_path = None

        # Initialize preview-related attributes EARLY to avoid AttributeError
        self.preview_artists = []  # Temporary artists for live preview
        self.selected_baseline_data = []  # List of (data_dict, color, baseline_key, filename)
        self.preview_colors = ["gray", "blue", "green", "orange", "purple", "brown", "pink", "olive", "cyan"]

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
            QListWidget {
                border: 2px solid #BBB;
                border-radius: 6px;
                padding: 5px;
                font-size: 13px;
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
        self.road_radio.setChecked(True)
        type_layout.addWidget(self.road_radio)
        type_layout.addWidget(self.bridge_radio)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Reference Layer Dropdown
        layout.addWidget(QLabel("Reference Layer of 2D design Layer:"))
        self.ref_layer_combo = QComboBox()
        self.ref_layer_combo.setEditable(False)
        layout.addWidget(self.ref_layer_combo)
        
        # Base Lines - Multi-Select List
        layout.addWidget(QLabel("2D Layer refer to Base lines (select one or more):"))
        self.base_lines_list = QListWidget()
        self.base_lines_list.setSelectionMode(QListWidget.MultiSelection)
        self.base_lines_list.setMinimumHeight(120)
        layout.addWidget(self.base_lines_list)
        
        # Initial load
        self.load_design_layers()
        
        # Connect signals
        self.ref_layer_combo.currentIndexChanged.connect(self.on_reference_layer_changed)
        self.base_lines_list.itemSelectionChanged.connect(self.on_baseline_selection_changed)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet("background-color:#7B1FA2;color:white;")
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("background-color:#B0BEC5;color:#333;")
        self.cancel_button.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

    def set_current_worksheet_path(self, path):
        self.current_worksheet_path = path
        self.load_design_layers()

    def get_designs_path(self):
        if not self.current_worksheet_path:
            return None
        return os.path.join(self.current_worksheet_path, "designs")
    
    def load_design_layers(self):
        self.ref_layer_combo.clear()
        self.ref_layer_combo.addItem("None")
        designs_path = self.get_designs_path()
        if not designs_path or not os.path.exists(designs_path):
            self.ref_layer_combo.addItem("(No designs folder)")
            self.on_reference_layer_changed()
            return
        try:
            folders = [name for name in os.listdir(designs_path)
                       if os.path.isdir(os.path.join(designs_path, name))]
            folders.sort()
            if folders:
                self.ref_layer_combo.addItems(folders)
            else:
                self.ref_layer_combo.addItem("(No design layers found)")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load design layers:\n{e}")
        self.on_reference_layer_changed()
    
    def get_json_baselines_in_layer(self, design_layer_name):
        if not design_layer_name or design_layer_name in ("None", "(No designs folder)", "(No design layers found)"):
            return []
        designs_path = self.get_designs_path()
        if not designs_path:
            return []
        layer_path = os.path.join(designs_path, design_layer_name)
        if not os.path.exists(layer_path):
            return []
        try:
            json_files = [
                name for name in os.listdir(layer_path)
                if name.lower().endswith('.json') and os.path.isfile(os.path.join(layer_path, name))
            ]
            json_files.sort()
            return json_files
        except Exception:
            return []

    def on_reference_layer_changed(self):
        ref_layer = self.ref_layer_combo.currentText()
        json_baselines = self.get_json_baselines_in_layer(ref_layer)
        
        self.base_lines_list.clear()
        if json_baselines:
            self.base_lines_list.addItems(json_baselines)
        else:
            self.base_lines_list.addItem("(No baseline files found)")

        # Clear any existing preview
        self.clear_preview_lines()
        self.selected_baseline_data.clear()

    def clear_preview_lines(self):
        for artist in self.preview_artists:
            try:
                artist.remove()
            except:
                pass
        self.preview_artists.clear()
        if hasattr(self.parent, 'canvas'):
            self.parent.canvas.draw_idle()

    def on_baseline_selection_changed(self):
        self.clear_preview_lines()
        self.selected_baseline_data.clear()

        selected_items = self.base_lines_list.selectedItems()
        if not selected_items:
            self.parent.message_text.append("No baselines selected for preview.")
            return

        ref_layer = self.ref_layer_combo.currentText()
        if ref_layer in ("None", "(No designs folder)", "(No design layers found)"):
            return

        designs_path = self.get_designs_path()
        if not designs_path:
            return

        color_idx = 0
        for item in selected_items:
            json_file = item.text()
            if json_file.startswith("("):  # Skip placeholder items
                continue

            json_path = os.path.join(designs_path, ref_layer, json_file)
            if not os.path.exists(json_path):
                continue

            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                color = data.get("color", self.preview_colors[color_idx % len(self.preview_colors)])
                baseline_key = data.get("baseline_key", json_file.replace("_baseline.json", ""))
                baseline_type = data.get("baseline_type", "Baseline")

                # Store for later use (on OK)
                self.selected_baseline_data.append((data, color, baseline_key, json_file))

                # Plot dotted preview
                all_x = []
                all_y = []
                for poly in data.get("polylines", []):
                    poly_x = [pt["chainage_m"] for pt in poly.get("points", [])]
                    poly_y = [pt["relative_elevation_m"] for pt in poly.get("points", [])]
                    if poly_x:
                        all_x.extend(poly_x)
                        all_y.extend(poly_y)

                if all_x:
                    artist, = self.parent.ax.plot(
                        all_x, all_y,
                        color=color,
                        linestyle=':',
                        linewidth=3,
                        alpha=0.8,
                        label=f"Ref: {baseline_type} ({json_file})",
                        zorder=5
                    )
                    self.preview_artists.append(artist)

                color_idx += 1

            except Exception as e:
                QMessageBox.warning(self, "Load Error", f"Failed to load {json_file}:\n{str(e)}")

        self.parent.canvas.draw_idle()
        self.parent.message_text.append(f"Preview: {len(selected_items)} baseline(s) selected (dotted lines)")

    def validate_and_accept(self):
        layer_name = self.name_edit.text().strip()
        if not layer_name:
            QMessageBox.warning(self, "Input Required", "Please enter a layer name.")
            return

        construction_base = os.path.join(r"E:\3D_Tool\user\worksheets", self.parent.current_worksheet_name, "construction")
        if os.path.exists(os.path.join(construction_base, layer_name)):
            QMessageBox.warning(self, "Name Exists",
                                "A construction layer with this name already exists.\nPlease enter another name.")
            return

        # Clear standard baseline types
        baseline_types_to_clear = [
            'surface', 'construction', 'road_surface',
            'deck_line', 'projection_line', 'material'
        ]
        for ltype in baseline_types_to_clear:
            if ltype in self.parent.line_types:
                for artist in self.parent.line_types[ltype]['artists']:
                    try:
                        artist.remove()
                    except:
                        pass
                self.parent.line_types[ltype]['artists'].clear()
                self.parent.line_types[ltype]['polylines'].clear()

        # Re-plot ALL selected reference baselines permanently (dotted)
        self.clear_preview_lines()  # Remove temporary ones
        for data, color, baseline_key, filename in self.selected_baseline_data:
            if baseline_key not in self.parent.line_types:
                self.parent.line_types[baseline_key] = {'color': color, 'polylines': [], 'artists': []}

            # Clear any old
            for artist in self.parent.line_types[baseline_key]['artists']:
                try:
                    artist.remove()
                except:
                    pass
            self.parent.line_types[baseline_key]['artists'].clear()
            self.parent.line_types[baseline_key]['polylines'].clear()

            all_x = []
            all_y = []
            for poly in data.get("polylines", []):
                poly_x = [pt["chainage_m"] for pt in poly.get("points", [])]
                poly_y = [pt["relative_elevation_m"] for pt in poly.get("points", [])]
                if poly_x:
                    all_x.extend(poly_x)
                    all_y.extend(poly_y)
                    self.parent.line_types[baseline_key]['polylines'].append(list(zip(poly_x, poly_y)))

            if all_x:
                ref_artist, = self.parent.ax.plot(
                    all_x, all_y,
                    color=color,
                    linestyle=':',
                    linewidth=3,
                    alpha=0.8,
                    zorder=5
                )
                self.parent.line_types[baseline_key]['artists'].append(ref_artist)

        self.parent.canvas.draw_idle()

        # Create 3D base plane from FIRST selected baseline (if any)
        if self.selected_baseline_data:
            first_data = self.selected_baseline_data[0][0]
            width = float(first_data.get("width_meters", 10.0))
            half_width = width / 2.0

            if not hasattr(self.parent, 'construction_base_actors'):
                self.parent.construction_base_actors = []
            for actor in self.parent.construction_base_actors:
                self.parent.renderer.RemoveActor(actor)
            self.parent.construction_base_actors.clear()

            zero_start = np.array(first_data["zero_line_start"])
            zero_end = np.array(first_data["zero_line_end"])
            zero_dir_vec = zero_end - zero_start
            zero_length = np.linalg.norm(zero_dir_vec)
            ref_z = float(first_data.get("zero_start_elevation", 0.0))

            ltype = self.selected_baseline_data[0][2]
            plane_colors = {
                'surface': (0.0, 0.8, 0.0, 0.4),
                'construction': (1.0, 0.0, 0.0, 0.4),
                'road_surface': (0.0, 0.6, 1.0, 0.45),
                'deck_line': (1.0, 0.5, 0.0, 0.4),
                'projection_line': (0.5, 0.0, 0.5, 0.4),
                'material': (1.0, 1.0, 0.0, 0.4),
            }
            rgba = plane_colors.get(ltype, (0.5, 0.5, 0.5, 0.4))
            color_rgb = rgba[:3]
            opacity = rgba[3]

            for poly in first_data.get("polylines", []):
                points_2d = poly.get("points", [])
                if len(points_2d) < 2:
                    continue

                for i in range(len(points_2d) - 1):
                    pt1 = points_2d[i]
                    pt2 = points_2d[i + 1]

                    dist1 = pt1["chainage_m"]
                    dist2 = pt2["chainage_m"]
                    rel_z1 = pt1["relative_elevation_m"]
                    rel_z2 = pt2["relative_elevation_m"]

                    pos1 = zero_start + (dist1 / zero_length) * zero_dir_vec
                    pos2 = zero_start + (dist2 / zero_length) * zero_dir_vec

                    center1 = np.array([pos1[0], pos1[1], ref_z + rel_z1])
                    center2 = np.array([pos2[0], pos2[1], ref_z + rel_z2])

                    seg_dir = center2 - center1
                    seg_len = np.linalg.norm(seg_dir)
                    if seg_len < 1e-6:
                        continue
                    seg_unit = seg_dir / seg_len

                    horiz = np.array([seg_unit[0], seg_unit[1], 0.0])
                    hlen = np.linalg.norm(horiz)
                    if hlen < 1e-6:
                        zero_unit = zero_dir_vec / zero_length
                        perp = np.array([-zero_unit[1], zero_unit[0], 0.0])
                    else:
                        horiz /= hlen
                        perp = np.array([-horiz[1], horiz[0], 0.0])

                    perp_len = np.linalg.norm(perp)
                    if perp_len > 0:
                        perp /= perp_len

                    c1 = center1 + perp * half_width
                    c2 = center1 - perp * half_width
                    c3 = center2 - perp * half_width
                    c4 = center2 + perp * half_width

                    plane = vtkPlaneSource()
                    plane.SetOrigin(c1[0], c1[1], c1[2])
                    plane.SetPoint1(c4[0], c4[1], c4[2])
                    plane.SetPoint2(c2[0], c2[1], c2[2])
                    plane.SetXResolution(12)
                    plane.SetYResolution(2)
                    plane.Update()

                    mapper = vtkPolyDataMapper()
                    mapper.SetInputConnection(plane.GetOutputPort())

                    actor = vtkActor()
                    actor.SetMapper(mapper)
                    actor.GetProperty().SetColor(*color_rgb)
                    actor.GetProperty().SetOpacity(opacity)
                    actor.GetProperty().EdgeVisibilityOn()
                    actor.GetProperty().SetEdgeColor(*color_rgb)
                    actor.GetProperty().SetLineWidth(1.5)

                    self.parent.renderer.AddActor(actor)
                    self.parent.construction_base_actors.append(actor)

            self.parent.vtk_widget.GetRenderWindow().Render()
            self.parent.message_text.append(f"Base plane created from first selected baseline (width: {width:.2f}m)")

        self.accept()

    def get_data(self):
        ref_layer = self.ref_layer_combo.currentText()
        selected_baselines = [
            item.text() for item in self.base_lines_list.selectedItems()
            if not item.text().startswith("(")
        ]
        
        return {
            'layer_name': self.name_edit.text().strip(),
            'is_road': self.road_radio.isChecked(),
            'is_bridge': self.bridge_radio.isChecked(),
            'reference_layer': None if ref_layer in ("None", "(No designs folder)", "(No design layers found)") else ref_layer,
            'base_lines_layer': selected_baselines  # List of selected JSON files
        }

# ===========================================================================================================================
# ** CREATE PROJECT DIALOG - IMPROVED VERSION (Supports File + Folder Selection) **
# ===========================================================================================================================

class CreateProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setFixedWidth(500)
        self.setModal(True)
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
                image: url(down_arrow.png);
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
                                          stop:0 #9C27B0, stop:1 #7B1FA2);
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
        ok_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
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

    def validate_and_accept(self):
        project_name = self.name_edit.text().strip()
        if not project_name:
            QMessageBox.warning(self, "Input Required", "Please enter a project name.")
            return

        projects_base = r"E:\3D_Tool\projects"
        project_folder = os.path.join(projects_base, project_name)
        if os.path.exists(project_folder):
            QMessageBox.warning(self, "Name Exists", "A project with this name already exists.\nPlease enter another name.")
            return

        self.accept()

    def get_data(self):
        return {
            "project_name": self.name_edit.text().strip(),
            "pointcloud_files": self.selected_files.copy(),
            "category": self.category_combo.currentText(),
            "file_count": len(self.selected_files)
        }


# ===========================================================================================================================
# ** EXISTING WORKSHEET DIALOG - MULTI-PAGE VERSION **
# ===========================================================================================================================
class ExistingWorksheetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open Existing Worksheet")
        self.setModal(True)
        self.resize(800, 600)

        self.parent = parent  # PointCloudViewer instance
        if parent and hasattr(parent, 'WORKSHEETS_BASE_DIR'):
            self.base_dir = parent.WORKSHEETS_BASE_DIR
        else:
            self.base_dir = r"E:\3D_Tool\user\worksheets"

        # Final selected data
        self.selected_worksheet_data = None
        self.selected_worksheet_folder = None
        self.selected_subfolder_type = None   # "designs", "measurements", "construction"
        self.selected_layer_name = None

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Dynamic title
        self.title_label = QLabel("Select an Existing Worksheet")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 20px; font-weight: bold; color: #4A148C;
            padding: 10px; background-color: #E8EAF6; border-radius: 8px;
        """)
        main_layout.addWidget(self.title_label)

        # Pages
        self.page1 = self.create_page1()
        self.page2 = self.create_page2()
        self.page3 = self.create_page3()

        main_layout.addWidget(self.page1)
        main_layout.addWidget(self.page2)
        main_layout.addWidget(self.page3)

        self.page2.hide()
        self.page3.hide()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.back_btn = QPushButton("Back")
        self.back_btn.setFixedWidth(100)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.hide()

        self.next_btn = QPushButton("Next")
        self.next_btn.setFixedWidth(120)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #AB47BC, stop:1 #8E24AA);
                color: white; border: none; padding: 12px;
                border-radius: 20px; font-weight: bold;
            }
        """)
        self.next_btn.clicked.connect(self.go_next)

        self.open_btn = QPushButton("Open Selected")
        self.open_btn.setFixedWidth(160)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #AB47BC, stop:1 #8E24AA);
                color: white; border: none; padding: 12px;
                border-radius: 20px; font-weight: bold;
            }
        """)
        self.open_btn.clicked.connect(self.final_open)
        self.open_btn.hide()  # Only shown on page 3

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.back_btn)
        btn_layout.addWidget(self.next_btn)
        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(cancel_btn)

        main_layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Page 1: List of worksheets
    # ------------------------------------------------------------------
    def create_page1(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 2px solid #BA68C8; border-radius: 10px; background:white; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignTop)
        content_layout.setSpacing(12)

        self.ws_radio_group = QButtonGroup()
        self.ws_radio_group.setExclusive(True)
        self.ws_items = []  # (radio, data, folder_name, item_widget)

        if not os.path.exists(self.base_dir):
            lbl = QLabel(f"Directory not found:\n{self.base_dir}")
            lbl.setStyleSheet("color:red;")
            content_layout.addWidget(lbl)
        else:
            found = False
            for folder_name in sorted(os.listdir(self.base_dir)):
                folder_path = os.path.join(self.base_dir, folder_name)
                if not os.path.isdir(folder_path):
                    continue
                config_path = os.path.join(folder_path, "worksheet_config.txt")
                if not os.path.exists(config_path):
                    continue
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    found = True

                    name = data.get("worksheet_name", folder_name)
                    proj = data.get("project_name", "None")
                    if proj in ("None", ""):
                        proj = "No Project"
                    date_str = data.get("created_at", "")
                    if date_str:
                        try:
                            date_str = date_str.replace("Z", "+00:00")
                            date = datetime.fromisoformat(date_str).strftime("%Y-%m-%d %H:%M")
                        except:
                            date = date_str[:19] if len(date_str) >= 19 else date_str
                    else:
                        date = "Unknown"

                    radio = QRadioButton()
                    text = f"<b>{name}</b><br>"
                    text += f"<small>Project: <i>{proj}</i> | Created: {date}<br>Folder: {folder_name}</small>"
                    label = QLabel(text)
                    label.setWordWrap(True)
                    label.setStyleSheet("""
                        QLabel { background:#F8E8FF; padding:14px; border-radius:10px;
                                 border:1px solid #E1BEE7; }
                    """)

                    item_widget = QWidget()
                    item_layout = QHBoxLayout(item_widget)
                    item_layout.setContentsMargins(0,0,0,0)
                    item_layout.addWidget(radio)
                    item_layout.addWidget(label, 1)

                    content_layout.addWidget(item_widget)
                    self.ws_radio_group.addButton(radio)
                    self.ws_items.append((radio, data, folder_name, item_widget))
                except Exception as e:
                    err_lbl = QLabel(f"Warning: Error loading {folder_name}: {e}")
                    err_lbl.setStyleSheet("color:orange;")
                    content_layout.addWidget(err_lbl)

            if not found:
                content_layout.addWidget(QLabel("No worksheets found in the directory."))

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return widget

    # ------------------------------------------------------------------
    # Page 2: Actual existing subfolders
    # ------------------------------------------------------------------
    def create_page2(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.subfolder_list = QListWidget()
        self.subfolder_list.setStyleSheet("""
            QListWidget::item { padding: 12px; border-bottom: 1px solid #E0E0E0; }
            QListWidget::item:selected { background: #BBDEFB; color: black; }
        """)
        layout.addWidget(QLabel("Select a section folder:"))
        layout.addWidget(self.subfolder_list)
        return widget

    # ------------------------------------------------------------------
    # Page 3: Layer folders inside selected subfolder
    # ------------------------------------------------------------------
    def create_page3(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.layer_list = QListWidget()
        self.layer_list.setStyleSheet("""
            QListWidget::item { padding: 14px; border-bottom: 1px solid #E0E0E0; font-size: 14px; }
            QListWidget::item:selected { background: #BBDEFB; color: black; }
        """)
        self.layer_list.itemDoubleClicked.connect(self.final_open)  # Double-click to open
        layout.addWidget(QLabel("Select a layer folder:"))
        layout.addWidget(self.layer_list)
        return widget

    # ------------------------------------------------------------------
    # Navigation: Next button logic
    # ------------------------------------------------------------------
    def go_next(self):
        if self.page1.isVisible():
            # From Page 1 → Page 2
            selected_radio = self.ws_radio_group.checkedButton()
            if not selected_radio:
                QMessageBox.information(self, "No Selection", "Please select a worksheet.")
                return

            for radio, data, folder_name, _ in self.ws_items:
                if radio is selected_radio:
                    self.selected_worksheet_data = data
                    self.selected_worksheet_folder = os.path.join(self.base_dir, folder_name)
                    worksheet_name = data.get("worksheet_name", folder_name)

                    # Find actual subfolders that exist
                    possible_subfolders = ["designs", "measurements", "construction"]
                    existing = []
                    for sf in possible_subfolders:
                        path = os.path.join(self.selected_worksheet_folder, sf)
                        if os.path.isdir(path):
                            existing.append(sf)

                    self.subfolder_list.clear()
                    if existing:
                        for sf in existing:
                            self.subfolder_list.addItem(sf)
                    else:
                        self.subfolder_list.addItem("(No sections found)")

                    self.page1.hide()
                    self.page2.show()
                    self.back_btn.show()
                    self.next_btn.show()
                    self.open_btn.hide()
                    self.title_label.setText(f"{worksheet_name} → Select Section")
                    return

        elif self.page2.isVisible():
            # From Page 2 → Page 3
            item = self.subfolder_list.currentItem()
            if not item or item.text().startswith("("):
                QMessageBox.information(self, "No Selection", "Please select a valid section folder.")
                return

            self.selected_subfolder_type = item.text()
            sub_path = os.path.join(self.selected_worksheet_folder, self.selected_subfolder_type)

            self.layer_list.clear()
            try:
                layers = [d for d in os.listdir(sub_path)
                          if os.path.isdir(os.path.join(sub_path, d))]
                layers.sort()
                if layers:
                    for layer in layers:
                        self.layer_list.addItem(layer)
                else:
                    self.layer_list.addItem("(No layers in this section)")
            except Exception as e:
                self.layer_list.addItem(f"Error reading folder: {e}")

            self.page2.hide()
            self.page3.show()
            self.next_btn.hide()
            self.open_btn.show()
            self.title_label.setText(f"Select Layer in '{self.selected_subfolder_type}'")

    # ------------------------------------------------------------------
    # Back button
    # ------------------------------------------------------------------
    def go_back(self):
        if self.page3.isVisible():
            self.page3.hide()
            self.page2.show()
            self.next_btn.show()
            self.open_btn.hide()
            self.title_label.setText(f"{self.selected_worksheet_data.get('worksheet_name', '')} → Select Section")
        elif self.page2.isVisible():
            self.page2.hide()
            self.page1.show()
            self.back_btn.hide()
            self.next_btn.show()
            self.open_btn.hide()
            self.title_label.setText("Select an Existing Worksheet")

    # ------------------------------------------------------------------
    # Final open - THIS IS WHERE WE SAVE THE selected_config.txt
    # ------------------------------------------------------------------
    def final_open(self):
        if not self.page3.isVisible():
            self.go_next()
            return

        item = self.layer_list.currentItem()
        if not item or item.text().startswith("("):
            QMessageBox.information(self, "No Layer", "Please select a valid layer folder.")
            return

        self.selected_layer_name = item.text()

        # Save selected config in worksheet root folder (overwrites existing)
        config_data = {
            "worksheet": self.selected_worksheet_data.get("worksheet_name",
                                                        os.path.basename(self.selected_worksheet_folder)),
            "folder": self.selected_subfolder_type,
            "layer": self.selected_layer_name,
            "last_selected": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        config_path = os.path.join(self.selected_worksheet_folder, "selected_config.txt")

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
            print(f"Updated {config_path}")
        except Exception as e:
            print(f"Failed to save {config_path}: {e}")

        self.accept()

    # ------------------------------------------------------------------
    # Return selected data to main window
    # ------------------------------------------------------------------
    def get_selected_data(self):
        if not all([self.selected_worksheet_data, self.selected_subfolder_type, self.selected_layer_name]):
            return None

        full_path = os.path.join(
            self.selected_worksheet_folder,
            self.selected_subfolder_type,
            self.selected_layer_name
        )

        return {
            "worksheet_data": self.selected_worksheet_data,
            "worksheet_name": self.selected_worksheet_data.get("worksheet_name"),
            "subfolder_type": self.selected_subfolder_type,
            "layer_name": self.selected_layer_name,
            "full_layer_path": full_path
        }


# =================================================================================================================================================================
#                                                   ** Updated WorksheetNewDialog (Layer Name - No Fallback) **
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

        worksheets_base = r"E:\3D_Tool\user\worksheets"
        worksheet_folder = os.path.join(worksheets_base, worksheet_name)
        if os.path.exists(worksheet_folder):
            QMessageBox.warning(self, "Name Exists", "A worksheet with this name already exists.\nPlease enter another name.")
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
    


# ===========================================================================================================================
# ** ROAD PLANE WIDTH DIALOG **  For the road baseline map on 3D Point Cloud Data
# ===========================================================================================================================

class RoadPlaneWidthDialog(QDialog):
    def __init__(self, current_width=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Road Plane Width")
        self.setModal(True)
        self.setFixedSize(400, 180)

        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #f0e6fa, stop:1 #e6e6fa);
                border-radius: 15px;
            }
            QLabel { 
                color: #2d1b3d; 
                font-weight: bold; 
                font-size: 14px; 
            }
            QLineEdit {
                border: 2px solid #BA68C8;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #9C27B0;
            }
            QLineEdit::placeholder {
                color: #999;
            }
            QPushButton {
                border-radius: 20px;
                padding: 10px;
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
                                          stop:0 #CE93D8, stop:1 #BA68C8);
            }
        """)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Dynamic title label
        self.title_label = QLabel("Enter Road Plane Width (meters)")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Width input - QLineEdit with strict float validation
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("e.g. 20.0")
        self.width_input.setAlignment(Qt.AlignCenter)

        # Restrict input to valid positive float numbers (0.1 to 1000.0, up to 2 decimals)
        validator = QDoubleValidator(0.1, 1000.0, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.width_input.setValidator(validator)

        # Pre-fill if a valid current width is provided
        if current_width is not None and current_width > 0:
            self.width_input.setText(f"{float(current_width):.2f}")

        layout.addWidget(self.width_input)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("okBtn")
        ok_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def get_width(self):
        """
        Returns the entered width as a float.
        Thanks to QDoubleValidator, input is guaranteed to be valid float > 0
        if the field is not empty.
        """
        text = self.width_input.text().strip()
        if not text:
            return None
        try:
            value = float(text)
            return value if value > 0 else None
        except ValueError:
            return None  # This should never happen due to validator


# =======================================================================================================================================
# ADD THIS NEW DIALOG CLASS TO dialogs.py (or inline if preferred)
# =======================================================================================================================================
class MaterialSegmentDialog(QDialog):
    def __init__(self, from_chainage=None, to_chainage=None, material_thickness=None, width=None, after_rolling=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Material Segment Configuration")
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

        layout = QVBoxLayout(self)

        # Chainage Group
        chainage_group = QGroupBox("Chainage")
        chainage_layout = QHBoxLayout(chainage_group)
        chainage_layout.addWidget(QLabel("From chainage:"))
        self.from_chainage_edit = QLineEdit(str(from_chainage) if from_chainage else "")
        chainage_layout.addWidget(self.from_chainage_edit)
        chainage_layout.addWidget(QLabel("To chainage:"))
        self.to_chainage_edit = QLineEdit(str(to_chainage) if to_chainage else "")
        chainage_layout.addWidget(self.to_chainage_edit)
        layout.addWidget(chainage_group)

        # Material Properties Group
        material_group = QGroupBox("Material Properties")
        material_layout = QGridLayout(material_group)
        material_layout.addWidget(QLabel("Material Thickness (m):"), 0, 0)
        self.thickness_edit = QLineEdit(str(material_thickness) if material_thickness else "")
        material_layout.addWidget(self.thickness_edit, 0, 1)
        material_layout.addWidget(QLabel("Width (m):"), 1, 0)
        self.width_edit = QLineEdit(str(width) if width else "")
        material_layout.addWidget(self.width_edit, 1, 1)
        layout.addWidget(material_group)

        # After Rolling Group
        rolling_group = QGroupBox("After Rolling")
        rolling_layout = QHBoxLayout(rolling_group)
        rolling_layout.addWidget(QLabel("Thickness (m):"))
        self.after_rolling_edit = QLineEdit(str(after_rolling) if after_rolling else "")
        rolling_layout.addWidget(self.after_rolling_edit)
        layout.addWidget(rolling_group)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("okBtn")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)


    def get_data(self):
        try:
            def parse_chainage_to_meters(s):
                if not s:
                    return None
                s = s.split('(')[0].strip()  # remove approx note
                s = s.replace(' ', '')
                if '+' in s:
                    km_str, interval_str = s.split('+')
                    # km = int(km_str)  # We DON'T add km*1000 here!
                    interval = float(interval_str)  # Just the interval meters
                    return interval  # Return only meters along the line (0 to total_distance)
                else:
                    # If plain number (e.g., "150.5m")
                    return float(s.replace('m', ''))

            from_m = parse_chainage_to_meters(self.from_chainage_edit.text().strip())
            to_m   = parse_chainage_to_meters(self.to_chainage_edit.text().strip())

            if from_m is None or to_m is None:
                QMessageBox.warning(self, "Invalid", "Please enter valid chainage.")
                return None

            thickness = float(self.thickness_edit.text().strip() or 0)
            width     = float(self.width_edit.text().strip() or 0)
            after_rolling = float(self.after_rolling_edit.text().strip() or 0)

            return {
                'from_chainage_m': from_m,
                'to_chainage_m': to_m,
                'material_thickness_m': thickness,
                'width_m': width,
                'after_rolling_thickness_m': after_rolling
            }
        except Exception as e:
            QMessageBox.warning(self, "Input Error",
                                f"Invalid chainage format. Use KM+Interval like 101+000 or just meters.\nError: {str(e)}")
            return None
        

# ======================================================================================================================================================================
#                                                                ** NEW MATERIAL LINE DIALOG CLASS **
# ======================================================================================================================================================================
class NewMaterialLineDialog(QDialog):
    """Dialog for creating new material lines after the first one.
       Intelligently splits references using EXACT chainage strings from JSON files."""
    def __init__(self, material_config=None, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.material_config = material_config or {}
        self.table_data = []
        self.is_edit_mode = bool(material_config and material_config.get('name'))

        title = "Edit Material Line" if self.is_edit_mode else "New Material Line Configuration"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(1100)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #f0e6fa, stop:1 #e6e6fa);
                border-radius: 20px;
            }
            QLabel { color: black; font-weight: 500; font-size: 14px; }
            QLineEdit {
                border: 2px solid #9C27B0; border-radius: 8px; padding: 8px;
                background-color: white;
            }
            QLineEdit:focus { border: 2px solid #7B1FA2; background-color: #F3E5F5; }
            QLineEdit[readOnly="true"] { background-color: #f0f0f0; color: #555555; }
            QPushButton { border-radius: 20px; padding: 10px; font-weight: bold; min-width: 120px; border: none; }
            QPushButton#saveBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9C27B0, stop:1 #6A1B9A);
                color: white;
            }
            QPushButton#saveBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #AB47BC, stop:1 #4A148C);
            }
            QPushButton#cancelBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E1BEE7, stop:1 #CE93D8);
                color: #333333;
            }
            QPushButton#cancelBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D1C4E9, stop:1 #BA68C8);
            }
        """)

        self.load_table_data()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000; padding-bottom: 15px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Material Line Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Material line name:")
        name_label.setFixedWidth(150)
        self.name_input = QLineEdit()
        
        # Always start empty — user types whatever they want
        self.name_input.clear()
        self.name_input.setPlaceholderText("Enter any name: e.g. GSB, WMM, DBM, Subbase, m1")
        
        # Optional: helpful tooltip
        self.name_input.setToolTip("Type the exact name for this material layer (fully customizable)")

        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input, 1)
        layout.addLayout(name_layout)

        # Material Type
        type_layout = QHBoxLayout()
        type_label = QLabel("Material Type:")
        type_label.setFixedWidth(150)
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("Enter material type (e.g., GSB, WMM, Soil, Stone)")
        
        if self.is_edit_mode:
            self.type_input.setText(self.material_config.get('material_type', ''))
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_input, 1)
        layout.addLayout(type_layout)

        # Table
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setSpacing(15)

        header = QHBoxLayout()
        headers = ["From", "→", "To", "Reference Name", "Width (m)", "Initial Thickness", "After Rolling"]
        for i, text in enumerate(headers):
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            header.addWidget(label)
            if i == 0: header.addSpacing(5)
            elif i == 1: header.addSpacing(15)
            elif i == 2: header.addSpacing(5)
            elif i == 3: header.addSpacing(80)
            elif i == 4: header.addSpacing(20)
            elif i == 5: header.addSpacing(15)
            elif i == 6: header.addSpacing(80)

        table_layout.addLayout(header)

        self.segment_rows = []

        if self.table_data:
            for idx, item in enumerate(self.table_data):
                row = self.create_row(idx, item, is_edit_mode=self.is_edit_mode)
                table_layout.addLayout(row['layout'])
                self.segment_rows.append(row)
        else:
            for i in range(3):
                row = self.create_row(i, None, is_edit_mode=False)
                table_layout.addLayout(row['layout'])
                self.segment_rows.append(row)

        layout.addWidget(table_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self.on_save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def load_table_data(self):
        """Load and split references using EXACT chainage strings from JSON files."""
        self.table_data = []

        if not self.parent or not hasattr(self.parent, 'current_construction_layer_path'):
            return

        construction_path = self.parent.current_construction_layer_path
        worksheet_root = os.path.abspath(os.path.join(construction_path, "..", ".."))
        designs_path = os.path.join(worksheet_root, "designs")

        # === Step 1: Get Construction baseline full range (with exact strings) ===
        overall_start_str = overall_end_str = ""
        overall_start_m = overall_end_m = None

        const_config_path = os.path.join(construction_path, "Construction_Layer_config.txt")
        ref_design_layer = ""
        if os.path.exists(const_config_path):
            try:
                with open(const_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                ref_design_layer = data.get("reference_layer_2d", "")
            except: pass

        baseline_path = None
        if ref_design_layer:
            candidate = os.path.join(designs_path, ref_design_layer, "construction_baseline.json")
            if os.path.exists(candidate):
                baseline_path = candidate

        if baseline_path and os.path.exists(baseline_path):
            try:
                with open(baseline_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                polylines = data.get("polylines", [])
                all_pts = []
                for poly in polylines:
                    all_pts.extend(poly.get("points", []))
                if all_pts:
                    all_pts.sort(key=lambda p: p.get("chainage_m", 0))
                    first = all_pts[0]
                    last = all_pts[-1]
                    overall_start_m = first.get("chainage_m")
                    overall_end_m = last.get("chainage_m")
                    overall_start_str = first.get("chainage_str", f"{overall_start_m:.3f}" if overall_start_m else "")
                    overall_end_str = last.get("chainage_str", f"{overall_end_m:.3f}" if overall_end_m else "")
            except Exception as e:
                print(f"Error loading construction baseline: {e}")

        if not overall_start_str or not overall_end_str:
            return

        # === Step 2: Collect all existing material lines with their EXACT chainage strings ===
        material_coverages = []  # List of (start_m, end_m, name, from_str, to_str, json_data)

        known_non_material = {
            "zero_line_config.json",
            "construction_layer_config.txt",
            "worksheet_config.json"
        }

        for filename in os.listdir(construction_path):
            if not filename.lower().endswith(".json"):
                continue
            if filename in known_non_material:
                continue

            json_path = os.path.join(construction_path, filename)
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if not (
                    "material_line_name" in data or
                    "material_line_id" in data or
                    "segments" in data or
                    "overall_from_chainage" in data
                ):
                    continue

                material_name = (
                    data.get("material_line_name") or
                    data.get("material_line_id") or
                    data.get("name") or
                    os.path.splitext(filename)[0]
                )

                from_info = data.get("overall_from_chainage", {})
                to_info = data.get("overall_to_chainage", {})

                start_m = from_info.get("chainage_m")
                end_m = to_info.get("chainage_m")
                from_str = from_info.get("chainage_str", f"{start_m:.3f}" if start_m is not None else "")
                to_str = to_info.get("chainage_str", f"{end_m:.3f}" if end_m is not None else "")

                if start_m is not None and end_m is not None and from_str and to_str and end_m > start_m:
                    material_coverages.append((start_m, end_m, material_name, from_str, to_str, data))

            except Exception as e:
                print(f"Skipped {filename}: {e}")

        # Sort by start chainage
        material_coverages.sort(key=lambda x: x[0])

        # === Step 3: Build segmented rows using exact strings ===
        segments = []
        current_pos_m = overall_start_m

        for start_m, end_m, mat_name, from_str, to_str, mat_data in material_coverages:
            # Add Construction segment before this material (if gap exists)
            if current_pos_m is not None and start_m > current_pos_m + 0.001:  # tolerance for float
                segments.append({
                    'from': overall_start_str if len(segments) == 0 else segments[-1]['to'],
                    'to': from_str,
                    'name': "Construction",
                    'width': "",
                    'initial': 0,
                    'final': 0
                })

            # Add the material segment with exact strings
            width = initial = final = ""
            segs = mat_data.get("segments", [])
            if segs:
                s = segs[0]
                width = s.get("width_m", "")
                initial = s.get("material_thickness_m", 0)
                final = s.get("after_rolling_thickness_m", 0)

            segments.append({
                'from': from_str,
                'to': to_str,
                'name': mat_name,
                'width': width,
                'initial': initial,
                'final': final
            })

            current_pos_m = end_m

        # Add final Construction segment
        if current_pos_m is not None and overall_end_m > current_pos_m + 0.001:
            last_to = overall_end_str
            from_for_last = material_coverages[-1][4] if material_coverages else overall_start_str
            segments.append({
                'from': from_for_last,
                'to': last_to,
                'name': "Construction",
                'width': "",
                'initial': 0,
                'final': 0
            })

        # If no materials, just full construction
        if not segments:
            segments.append({
                'from': overall_start_str,
                'to': overall_end_str,
                'name': "Construction",
                'width': "",
                'initial': 0,
                'final': 0
            })

        self.table_data = segments

    def create_row(self, index, item_data, is_edit_mode=False):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)

        checkbox = QCheckBox()
        if is_edit_mode and item_data:
            ref_layer = self.material_config.get('ref_layer')
            if isinstance(ref_layer, list):
                checkbox.setChecked(item_data['name'] in ref_layer)
            else:
                checkbox.setChecked(str(item_data['name']).lower() == str(ref_layer).lower())
        else:
            checkbox.setChecked(True)

        row_layout.addWidget(checkbox)

        from_edit = QLineEdit(str(item_data['from']) if item_data else "")
        from_edit.setReadOnly(True)
        from_edit.setFixedWidth(130)
        row_layout.addWidget(from_edit)

        row_layout.addWidget(QLabel("→"), alignment=Qt.AlignCenter)

        to_edit = QLineEdit(str(item_data['to']) if item_data else "")
        to_edit.setReadOnly(True)
        to_edit.setFixedWidth(130)
        row_layout.addWidget(to_edit)

        name_label = QLineEdit(item_data['name'] if item_data else "Unknown")
        name_label.setReadOnly(True)
        name_label.setFixedWidth(200)
        row_layout.addWidget(name_label, alignment=Qt.AlignCenter)

        width_edit = QLineEdit()
        width_edit.setFixedWidth(100)
        if item_data and item_data['width'] not in ("", None):
            width_edit.setText(str(item_data['width']))
        row_layout.addWidget(width_edit, alignment=Qt.AlignCenter)

        initial_edit = QLineEdit()
        initial_edit.setFixedWidth(130)
        if item_data and item_data['initial'] not in ("", None, 0):
            val = item_data['initial']
            if isinstance(val, (int, float)):
                initial_edit.setText(f"{val * 1000:.0f} mm")
        row_layout.addWidget(initial_edit, alignment=Qt.AlignCenter)

        final_edit = QLineEdit()
        final_edit.setFixedWidth(130)
        if item_data and item_data['final'] not in ("", None, 0):
            val = item_data['final']
            if isinstance(val, (int, float)):
                final_edit.setText(f"{val * 1000:.0f} mm")
        row_layout.addWidget(final_edit, alignment=Qt.AlignCenter)

        row_layout.addStretch()

        return {
            'layout': row_layout,
            'checkbox': checkbox,
            'from': from_edit,
            'to': to_edit,
            'material_name': name_label,
            'width': width_edit,
            'initial': initial_edit,
            'final': final_edit
        }


    def on_save(self):
        updated_segments = []
        checked_refs = []

        for row in self.segment_rows:
            if not row['checkbox'].isChecked():
                continue

            ref_name = row['material_name'].text().strip()
            checked_refs.append(ref_name)

            w = row['width'].text().strip()
            i = row['initial'].text().strip()
            f = row['final'].text().strip()

            if not w:
                QMessageBox.warning(self, "Error", f"Width required for {ref_name}")
                return
            try:
                width_m = float(w)
            except:
                QMessageBox.warning(self, "Error", f"Invalid width for {ref_name}")
                return

            def parse_mm(text):
                if not text: return 0.0
                text = text.lower().replace("mm", "").strip()
                try: return float(text) / 1000.0
                except: return None

            init_m = parse_mm(i)
            final_m = parse_mm(f)
            if (i and init_m is None) or (f and final_m is None):
                QMessageBox.warning(self, "Error", f"Invalid thickness for {ref_name}")
                return

            updated_segments.append({
                'from_chainage': row['from'].text().strip(),
                'to_chainage': row['to'].text().strip(),
                'width': width_m,
                'initial_thickness': init_m or 0.0,
                'after_rolling': final_m or 0.0
            })

        if not updated_segments:
            QMessageBox.warning(self, "Error", "At least one reference must be selected")
            return

        # === SECURITY: Force user to enter a name ===
        material_name = self.name_input.text().strip()
        if not material_name:
            QMessageBox.warning(self, "Required Field", "Please enter a Material line name.")
            return

        # Use the validated name
        proposed_name = material_name

        # === ENFORCE UNIQUE NAME (your existing logic preserved) ===
        existing_names = [cfg['name'] for cfg in getattr(self.parent, 'material_configs', [])]

        if self.is_edit_mode:
            current_original_name = self.material_config.get('name', '')
            if proposed_name != current_original_name and proposed_name in existing_names:
                QMessageBox.warning(self, "Duplicate Name",
                                    f"A material named '{proposed_name}' already exists.\n"
                                    "Please choose a unique name.")
                return
        else:
            if proposed_name in existing_names:
                counter = 1
                base_name = proposed_name
                while f"{base_name} ({counter})" in existing_names:
                    counter += 1
                unique_name = f"{base_name} ({counter})"
                reply = QMessageBox.question(self, "Name Conflict",
                                             f"'{proposed_name}' already exists.\n"
                                             f"Use '{unique_name}' instead?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    proposed_name = unique_name
                else:
                    return

        material_type = self.type_input.text().strip()

        unique_refs = list(dict.fromkeys(checked_refs))
        ref_layer_value = unique_refs[0] if len(unique_refs) == 1 else unique_refs

        self.result_data = {
            'name': proposed_name,
            'material_type': material_type,
            'ref_layer': ref_layer_value,
            'segments': updated_segments
        }

        self.accept()

    def get_material_data(self):
        return getattr(self, 'result_data', None)