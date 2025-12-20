# main.py
import os
import numpy as np
import open3d as o3d
import time
import json

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton, QFileDialog, QMessageBox, QDialog, QApplication,
    QCheckBox
)
from PyQt5.QtCore import Qt, QByteArray, QSize, QRectF, QTimer, QEvent
from PyQt5.QtGui import QPixmap, QPainter, QIcon
from PyQt5.QtSvg import QSvgRenderer

import vtk
from vtkmodules.vtkFiltersSources import vtkSphereSource, vtkLineSource
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper)

from vtkmodules.vtkFiltersSources import vtkPlaneSource


from datetime import datetime
from math import sqrt, degrees

from utils import find_best_fitting_plane
from application_ui import ApplicationUI
from dialogs import (ConstructionConfigDialog, CurveDialog, ZeroLineDialog, MaterialLineDialog, MeasurementDialog,
                    DesignNewDialog, WorksheetNewDialog, HelpDialog, ConstructionNewDialog, CreateProjectDialog, ExistingWorksheetDialog,
                    RoadPlaneWidthDialog)

# =============================================================================================================================================
#                                                        ** CLASS POINTCLOUDVIEWER **
# =============================================================================================================================================
class PointCloudViewer(ApplicationUI):
    def __init__(self, username=None):  # Add username parameter
        super().__init__()
        self.current_user = username or "guest"  # Store logged-in user

        # Add these lines
        self.current_worksheet_name = None
        self.current_project_name = None     # <-- Important
        self.current_worksheet_data = {}

        # Curve-related attributes
        self.curve_active = False
        self.curve_start_x = None
        self.curve_annotation = None        # First/main curve label (yellow box)
        self.curve_arrow_annotation = None
        self.curve_pick_id = None
        self.curve_labels = []              # Stores ALL "5.0° - I" labels on top (including intermediates)
        self.current_curve_text = ""        # Stores the text like "5.0° - I"

        self.road_plane_actors = []      # Stores the two side planes (left + right)
        self.road_plane_center_actor = None   # Optional: centre line for reference

        self.slider_marker_actor = None   # The sphere actor that follows the slider
        self.slider_marker_radius = 0.45  # Size of the marker sphere (adjust if needed)

        # NEW: storage for 3D curve actors (so we can clear them later)
        self.curve_3d_actors = []          # list of vtkActor for the yellow arcs
        self.curve_start_point_3d = None   # world coordinate of the point where curve started
        self.curve_start_chainage = None   # distance along zero line at start
        # NEW: 3D curve support
        self.surface_line_3d_points = []

        self.zero_interval = None  # Will be set when zero line is defined

        self.bottom_button_layout = None   # Add for the baseline name show in bottom section

        self.material_line_widgets = []

        # NEW: Unified plane support for ALL baselines
        self.baseline_plane_actors = []     # Stores all plane actors (individual + combined)
        self.plane_colors = {               # Distinct semi-transparent colors for each type
            'surface': (0.0, 0.8, 0.0, 0.4),      # Green
            'construction': (1.0, 0.0, 0.0, 0.4), # Red
            'road_surface': (0.0, 0.6, 1.0, 0.45),# Blue
            'deck_line': (1.0, 0.5, 0.0, 0.4),    # Orange
            'projection_line': (0.5, 0.0, 0.5, 0.4), # Purple
            'material': (1.0, 1.0, 0.0, 0.4),     # Yellow
        }

        # List of line types considered as "baselines" for plane mapping
        self.baseline_types = ['surface', 'construction', 'road_surface', 'deck_line', 'projection_line', 'material']

        # Construction mode state
        self.construction_mode_active = False
        self.current_construction_layer = None  # Will store layer name/folder if needed later
        
        # Define worksheet base directory
        self.WORKSHEETS_BASE_DIR = r"E:\3D_Tool\user\worksheets"
        os.makedirs(self.WORKSHEETS_BASE_DIR, exist_ok=True)

        # === ADD THIS: Projects base directory ===
        self.PROJECTS_BASE_DIR = r"E:\3D_Tool\projects"
        os.makedirs(self.PROJECTS_BASE_DIR, exist_ok=True)
        
        # Initialize specific attributes that need different values
        self.start_point = np.array([387211.43846649484, 2061092.3144329898, 598.9991744523196])
        self.end_point = np.array([387219.37847222225, 2060516.8861111111, 612.2502197265625])
        self.total_distance = np.sqrt((self.end_point[0] - self.start_point[0])**2 + (self.end_point[1] - self.start_point[1])**2)
        self.original_total_distance = self.total_distance
        
        # Connect signals
        self.connect_signals()

        # NEW: Connect label click event AFTER everything is initialized
        self.label_pick_id = None  # Initialize the attribute
        
        # Add this method call to set up the label click handler
        QTimer.singleShot(100, self.setup_label_click_handler)  # Small delay to ensure canvas is ready

# ===================================================================================================================================
    def setup_label_click_handler(self):
        """Set up the label click event handler after canvas is fully initialized"""
        if self.canvas:
            self.label_pick_id = self.canvas.mpl_connect('pick_event', self.on_label_click)  

# ===================================================================================================================================
    def on_label_click(self, event):
        """Handle click on construction dot labels"""
        artist = event.artist
        
        # Check if this is a construction dot label
        if hasattr(artist, 'point_data') and artist.point_data.get('type') == 'construction_dot':
            point_number = artist.point_data['point_number']
            x = artist.point_data['x']
            y = artist.point_data['y']
            
            # Calculate chainage for this point using the KM+Interval format
            if self.zero_line_set and hasattr(self, 'zero_start_km') and self.zero_start_km is not None:
                # Calculate which interval this point falls into
                # x is the distance along the zero line in meters
                interval_number = int(x / self.zero_interval) if self.zero_interval > 0 else 0
                
                # Calculate the interval value (multiple of the interval)
                interval_value = interval_number * self.zero_interval
                
                # Format as KM+Interval (3 digits with leading zeros)
                chainage_label = f"{self.zero_start_km}+{interval_value:03d}"
                
                # Add note about exact position if not exactly on interval
                if self.zero_interval > 0:
                    exact_position = x
                    exact_interval_value = int(exact_position / self.zero_interval) * self.zero_interval
                    if abs(exact_position - exact_interval_value) > 0.01:  # If not exactly on interval
                        chainage_label += f" (approx, actual: {exact_position:.2f}m)"
            else:
                chainage_label = f"Distance: {x:.2f}m"
            
            # Open construction configuration dialog with updated chainage format
            dialog = ConstructionConfigDialog(chainage_label, self)
            dialog.setWindowTitle(f"Construction Configuration - Point P{point_number}")
            
            if dialog.exec_() == QDialog.Accepted:
                config = dialog.get_configuration()
                self.message_text.append(f"Construction configuration saved for Point P{point_number}:")
                self.message_text.append(f"  Chainage: {config['chainage']}")
                self.message_text.append(f"  Water Position: {config['water_position']}")
                self.message_text.append(f"  Base Shape: {config['base_shape']}")
                self.message_text.append(f"  Pillar Shape: {config['pillar_shape']}")
                self.message_text.append(f"  Span Shape: {config['span_shape']}")
                self.message_text.append(f"  Base Dimensions: Width={config['base_width']}, Length={config['base_length']}, Height={config['base_height']}")
                self.message_text.append(f"  Pillar Dimensions: Radius={config['pillar_radius']}, Height={config['pillar_height']}")
                self.message_text.append(f"  Span Dimensions: Height={config['span_height']}, Width={config['span_width']}")
                
                # Store this configuration with the point for later reference
                artist.point_data['config'] = config
                
                # Update the label to show it's configured (add checkmark)
                artist.set_text(f'P{point_number}✓')
                artist.set_bbox(dict(
                    boxstyle='round,pad=0.5', 
                    facecolor='lightgreen', 
                    alpha=0.9,
                    edgecolor='green',
                    linewidth=2
                ))
                
                # Redraw the canvas
                self.canvas.draw_idle()

# =====================================================================================================================================
    def scroll_graph_with_slider(self, value):
        """Scroll the graph canvas based on slider position"""
        if not hasattr(self, 'graph_horizontal_scrollbar') or not self.graph_horizontal_scrollbar:
            return
        
        # Get the maximum range of the slider
        slider_max = self.volume_slider.maximum()
        
        # Get the maximum range of the scrollbar
        scrollbar_max = self.graph_horizontal_scrollbar.maximum()
        
        # Calculate the position
        if slider_max > 0 and scrollbar_max > 0:
            # Map slider value (0-100) to scrollbar range
            scroll_position = int((value / slider_max) * scrollbar_max)
            self.graph_horizontal_scrollbar.setValue(scroll_position)
            
            # Update the visual marker on the main graph
            self.update_main_graph_marker(value)
        
# =======================================================================================================================================
    # HOVER HANDLER FOR POINTS
    def on_hover(self, event):
        if event.inaxes != self.ax:
            self.annotation.set_visible(False)
            self.canvas.draw_idle()
            return
        vis = self.annotation.get_visible()
        closest_point = None
        min_dist = float('inf')
        for line_type in ['surface', 'construction', 'road_surface']:
            for artist in self.line_types[line_type]['artists']:
                if len(artist.get_xdata()) == 0:
                    continue
                xs = artist.get_xdata()
                ys = artist.get_ydata()
                distances = np.hypot(xs - event.xdata, ys - event.ydata)
                idx = np.argmin(distances)
                if distances[idx] < 0.2: # threshold for hover detection
                    if distances[idx] < min_dist:
                        min_dist = distances[idx]
                        closest_point = (xs[idx], ys[idx])
        if closest_point is not None:
            x_dist, rel_elev = closest_point
            if self.zero_line_set and self.total_distance > 0:
                t = x_dist / self.total_distance
                dir_vec = self.zero_end_point - self.zero_start_point
                pos_along = self.zero_start_point + t * dir_vec
                abs_z = self.zero_start_z + rel_elev
                text = f'({pos_along[0]:.3f}, {pos_along[1]:.3f}, {abs_z:.2f})'
            else:
                text = f'({x_dist:.2f}, {rel_elev:.2f})'
            self.annotation.xy = closest_point
            self.annotation.set_text(text)
            self.annotation.set_visible(True)
            self.canvas.draw_idle()
        elif vis:
            self.annotation.set_visible(False)
            self.canvas.draw_idle()
    
# =======================================================================================================================================
    def set_measurement_type(self, mtype):
        """Helper to switch measurement type"""
        self.current_measurement = mtype
        self.measurement_points = []
        self.message_text.append(f"Switched to {mtype.replace('_', ' ').title()}")

# =======================================================================================================================================
    def reset_measurement_tools(self):
        """Clear all measurement buttons and states"""
        self.line_button.setVisible(False)
        self.polygon_button.setVisible(False)
        self.stockpile_polygon_button.setVisible(False)
        self.complete_polygon_button.setVisible(False)
        self.presized_button.setVisible(False)
        self.metrics_group.setVisible(False)

# =======================================================================================================================================
# Close dropdown when clicking outside
    def eventFilter(self, obj, event):
        if event.type() == event.MouseButtonPress:
            if obj.isWidgetType() and obj.windowFlags() & Qt.Popup:
                # click outside any popup → close all popups
                for btn in [self.worksheet_button, self.design_button,
                            self.construction_button, self.measurement_button]:
                    if btn.isChecked():
                        btn.setChecked(False)
                        btn.property("dropdown").hide()
        return super().eventFilter(obj, event)
    
# =======================================================================================================================================
# Helper called when user picks New / Existing (optional)
    def on_dropdown_choice(self, main_btn, choice):
        main_btn.setChecked(False)
        main_btn.property("dropdown").hide()
        #print(f"{main_btn.text()} → {choice} selected")   # replace with real logic

# =======================================================================================================================================   
    def load_last_worksheet(self):
        """Load and display the most recently created worksheet on startup"""
        if not os.path.exists(self.WORKSHEET_FILE):
            return
        try:
            with open(self.WORKSHEET_FILE, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                if not lines:
                    return
                last_data = json.loads(lines[-1])
                self.display_current_worksheet(last_data)
                self.message_text.append(f"Loaded last worksheet: {last_data.get('worksheet_name', 'Unknown')}")
        except Exception as e:
            print(f"Failed to load last worksheet: {e}")

# =======================================================================================================================================
# TOGGLE MESSAGE SECTION
    def toggle_message_section(self):
        self.message_visible = not self.message_visible
        self.message_section.setVisible(self.message_visible)
        self.message_button.setText("Hide Message" if self.message_visible else "Message")

# =======================================================================================================================================
    def toggle_worksheet_options(self):
        checked = self.worksheet_button.isChecked()
        self.sub_buttons_widget.setVisible(checked)
        
        # Optional: change icon/text to indicate open/close state
        self.worksheet_button.setText("📊Worksheet ▼" if checked else "📊Worksheet")

# =======================================================================================================================================
    def toggle_design_options(self):
        checked = self.design_button.isChecked()
        self.sub_design_buttons_widget.setVisible(checked)
        
        # Optional: change icon/text to indicate open/close state
        self.design_button.setText("📐Design ▼" if checked else "📐Design")

# =======================================================================================================================================   
    def toggle_construction_options(self):
        checked = self.construction_button.isChecked()
        self.sub_construction_buttons_widget.setVisible(checked)
        
        # Optional: change icon/text to indicate open/close state
        self.construction_button.setText("🏗 Construction ▼" if checked else "🏗 Construction")

# =======================================================================================================================================
    def toggle_measurement_options(self):
        checked = self.measurement_button.isChecked()
        self.sub_measurement_buttons_widget.setVisible(checked)
        
        # Optional: change icon/text to indicate open/close state
        self.measurement_button.setText("📏Measurement ▼" if checked else "📏Measurement")

# =======================================================================================================================================
    def open_create_project_dialog(self):
        dialog = CreateProjectDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            project_name = data["project_name"].strip()
            pointcloud_files = data["pointcloud_files"]
            category = data["category"]

            if not project_name:
                QMessageBox.warning(self, "Error", "Project name is required!")
                return

            if not pointcloud_files:
                QMessageBox.warning(self, "Error", "Please select at least one point cloud file or folder.")
                return

            # Define base projects directory
            BASE_PROJECTS_DIR = r"E:\3D_Tool\projects"
            os.makedirs(BASE_PROJECTS_DIR, exist_ok=True)

            # Create project-specific folder
            project_folder = os.path.join(BASE_PROJECTS_DIR, project_name)
            try:
                os.makedirs(project_folder, exist_ok=False)  # Raises error if already exists
            except FileExistsError:
                reply = QMessageBox.question(
                    self, "Project Exists",
                    f"A project named '{project_name}' already exists.\nDo you want to overwrite it?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
                # If yes, continue (folder already exists, we'll overwrite config)

            # Prepare project config data
            project_entry = {
                "project_name": project_name,
                "pointcloud_files": pointcloud_files,  # List of full paths
                "category": category,
                "created_at": datetime.now().isoformat(),
                "created_by": self.current_user  # Optional: track who created it
            }

            # Path to project_config.txt inside the project folder
            config_file_path = os.path.join(project_folder, "project_config.txt")

            try:
                with open(config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(project_entry, f, indent=4)
                
                QMessageBox.information(
                    self, "Success",
                    f"Project '{project_name}' created successfully!\n\n"
                    f"Location:\n{project_folder}\n\n"
                    f"Point cloud files linked: {len(pointcloud_files)} file(s)"
                )

                self.message_text.append(f"New project created: {project_name}")
                self.message_text.append(f"   → Folder: {project_folder}")
                self.message_text.append(f"   → Files linked: {len(pointcloud_files)}")

                # Optional: You can now allow loading this project later
                # Or auto-load point clouds if desired

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save project configuration:\n{str(e)}")
                self.message_text.append(f"Error saving project '{project_name}': {str(e)}")

# =======================================================================================================================================
    def open_new_worksheet_dialog(self):
        """Open dialog to create a new worksheet with Road/Bridge baseline selection and dynamic UI updates.
        Creates 'designs' or 'measurements' subfolder based on 2D/3D selection, then adds the initial layer folder."""
        dialog = WorksheetNewDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return

        data = dialog.get_data()
        worksheet_name = data["worksheet_name"].strip()

        if not worksheet_name:
            QMessageBox.warning(self, "Invalid Name", "Worksheet name cannot be empty!")
            return

        project_name = data["project_name"] if data["project_name"].strip() else None
        category = data["worksheet_category"]  # "Road", "Bridge", "Other", "None"
        worksheet_type = data["worksheet_type"]  # "Design" or "Measurement"
        dimension = "2D" if worksheet_type == "Design" else "3D"
        initial_layer_name = data["initial_layer_name"].strip()  # User-entered layer name
        point_cloud_file = data.get("point_cloud_file")

        # Create main worksheet folder
        worksheet_folder = os.path.join(self.WORKSHEETS_BASE_DIR, worksheet_name)
        try:
            os.makedirs(worksheet_folder, exist_ok=False)
        except FileExistsError:
            reply = QMessageBox.question(self, "Folder Exists",
                                        f"A worksheet named '{worksheet_name}' already exists.\n"
                                        f"Do you want to overwrite it?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # === NEW LOGIC: Create 'designs' or 'measurements' based on dimension ===
        if dimension == "2D":
            base_subfolder = os.path.join(worksheet_folder, "designs")
            self.message_text.append("   → Creating 'designs' folder for 2D Design mode")
        else:  # 3D
            base_subfolder = os.path.join(worksheet_folder, "measurements")
            self.message_text.append("   → Creating 'measurements' folder for 3D Measurement mode")

        try:
            os.makedirs(base_subfolder, exist_ok=True)
        except Exception as e:
            self.message_text.append(f"   → Warning: Could not create subfolder '{os.path.basename(base_subfolder)}': {str(e)}")

        # === Create initial layer folder inside the correct subfolder (only if layer name provided) ===
        layer_folder = None
        if initial_layer_name:
            layer_folder = os.path.join(base_subfolder, initial_layer_name)
            try:
                os.makedirs(layer_folder, exist_ok=True)
                self.message_text.append(f"   → Initial layer folder created: {initial_layer_name}")
                self.message_text.append(f"      Path: {layer_folder}")
            except Exception as e:
                self.message_text.append(f"   → Error creating layer folder '{initial_layer_name}': {str(e)}")
                layer_folder = None
        else:
            self.message_text.append("   → No layer name entered — no initial layer folder created")

        # Save worksheet config
        config_data = {
            "worksheet_name": worksheet_name,
            "project_name": project_name or "None",
            "created_at": datetime.now().isoformat(),
            "created_by": self.current_user,
            "worksheet_type": worksheet_type,
            "initial_layer": initial_layer_name or None,
            "worksheet_category": category,
            "dimension": dimension,
            "point_cloud_file": point_cloud_file
        }

        config_path = os.path.join(worksheet_folder, "worksheet_config.txt")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"Could not save worksheet config:\n{str(e)}")
            return

        # Update application state
        self.current_worksheet_name = worksheet_name
        self.current_project_name = project_name
        self.current_worksheet_data = config_data.copy()
        self.display_current_worksheet(config_data)

        # Add initial layer to left panel (if name was provided)
        if initial_layer_name:
            self.add_layer_to_panel(initial_layer_name, dimension)

        self.current_layer_name = initial_layer_name

        # Show/Hide 3D vs 2D sections
        if dimension == "3D":
            self.three_D_frame.setVisible(True)
            self.two_D_frame.setVisible(False)
            self.message_text.append("→ 3D Layers section shown, 2D Layers hidden (Measurement mode)")
        elif dimension == "2D":
            self.three_D_frame.setVisible(False)
            self.two_D_frame.setVisible(True)
            self.message_text.append("→ 2D Layers section shown, 3D Layers hidden (Design mode)")

        # Log messages
        self.message_text.append(f"Worksheet '{worksheet_name}' created successfully!")
        self.message_text.append(f"   → Path: {worksheet_folder}")
        self.message_text.append(f"   → Type: {worksheet_type} ({dimension})")
        self.message_text.append(f"   → Category: {category}")

        if point_cloud_file:
            self.message_text.append(f"   → Point Cloud Linked: {os.path.basename(point_cloud_file)}")
        else:
            self.message_text.append(f"   → Point Cloud: None selected")

        # Baseline logic (Road/Bridge)
        ref_type = None
        ref_line = None
        if category in ["Road", "Bridge"]:
            ref_type = category
            available_lines = ["Road_Layer_1", "Road_Layer_2", "Road_Layer_3"] if category == "Road" \
                              else ["Bridge_Layer_1", "Bridge_Layer_2", "Bridge_Layer_3"]
            ref_line = available_lines[0] if available_lines else None

            self.message_text.append(f"   → Baseline Type: {ref_type}")
            if ref_line:
                self.message_text.append(f"   → Reference Baseline: {ref_line}")

        # UI updates based on category
        self.bottom_section.setVisible(category in ["Road", "Bridge"])

        # Hide all containers first
        self.surface_container.setVisible(False)
        self.construction_container.setVisible(False)
        self.road_surface_container.setVisible(False)
        self.zero_container.setVisible(False)
        self.deck_line_container.setVisible(False)
        self.projection_container.setVisible(False)
        self.construction_dots_container.setVisible(False)
        self.bridge_zero_container.setVisible(False)

        if category == "Road":
            self.surface_container.setVisible(True)
            self.construction_container.setVisible(True)
            self.road_surface_container.setVisible(True)
            self.zero_container.setVisible(True)
            self.message_text.append(f"Mode Activated: {dimension} - ROAD Mode")
        elif category == "Bridge":
            self.deck_line_container.setVisible(True)
            self.projection_container.setVisible(True)
            self.construction_dots_container.setVisible(True)
            if hasattr(self, 'bridge_zero_container'):
                self.bridge_zero_container.setVisible(True)
            self.message_text.append(f"Mode Activated: {dimension} - BRIDGE Mode")
        else:
            self.message_text.append(f"Mode Activated: {dimension} - General Mode")

        if ref_line:
            self.message_text.append(f"Reference Baseline Set: {ref_line}")

        # Action buttons
        self.preview_button.setVisible(True)
        self.threed_map_button.setVisible(True)
        self.save_button.setVisible(True)

        # Auto-check zero lines
        if not self.zero_line_set:
            self.zero_line.setChecked(True)
            if hasattr(self, 'bridge_zero_line'):
                self.bridge_zero_line.setChecked(True)

        # Refresh rendering
        self.canvas.draw()
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.GetRenderWindow().Render()

        # Auto-load point cloud if selected
        if point_cloud_file and os.path.exists(point_cloud_file):
            self.message_text.append("Auto-loading selected point cloud...")
            success = self.load_point_cloud_from_path(point_cloud_file)
            if success:
                self.message_text.append("Point cloud loaded successfully!")
            else:
                self.message_text.append("Failed to auto-load point cloud.")
        elif point_cloud_file:
            self.message_text.append(f"Selected point cloud file not found: {point_cloud_file}")

        # Final success message
        layer_display = initial_layer_name if initial_layer_name else "(none)"
        layer_path_display = layer_folder if layer_folder else "(not created)"
        pc_display = os.path.basename(point_cloud_file) if point_cloud_file else "None"

        QMessageBox.information(self, "Success",
                                f"Worksheet '{worksheet_name}' created successfully!\n\n"
                                f"Dimension: {dimension} ({worksheet_type})\n"
                                f"Initial Layer: {layer_display}\n"
                                f"Layer Path: {layer_path_display}\n"
                                f"Mode: {category or 'General'}\n"
                                f"Point Cloud: {pc_display}\n\n"
                                f"Saved in:\n{worksheet_folder}")

# =======================================================================================================================================
    def display_current_worksheet(self, config_data):
        """
        Updates the Current Worksheet box and the top mode banner (Measurement/Design)
        """
        if not config_data:
            self.worksheet_display.setVisible(False)
            self.mode_banner.setVisible(False)
            return

        self.worksheet_display.setVisible(True)
        self.mode_banner.setVisible(True)

        worksheet_name = config_data.get("worksheet_name", "Unknown")
        project_name = config_data.get("project_name", "None")
        worksheet_type = config_data.get("worksheet_type", "Unknown")  # "Measurement" or "Design"
        category = config_data.get("worksheet_category", "None")
        created_at = config_data.get("created_at", "Unknown")

        # Format created time
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            created_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            created_str = created_at

        # Update worksheet info inside the box
        info_lines = [
            f"<b>Worksheet Name:</b> {worksheet_name}",
            f"<b>Worksheet Type:</b> {worksheet_type}",
            f"<b>Project:</b> {project_name}",
            f"<b>Worksheet Category:</b> {category}",
            f"<b>Worksheet Created:</b> {created_str}"
        ]
        info_text = "<br>".join(info_lines)
        self.worksheet_info_label.setText(info_text)

        # Update title with Active:
        self.worksheet_display.setTitle(f"Active: {worksheet_name}")

        # === UPDATE TOP MODE BANNER ===
        if worksheet_type == "Measurement":
            self.mode_banner.setText("MEASUREMENT MODE")
            self.mode_banner.setStyleSheet("""
            QLabel {
                    font-weight: bold;}
            """)
            # self.mode_banner.setStyleSheet("""
            #     QLabel {
            #         font-size: 22px;
            #         font-weight: bold;
            #         color: white;
            #         background-color: #7B1FA2;
            #         border-radius: 14px;
            #         padding: 16px;
            #         margin: 12px 20px 20px 20px;
            #         border: 4px solid #4A148C;
            #     }
            # """)
        elif worksheet_type == "Design":
            self.mode_banner.setText("DESIGN MODE")
            self.mode_banner.setStyleSheet("""
            QLabel {
                    font-weight: bold;}
            """)
            # self.mode_banner.setStyleSheet("""
            #     QLabel {
            #         font-size: 22px;
            #         font-weight: bold;
            #         color: white;
            #         background-color: #2E7D32;
            #         border-radius: 14px;
            #         padding: 16px;
            #         margin: 12px 20px 20px 20px;
            #         border: 4px solid #1B5E20;
            #     }
            # """)
        else:
            self.mode_banner.setText("GENERAL MODE")
            # self.mode_banner.setStyleSheet("""
            #     QLabel {
            #         font-size: 20px;
            #         font-weight: bold;
            #         color: white;
            #         background-color: #666666;
            #         border-radius: 12px;
            #         padding: 14px;
            #         margin: 10px 15px 15px 15px;
            #     }
            # """)


# =======================================================================================================================================
# # OPEN CREATE NEW DESIGN LAYER DIALOG
    def open_create_new_design_layer_dialog(self):
        """Open the Design New Layer dialog and save config to current worksheet's designs folder"""
        if not hasattr(self, 'current_worksheet_name') or not self.current_worksheet_name:
            QMessageBox.warning(self, "No Active Worksheet",
                                "Please create or open a worksheet first before creating a design layer.")
            return

        dialog = DesignNewDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_configuration()
            layer_name = config["layer_name"]
            dimension = config["dimension"]
            ref_type = config["reference_type"]
            ref_line = config["reference_line"]

            # Build path inside current worksheet
            base_designs_path = os.path.join(self.WORKSHEETS_BASE_DIR, self.current_worksheet_name, "designs")
            layer_folder = os.path.join(base_designs_path, layer_name)

            # Create folder (safe because we already checked in dialog)
            os.makedirs(layer_folder, exist_ok=True)

            # Prepare full config data
            full_config = {
                "layer_name": layer_name,
                "dimension": dimension,
                "reference_type": ref_type,
                "reference_line": ref_line,
                "project_name": getattr(self, 'current_project_name', 'None'),
                "worksheet_name": self.current_worksheet_name,
                "created_by": self.current_user,
                "created_at": datetime.now().isoformat(),
            }

            # Save config file
            config_file_path = os.path.join(layer_folder, "design_layer_config.txt")
            try:
                with open(config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(full_config, f, indent=4)

                QMessageBox.information(self, "Success",
                                        f"Design layer '{layer_name}' created successfully!\n\n"
                                        f"Location:\n{layer_folder}")

                self.message_text.append(f"New design layer created: {layer_name}")
                self.message_text.append(f" → Path: {layer_folder}")
                self.message_text.append(f" → Dimension: {dimension}")
                if ref_type:
                    self.message_text.append(f" → Type: {ref_type} ({ref_line or 'No reference'})")

                # Add to left panel
                self.add_layer_to_panel(layer_name, dimension)
                            # === ADD THIS LINE ===
                self.current_layer_name = layer_name

            except Exception as e:
                QMessageBox.critical(self, "Save Failed", f"Could not save design layer config:\n{str(e)}")
                return

            # === UI Updates ===
            self.bottom_section.setVisible(True)
            self.surface_container.setVisible(False)
            self.construction_container.setVisible(False)
            self.road_surface_container.setVisible(False)
            self.zero_container.setVisible(False)
            self.deck_line_container.setVisible(False)
            self.projection_container.setVisible(False)
            self.construction_dots_container.setVisible(False)
            self.bridge_zero_container.setVisible(False)

            if ref_type == "Road":
                self.surface_container.setVisible(True)
                self.construction_container.setVisible(True)
                self.road_surface_container.setVisible(True)
                self.zero_container.setVisible(True)
                self.message_text.append(f"Design Layer Created: {dimension} - ROAD Mode")
            elif ref_type == "Bridge":
                self.deck_line_container.setVisible(True)
                self.projection_container.setVisible(True)
                self.construction_dots_container.setVisible(True)
                self.bridge_zero_container.setVisible(True)
                self.message_text.append(f"Design Layer Created: {dimension} - BRIDGE Mode")
            else:
                self.message_text.append(f"Design Layer Created: {dimension} - No reference type selected")

            if ref_line:
                self.message_text.append(f"Reference Line: {ref_line}")

            # Show action buttons
            self.preview_button.setVisible(True)
            self.threed_map_button.setVisible(True)
            self.save_button.setVisible(True)

            # Auto-check zero line
            if not self.zero_line_set:
                self.zero_line.setChecked(True)
                if hasattr(self, 'bridge_zero_line'):
                    self.bridge_zero_line.setChecked(True)

            self.canvas.draw()
            self.vtk_widget.GetRenderWindow().Render()
# =======================================================================================================================================
    def open_measurement_dialog(self):
        """Open the Measurement Configuration Dialog when New is clicked"""
        dialog = MeasurementDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_config()

            # Apply units
            idx = ["Meter", "Centimeter", "Millimeter"].index(config["units"].capitalize())
            self.metrics_combo.setCurrentIndex(idx)

            # Reset previous measurement state
            self.reset_measurement_tools()

            # Show relevant buttons
            self.metrics_group.setVisible(True)
            self.line_button.setVisible(config["measurement_type"] == "line")
            self.polygon_button.setVisible(config["measurement_type"] in ["polygon", "stockpile"])
            self.stockpile_polygon_button.setVisible(config["measurement_type"] == "stockpile")
            self.complete_polygon_button.setVisible(config["measurement_type"] in ["polygon", "stockpile"])
            self.presized_button.setVisible(config["presized_enabled"] and config["measurement_type"] == "line")

            # Set current measurement mode
            if config["measurement_type"] == "line":
                self.current_measurement = config["line_type"] + "_line"  # vertical_line, horizontal_line, general_line
                if config["line_type"] == "general":
                    self.current_measurement = "measurement_line"
            elif config["measurement_type"] == "polygon":
                self.current_measurement = "polygon"
            elif config["measurement_type"] == "stockpile":
                self.current_measurement = "polygon"
                self.message_text.append("Stockpile mode: Draw polygon → Complete → then click a height point")

            self.measurement_active = True
            self.plotting_active = False  # Disable graph drawing during measurement

            self.message_text.append(f"Started {config['measurement_type'].title()} measurement ({config['line_type'] if 'line_type' in config else ''})")
            self.message_text.append(f"Units set to: {config['units'].capitalize()}")

            # Connect actions
            self.vertical_line_action.triggered.connect(lambda: self.set_measurement_type('vertical_line'))
            self.horizontal_line_action.triggered.connect(lambda: self.set_measurement_type('horizontal_line'))
            self.measurement_line_action.triggered.connect(lambda: self.set_measurement_type('measurement_line'))
            self.polygon_button.clicked.connect(lambda: self.set_measurement_type('polygon'))
            if config["presized_enabled"]:
                self.presized_button.clicked.connect(self.handle_presized_button)

# =======================================================================================================================================
    def open_construction_new_dialog(self):
        """Handle 'Construction → New' – full workflow: validation, folder creation, config save, UI switch"""
        # 1. Must have an active worksheet
        if not hasattr(self, 'current_worksheet_name') or not self.current_worksheet_name:
            QMessageBox.warning(
                self,
                "No Active Worksheet",
                "Please create or open a worksheet first before creating a construction layer."
            )
            self.message_text.append("Attempted to create construction layer without active worksheet.")
            return

        # 2. Open dialog
        dialog = ConstructionNewDialog(self)
        # Critical: Pass the current worksheet path
        dialog.set_current_worksheet_path(
            os.path.join(self.WORKSHEETS_BASE_DIR, self.current_worksheet_name)
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        data = dialog.get_data()
        layer_name = data['layer_name'].strip()

        if not layer_name:
            QMessageBox.warning(self, "Invalid Name", "Construction layer name cannot be empty!")
            return

        # Determine type
        is_road = data['is_road']
        is_bridge = data['is_bridge']
        construction_type = "Road" if is_road else "Bridge" if is_bridge else "General"

        # 3. Create folder structure
        construction_base = os.path.join(
            self.WORKSHEETS_BASE_DIR,
            self.current_worksheet_name,
            "construction"
        )
        layer_folder = os.path.join(construction_base, layer_name)

        if os.path.exists(layer_folder):
            QMessageBox.warning(
                self,
                "Name Exists",
                f"A construction layer named '{layer_name}' already exists.\n"
                "Please choose a different name."
            )
            return

        try:
            os.makedirs(layer_folder, exist_ok=False)

            # 4. Save config file
            config_data = {
                "construction_layer_name": layer_name,
                "worksheet_name": self.current_worksheet_name,
                "project_name": self.current_project_name or "None",
                "worksheet_type": self.current_worksheet_data.get("worksheet_type", "Unknown"),
                "worksheet_category": self.current_worksheet_data.get("worksheet_category", "None"),
                "construction_type": construction_type,
                "reference_layer_2d": data['reference_layer'],
                "base_lines_reference": data['base_lines_layer'],
                "created_at": datetime.now().isoformat(),
                "created_by": self.current_user,
                "material_lines": []  # will be populated later
            }

            config_path = os.path.join(layer_folder, "Construction_Layer_config.txt")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)

            # 5. Store in memory for current session
            self.current_mode = "road" if is_road else "bridge"
            self.construction_layer_info = {
                "name": layer_name,
                "type": "road" if is_road else "bridge",
                "reference_layer": data['reference_layer'],
                "base_line": data['base_lines_layer'],
                "material_lines": [],
                "folder": layer_folder
            }
            self.construction_layer_created = True
            self.current_construction_layer = layer_name  # optional: track active one

            # 6. Update UI – show bottom section
            self.bottom_section.setVisible(True)

            # 7. Hide all standard line containers
            containers_to_hide = [
                self.zero_container,
                self.surface_container,
                self.construction_container,
                self.road_surface_container,
                self.bridge_zero_container,
                self.projection_container,
                self.construction_dots_container,
                self.deck_line_container,
                # Note: material_line_container will be shown via "Add Material Line" button
            ]
            for container in containers_to_hide:
                if hasattr(self, container.__class__.__name__) or container:
                    try:
                        container.setVisible(False)
                    except:
                        pass

            # Hide standard buttons
            self.preview_button.setVisible(False)
            self.threed_map_button.setVisible(False)
            # save_button will be shown below

            # 8. Show construction-specific controls
            self.add_material_line_button.setVisible(True)
            self.save_button.setVisible(True)

            # Optional: make Save button say "Save Construction"
            self.save_button.setText("Save Construction")

            # 9. Add to layers panel
            self.add_layer_to_panel(layer_name, "2D")
            self.two_D_frame.setVisible(True)

            if hasattr(self, 'mode_banner'):
                self.mode_banner.setText("CONSTRUCTION MODE")
                self.mode_banner.setStyleSheet("""
                    QLabel {

                        font-weight: bold;
                    }
                """)
                self.mode_banner.setVisible(True)

            # 10. Feedback
            self.message_text.append(f"Construction layer '{layer_name}' ({construction_type}) created successfully!")
            self.message_text.append(f"   → Folder: {layer_folder}")
            self.message_text.append(f"   → Reference 2D Layer: {data['reference_layer']}")
            self.message_text.append(f"   → Base Line Reference: {data['base_lines_layer']}")
            self.message_text.append("You can now add material lines using the button below.")

            QMessageBox.information(
                self,
                "Construction Layer Created",
                f"<b>{layer_name}</b> ({construction_type})<br><br>"
                f"Reference Layer: {data['reference_layer']}<br>"
                f"Base Line: {data['base_lines_layer']}<br><br>"
                f"Folder created at:<br>{layer_folder}<br><br>"
                f"You can now add material lines and save the construction design."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Creation Failed",
                f"Failed to create construction layer '{layer_name}':\n\n{str(e)}"
            )
            self.message_text.append(f"Error creating construction layer: {str(e)}")

# ===================================================================================================================================
    def switch_to_construction_mode(self):
        """Update bottom section for Construction mode: hide baselines, show only Save button"""
        # Hide ALL baseline-related containers
        self.surface_container.setVisible(False)
        self.road_surface_container.setVisible(False)
        self.zero_container.setVisible(False)
        self.construction_container.setVisible(False)
        self.deck_line_container.setVisible(False)
        self.projection_container.setVisible(False)
        
        if hasattr(self, 'bridge_zero_container'):
            self.bridge_zero_container.setVisible(False)
        if hasattr(self, 'construction_dots_container'):
            self.construction_dots_container.setVisible(False)

        # Hide preview and 3D mapping buttons (not used in construction)
        self.preview_button.setVisible(False)
        self.threed_map_button.setVisible(False)

        # Show ONLY the Save button
        self.save_button.setVisible(True)

        # Hide scale section (chainage not relevant in pure construction)
        self.scale_section.setVisible(False)

        # Update message and mode banner
        self.message_text.append("Switched to Construction mode. Only Save button is available.")
        
        if hasattr(self, 'mode_banner'):
            self.mode_banner.setText("CONSTRUCTION MODE")
            self.mode_banner.setStyleSheet("""
                QLabel {

                    font-weight: bold;
                }
            """)
            self.mode_banner.setVisible(True)

        self.canvas.draw_idle()

# =======================================================================================================================================
# OPEN MATERIAL LINE DIALOG WHEN "Construction → New" IS CLICKED
    def open_material_line_dialog(self):
        """Opens the Material Line Configuration Dialog to add a new line"""
        dialog = MaterialLineDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_material_data()
            
            # Add visibility flag
            config['visible'] = True
            
            # Store config
            self.material_configs.append(config)
            
            # Create UI entry for the material line
            self.create_material_line_entry(config)
            
            # If this is the first material line, change button color to orange
            if len(self.material_configs) == 1:
                self.add_material_line_button.setStyleSheet("""
                    QPushButton {
                        background-color: #FFA500;
                        color: white;
                        border: none;
                        padding: 10px;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #FF8C00;
                    }
                    QPushButton:pressed {
                        background-color: #FF7F00;
                    }
                """)
            
            self.message_text.append("Material Line Created Successfully!")
            self.message_text.append(f"Name: {config['name']}")
            self.message_text.append(f"Initial Thickness: {config['initial_filling']} mm")
            self.message_text.append(f"Final Thickness: {config['final_compressed']} mm")
        else:
            self.message_text.append("Material Line creation cancelled.")

# =======================================================================================================================================    
# Optional: allow editing later with pencil button
    def edit_material_line(self):
        if not hasattr(self, 'material_configs') or not self.material_configs:
            QMessageBox.information(self, "No Data", "No material line has been created yet.")
            return
        dialog = MaterialLineDialog(material_data=self.material_configs[-1], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.material_configs[-1] = dialog.get_material_data()
            self.message_text.append("Material Line configuration updated.")

# =======================================================================================================================================
    def create_material_line_entry(self, material_data, edit_index=None):
        """Create or update a material line entry in the UI (below the Add button)"""
        # Create container
        container = QWidget()
        container.setFixedWidth(250)
        container.setStyleSheet("""
            QWidget {
                background-color: #FFA500;  /* Orange background */
                border: 1px solid #FF8C00;
                border-radius: 5px;
                margin: 3px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Checkbox for visibility/selection
        checkbox = QCheckBox()
        checkbox.setChecked(material_data.get('visible', True))
        checkbox.setStyleSheet("""
            QCheckBox {
                background-color: transparent;
                border: none;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        
        # Connect checkbox to toggle visibility
        checkbox.stateChanged.connect(lambda state, idx=len(self.material_items) if edit_index is None else edit_index: 
                                    self.toggle_material_line_visibility(idx, state))
        
        # Material label
        material_label = QLabel(material_data['name'])
        material_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 2px;
                font-weight: bold;
                font-size: 14px;
                color: #000000;
            }
        """)
        
        # Pencil button for editing
        pencil_button = QPushButton()
        svg_data = QByteArray()
        svg_data.append(self.PENCIL_SVG)
        renderer = QSvgRenderer(svg_data)
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter, QRectF(pixmap.rect()))
        painter.end()
        icon = QIcon(pixmap)
        pencil_button.setIcon(icon)
        pencil_button.setIconSize(QSize(20, 20))
        pencil_button.setFixedSize(28, 28)
        pencil_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                border: none;
                padding: 0px;
                margin: 0px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        pencil_button.setCursor(Qt.PointingHandCursor)
        pencil_button.clicked.connect(lambda checked, idx=len(self.material_items) if edit_index is None else edit_index: 
                                    self.edit_existing_material_line(idx))
        
        # Add widgets to layout
        layout.addWidget(checkbox)
        layout.addWidget(material_label, 1)
        layout.addWidget(pencil_button)
        
        if edit_index is not None:
            # Replace existing item
            if edit_index < len(self.material_items):
                old_container = self.material_items[edit_index]['container']
                old_container.setParent(None)
                old_container.deleteLater()
                
                self.material_items[edit_index] = {
                    'container': container,
                    'checkbox': checkbox,
                    'label': material_label,
                    'pencil_button': pencil_button,
                    'data': material_data
                }
                
                # Re-insert at correct position
                self.material_items_layout.insertWidget(edit_index, container)
        else:
            # Add new item
            new_item = {
                'container': container,
                'checkbox': checkbox,
                'label': material_label,
                'pencil_button': pencil_button,
                'data': material_data
            }
            self.material_items.append(new_item)
            self.material_items_layout.addWidget(container)
        
        # Message for new items only
        if edit_index is None:
            self.message_text.append(f"Added material line: {material_data['name']}")
# =======================================================================================================================================
    def edit_existing_material_line(self, index):
        """Edit an existing material line by index"""
        if index < 0 or index >= len(self.material_items):
            return
        
        item = self.material_items[index]
        current_data = item['data']
        
        dialog = MaterialLineDialog(material_data=current_data, parent=self)
        
        if dialog.exec_() == QDialog.Accepted:
            new_material_data = dialog.get_material_data()
            
            # Preserve visibility
            new_material_data['visible'] = current_data.get('visible', True)
            
            # Update stored config as well
            if index < len(self.material_configs):
                self.material_configs[index] = new_material_data
            
            # Update UI
            self.create_material_line_entry(new_material_data, edit_index=index)
            
            self.message_text.append(f"Updated material line: {new_material_data['name']}")

# ====================================================================================================================================
    def toggle_material_line_visibility(self, index, state):
        """Toggle visibility of a material line"""
        if 0 <= index < len(self.material_items):
            item = self.material_items[index]
            is_visible = state == Qt.Checked
            item['data']['visible'] = is_visible
            if index < len(self.material_configs):
                self.material_configs[index]['visible'] = is_visible
            
            if is_visible:
                self.message_text.append(f"Showing material line: {item['data']['name']}")
            else:
                self.message_text.append(f"Hiding material line: {item['data']['name']}")

# =======================================================================================================================================
    def save_material_data(self):
        """Save all material lines"""
        if hasattr(self, 'material_items') and self.material_items:
            self.message_text.append("<b>Material lines saved successfully!</b>")
            self.message_text.append(f"Total: {len(self.material_items)} material line(s)\n")
            for i, item in enumerate(self.material_items):
                data = item['data']
                visibility = "Visible" if data.get('visible', True) else "Hidden"
                self.message_text.append(f"<b>{i+1}. {data['name']}</b> [{visibility}]")
                self.message_text.append(f"   • Initial Thickness: {data['initial_filling']} mm")
                self.message_text.append(f"   • Final Thickness: {data['final_compressed']} mm")
                ref = data.get('ref_layer') or data.get('ref_line') or 'None'
                self.message_text.append(f"   • Reference: {ref}")
                if data.get('description'):
                    self.message_text.append(f"   • Description: {data['description']}")
                self.message_text.append("")
        else:
            self.message_text.append("No material lines to save.")

# ===========================================================================================================================================================
    def open_existing_worksheet(self):
        dialog = ExistingWorksheetDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return

        data = dialog.get_selected_data()
        if not data:
            QMessageBox.warning(self, "Invalid Selection", "No valid worksheet/layer selected.")
            return

        # Extract data
        config = data["worksheet_data"]
        worksheet_name = config.get("worksheet_name")
        layer_name = data["layer_name"]
        subfolder_type = data["subfolder_type"]  # "designs", "measurements", "construction"
        full_layer_path = data["full_layer_path"]

        if not os.path.exists(full_layer_path):
            QMessageBox.critical(self, "Path Error", f"Layer folder not found:\n{full_layer_path}")
            return

        # Update application state
        self.current_worksheet_name = worksheet_name
        self.current_project_name = config.get("project_name")
        self.current_worksheet_data = config
        self.current_layer_name = layer_name

        # Update UI display (top banner)
        self.display_current_worksheet(config)

        dimension = config.get("dimension", "2D")
        category = config.get("worksheet_category", "None")

        # Show correct dimension panels
        self.three_D_frame.setVisible(dimension == "3D")
        self.two_D_frame.setVisible(dimension == "2D")

        # Show bottom section for Road/Bridge
        self.bottom_section.setVisible(category in ["Road", "Bridge"])

        # Reset everything first
        self.reset_all()
        self.clear_baseline_planes()

        # === STEP 1: Load zero line ===
        zero_loaded = self.load_zero_line_from_layer(full_layer_path)

        if not zero_loaded:
            QMessageBox.warning(self, "Zero Line Missing",
                                "No zero_line_config.json found in the layer.\n"
                                "Zero line is required for correct baseline mapping.\n"
                                "You can set it manually later.")

        # === STEP 2: Load all baselines ===
        loaded_baselines = self.load_all_baselines_from_layer(full_layer_path)

        # === STEP 3: Redraw baselines on 2D graph + check checkboxes ===
        for ltype in loaded_baselines:
            checkbox = {
                'surface': self.surface_baseline,
                'construction': self.construction_line,
                'road_surface': self.road_surface_line,
                'deck_line': self.deck_line,
                'projection_line': self.projection_line,
            }.get(ltype)

            if checkbox:
                checkbox.setChecked(True)

            self.redraw_baseline_on_graph(ltype)

        # === STEP 4: Regenerate 3D planes ===
        if self.zero_line_set and loaded_baselines:
            last_width = 10.0
            if loaded_baselines:
                first_ltype = list(loaded_baselines.keys())[0]
                baseline_data = loaded_baselines[first_ltype]
                last_width = baseline_data.get("width_meters", 10.0)

            self.last_plane_width = last_width
            self.map_baselines_to_3d_planes_from_data(loaded_baselines, last_width)

        # === STEP 5: Make sure the 2D graph section is VISIBLE ===
        self.show_graph_section(category)

        # === STEP 6: Show correct baseline containers ===
        self.surface_container.setVisible(False)
        self.construction_container.setVisible(False)
        self.road_surface_container.setVisible(False)
        self.zero_container.setVisible(False)
        self.deck_line_container.setVisible(False)
        self.projection_container.setVisible(False)
        self.construction_dots_container.setVisible(False)
        if hasattr(self, 'bridge_zero_container'):
            self.bridge_zero_container.setVisible(False)

        if category == "Road":
            self.surface_container.setVisible(True)
            self.construction_container.setVisible(True)
            self.road_surface_container.setVisible(True)
            self.zero_container.setVisible(True)
        elif category == "Bridge":
            self.deck_line_container.setVisible(True)
            self.projection_container.setVisible(True)
            self.construction_dots_container.setVisible(True)
            if hasattr(self, 'bridge_zero_container'):
                self.bridge_zero_container.setVisible(True)

        # Show action buttons
        self.preview_button.setVisible(True)
        self.threed_map_button.setVisible(True)
        self.save_button.setVisible(True)

        self.add_material_line_button.setVisible(False)

        # Add layer to left panel
        self.add_layer_to_panel(layer_name, dimension)

        # Auto-load point cloud if linked
        pc_file = config.get("point_cloud_file")
        if pc_file and os.path.exists(pc_file):
            self.load_point_cloud_from_path(pc_file)

        # Final feedback
        self.message_text.append(f"Successfully opened existing worksheet:")
        self.message_text.append(f"   → Worksheet: {worksheet_name}")
        self.message_text.append(f"   → Section: {subfolder_type}")
        self.message_text.append(f"   → Layer: {layer_name}")
        self.message_text.append(f"   → Baselines loaded: {len(loaded_baselines)} type(s)")
        self.message_text.append(f"   → Zero line: {'Loaded' if zero_loaded else 'Not found'}")
        self.message_text.append("   → 2D Graph section is now visible with all baselines.")

        QMessageBox.information(self, "Worksheet Opened",
                                f"<b>{worksheet_name}</b><br><br>"
                                f"Layer: <i>{layer_name}</i> ({subfolder_type})<br>"
                                f"Baselines: {len(loaded_baselines)} type(s) loaded<br>"
                                f"Zero Line: {'Yes' if zero_loaded else 'No'}<br><br>"
                                f"2D cross-section graph is now visible with all drawn lines.")

        # Final refresh
        self.canvas.draw_idle()
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.GetRenderWindow().Render()

# ===========================================================================================================================================================
    def show_graph_section(self, category):
        """
        Ensures the 2D cross-section graph and baseline controls are fully visible
        when opening an existing worksheet.
        """
        # 1. Show the entire bottom section (contains line section + graph)
        if hasattr(self, 'bottom_section'):
            self.bottom_section.setVisible(True)

        # 2. Show the collapsible line section (checkboxes)
        if hasattr(self, 'line_section'):
            self.line_section.setVisible(True)

        # 3. Expand the line section if it's collapsed
        if hasattr(self, 'line_content_widget') and not self.line_content_widget.isVisible():
            self.line_content_widget.show()
            self.collapse_button.setText("◀")
            self.collapse_button.setToolTip("Close Line Section")
            self.undo_button.show()
            self.redo_button.show()
            self.line_section.setMaximumWidth(350)
            self.line_section.setFixedWidth(350)

        # 4. Show scale section (chainage slider + scale bar)
        if hasattr(self, 'scale_section'):
            self.scale_section.setVisible(True)

        # 5. Show relevant baseline containers based on category
        if category == "Road":
            self.surface_container.setVisible(True)
            self.construction_container.setVisible(True)
            self.road_surface_container.setVisible(True)
            self.zero_container.setVisible(True)
        elif category == "Bridge":
            self.deck_line_container.setVisible(True)
            self.projection_container.setVisible(True)
            self.construction_dots_container.setVisible(True)
            if hasattr(self, 'bridge_zero_container'):
                self.bridge_zero_container.setVisible(True)

        # 6. Show action buttons
        self.preview_button.setVisible(True)
        self.threed_map_button.setVisible(True)
        self.save_button.setVisible(True)

        # 7. Force redraw of matplotlib canvas
        if hasattr(self, 'canvas'):
            self.canvas.draw_idle()

        # 8. Force layout update
        QApplication.processEvents()
    
# ===========================================================================================================================================================
    def load_zero_line_from_layer(self, layer_path):
        """Load zero_line_config.json from the given layer folder"""
        json_path = os.path.join(layer_path, "zero_line_config.json")
        if not os.path.exists(json_path):
            return False

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.zero_start_point = np.array(config["point1"]["coordinates"])
            self.zero_end_point = np.array(config["point2"]["coordinates"])
            self.zero_start_z = config["reference_elevation_z"]
            self.total_distance = config["total_length_m"]
            self.original_total_distance = self.total_distance
            self.zero_interval = config.get("interval_m", 20.0)
            self.zero_start_km = config["point1"].get("km")
            self.zero_end_km = config["point2"].get("km")

            self.zero_line_set = True

            # Redraw zero line on graph
            if hasattr(self, 'zero_graph_line') and self.zero_graph_line:
                self.zero_graph_line.remove()
            self.zero_graph_line, = self.ax.plot([0, self.total_distance], [0, 0],
                                                color='purple', linewidth=3)

            # Update ticks and scale
            self.update_chainage_ticks()
            if hasattr(self, 'scale_section'):
                self.scale_section.setVisible(True)

            return True
        except Exception as e:
            self.message_text.append(f"Error loading zero line config: {str(e)}")
            return False

# ===========================================================================================================================================================
    def load_all_baselines_from_layer(self, layer_path):
        """Load all *_baseline.json files from layer folder and return dict of loaded data"""
        loaded = {}
        possible_files = [
            "surface_baseline.json",
            "construction_baseline.json",
            "road_surface_baseline.json",
            "deck_line_baseline.json",
            "projection_line_baseline.json",
            "material_baseline.json"
        ]

        key_map = {
            "surface_baseline.json": "surface",
            "construction_baseline.json": "construction",
            "road_surface_baseline.json": "road_surface",
            "deck_line_baseline.json": "deck_line",
            "projection_line_baseline.json": "projection_line",
            "material_baseline.json": "material",
        }

        for filename in possible_files:
            filepath = os.path.join(layer_path, filename)
            if not os.path.exists(filepath):
                continue

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                ltype = key_map[filename]
                loaded[ltype] = data

                # Store polylines in memory
                polylines_2d = []
                for poly in data.get("polylines", []):
                    poly_2d = []
                    for pt in poly["points"]:
                        poly_2d.append((pt["chainage_m"], pt["relative_elevation_m"]))
                    if len(poly_2d) >= 2:
                        polylines_2d.append(poly_2d)

                self.line_types[ltype]['polylines'] = polylines_2d

            except Exception as e:
                self.message_text.append(f"Error loading {filename}: {str(e)}")

        return loaded

# ===========================================================================================================================================================
    def redraw_baseline_on_graph(self, ltype):
        """Redraw a loaded baseline on the 2D matplotlib graph"""
        color = self.line_types[ltype]['color']
        for poly_2d in self.line_types[ltype]['polylines']:
            if len(poly_2d) < 2:
                continue
            xs = [p[0] for p in poly_2d]
            ys = [p[1] for p in poly_2d]
            line, = self.ax.plot(xs, ys, color=color, linewidth=2.5)
            self.line_types[ltype]['artists'].append(line)

        self.canvas.draw_idle()

# ===========================================================================================================================================================
    def map_baselines_to_3d_planes_from_data(self, loaded_baselines, width):
        """Regenerate 3D planes from loaded baseline data (same logic as map_baselines_to_3d_planes but from dict)"""
        if not self.zero_line_set:
            return

        half_width = width / 2.0
        zero_dir_vec = self.zero_end_point - self.zero_start_point
        zero_length = self.total_distance
        ref_z = self.zero_start_z

        for ltype, baseline_data in loaded_baselines.items():
            rgba = self.plane_colors.get(ltype, (0.5, 0.5, 0.5, 0.4))
            color_rgb = rgba[:3]
            opacity = rgba[3]

            for poly in baseline_data.get("polylines", []):
                points_3d = poly["points"]
                if len(points_3d) < 2:
                    continue

                for i in range(len(points_3d) - 1):
                    pt1 = points_3d[i]
                    pt2 = points_3d[i + 1]

                    center1 = np.array(pt1["world_coordinates"])
                    center2 = np.array(pt2["world_coordinates"])

                    seg_dir = center2 - center1
                    seg_len = np.linalg.norm(seg_dir)
                    if seg_len < 1e-6:
                        continue
                    seg_unit = seg_dir / seg_len

                    horiz = np.array([seg_unit[0], seg_unit[1], 0.0])
                    hlen = np.linalg.norm(horiz)
                    if hlen < 1e-6:
                        zero_unit = zero_dir_vec / np.linalg.norm(zero_dir_vec)
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

                    self.renderer.AddActor(actor)
                    self.baseline_plane_actors.append(actor)

        self.vtk_widget.GetRenderWindow().Render()
# =======================================================================================================================================
    def load_point_cloud_files(self, file_list):
        """Load multiple point cloud files (merge or first one) - currently loads first file with progress bar"""
        if not file_list:
            return

        # For simplicity, load first file
        first_file = file_list[0]
        file_path = first_file  # For consistency with the single-load method

        # Store the loaded file path and name (same as single load)
        self.loaded_file_path = file_path
        self.loaded_file_name = os.path.splitext(os.path.basename(file_path))[0]

        try:
            # Show progress bar with file info
            self.show_progress_bar(file_path)
            self.update_progress(10, "Starting file loading...")

            self.update_progress(30, "Loading point cloud data...")
            self.point_cloud = o3d.io.read_point_cloud(file_path)

            if self.point_cloud.is_empty():
                raise ValueError("Point cloud is empty!")

            self.update_progress(50, "Converting to VTK format...")

            # Display in VTK
            points = np.asarray(self.point_cloud.points)
            colors = np.asarray(self.point_cloud.colors) if self.point_cloud.has_colors() else None

            poly_data = vtk.vtkPolyData()
            vtk_points = vtk.vtkPoints()
            vertices = vtk.vtkCellArray()

            for i, pt in enumerate(points):
                vtk_points.InsertNextPoint(pt)
                vertex = vtk.vtkVertex()
                vertex.GetPointIds().SetId(0, i)
                vertices.InsertNextCell(vertex)

            poly_data.SetPoints(vtk_points)
            poly_data.SetVerts(vertices)

            if colors is not None:
                self.update_progress(70, "Processing colors...")
                vtk_colors = vtk.vtkUnsignedCharArray()
                vtk_colors.SetNumberOfComponents(3)
                vtk_colors.SetName("Colors")
                for c in (colors * 255).astype(np.uint8):
                    vtk_colors.InsertNextTuple(c)
                poly_data.GetPointData().SetScalars(vtk_colors)
            else:
                self.update_progress(70, "Preparing visualization...")

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(poly_data)

            self.update_progress(90, "Creating visualization...")

            if self.point_cloud_actor:
                self.renderer.RemoveActor(self.point_cloud_actor)

            self.point_cloud_actor = vtk.vtkActor()
            self.point_cloud_actor.SetMapper(mapper)
            self.point_cloud_actor.GetProperty().SetPointSize(2)

            self.renderer.AddActor(self.point_cloud_actor)
            self.renderer.ResetCamera()
            self.vtk_widget.GetRenderWindow().Render()

            self.update_progress(100, "Loading complete!")
            QTimer.singleShot(500, self.hide_progress_bar)

            self.message_text.append(f"Successfully loaded point cloud: {os.path.basename(file_path)}")

        except Exception as e:
            self.hide_progress_bar()
            self.message_text.append(f"Failed to load point cloud '{os.path.basename(file_path)}': {str(e)}")
            QMessageBox.warning(self, "Load Failed", f"Could not load point cloud:\n{file_path}\n\nError: {str(e)}")

# =======================================================================================================================================
    def show_help_dialog(self):
        """Open the Help Dialog when Help button is clicked"""
        dialog = HelpDialog(self)
        dialog.exec_()  # Modal – blocks until closed

# =======================================================================================================================================
    def save_current_lines_state(self):
        """Save the current graph lines state when switching between modes"""
        if self.current_mode == 'road':
            # Save road lines
            self.road_lines_data = {
                'construction': {
                    'polylines': self.line_types['construction']['polylines'].copy(),
                    'artists': []  # Don't save artist references directly
                },
                'surface': {
                    'polylines': self.line_types['surface']['polylines'].copy(),
                    'artists': []
                },
                'road_surface': {
                    'polylines': self.line_types['road_surface']['polylines'].copy(),
                    'artists': []
                },
                'zero': {
                    'polylines': self.line_types['zero']['polylines'].copy(),
                    'artists': []
                }
            }
            self.message_text.append("Road lines state saved")
            
        elif self.current_mode == 'bridge':
            # Save bridge lines
            self.bridge_lines_data = {
                'deck_line': {
                    'polylines': self.line_types['deck_line']['polylines'].copy(),
                    'artists': []
                },
                'projection_line': {
                    'polylines': self.line_types['projection_line']['polylines'].copy(),
                    'artists': []
                },
                'construction_dots': {
                    'polylines': self.line_types['construction_dots']['polylines'].copy(),
                    'artists': []
                },
                'zero': {
                    'polylines': self.line_types['zero']['polylines'].copy(),
                    'artists': []
                }
            }
            self.message_text.append("Bridge lines state saved")

# =======================================================================================================================================
    def restore_saved_lines_state(self, mode):
        """Restore saved graph lines for a specific mode"""
        if mode == 'road' and self.road_lines_data:
            # Clear current lines first
            self.clear_graph_for_mode(mode)
            
            # Restore road lines
            for line_type in ['construction', 'surface', 'road_surface', 'zero']:
                if line_type in self.road_lines_data:
                    self.line_types[line_type]['polylines'] = self.road_lines_data[line_type]['polylines'].copy()
                    
                    # Recreate artists for the polylines
                    for polyline in self.line_types[line_type]['polylines']:
                        if len(polyline) > 1:
                            xs = [p[0] for p in polyline]
                            ys = [p[1] for p in polyline]
                            color = self.line_types[line_type]['color']
                            artist, = self.ax.plot(xs, ys, color=color, linewidth=2, marker='o', markersize=5)
                            self.line_types[line_type]['artists'].append(artist)
                            
                            # Add to all_graph_lines for undo/redo
                            self.all_graph_lines.append((line_type, polyline.copy(), artist, None))
            
            self.message_text.append("Restored saved road lines")
            
        elif mode == 'bridge' and self.bridge_lines_data:
            # Clear current lines first
            self.clear_graph_for_mode(mode)
            
            # Restore bridge lines
            for line_type in ['deck_line', 'projection_line', 'construction_dots', 'zero']:
                if line_type in self.bridge_lines_data:
                    self.line_types[line_type]['polylines'] = self.bridge_lines_data[line_type]['polylines'].copy()
                    
                    # Recreate artists for the polylines
                    for polyline in self.line_types[line_type]['polylines']:
                        if len(polyline) > 1:
                            xs = [p[0] for p in polyline]
                            ys = [p[1] for p in polyline]
                            color = self.line_types[line_type]['color']
                            artist, = self.ax.plot(xs, ys, color=color, linewidth=2, marker='o', markersize=5)
                            self.line_types[line_type]['artists'].append(artist)
                            
                            # Special handling for construction dots labels
                            if line_type == 'construction_dots':
                                for i, (x, y) in enumerate(polyline, 1):
                                    label = self.add_point_label(x, y, i, line_type)
                                    if label:
                                        self.point_labels.append(label)
                            
                            # Add to all_graph_lines for undo/redo
                            self.all_graph_lines.append((line_type, polyline.copy(), artist, None))
            
            self.message_text.append("Restored saved bridge lines")
        
        # Redraw canvas
        self.canvas.draw()
        self.figure.tight_layout()

# =======================================================================================================================================
    def clear_graph_for_switch(self):
        """Clear graph when switching between road and bridge modes"""
        # Clear current drawing session
        self.current_points = []
        if self.current_artist is not None:
            try:
                self.current_artist.remove()
            except:
                pass
            self.current_artist = None
        self.current_redo_points = []
        
        # Clear current point labels
        for label in self.current_point_labels:
            try:
                if label in self.ax.texts:
                    label.remove()
            except:
                pass
        self.current_point_labels = []
        
        # Disconnect drawing events if connected
        if self.cid_click is not None:
            self.canvas.mpl_disconnect(self.cid_click)
            self.cid_click = None
        if self.cid_key is not None:
            self.canvas.mpl_disconnect(self.cid_key)
            self.cid_key = None
        
        # Uncheck all checkboxes
        self.construction_line.setChecked(False)
        self.surface_baseline.setChecked(False)
        if hasattr(self, 'road_surface_line'):
            self.road_surface_line.setChecked(False)
        if hasattr(self, 'construction_dots_line'):
            self.construction_dots_line.setChecked(False)
        if hasattr(self, 'deck_line'):
            self.deck_line.setChecked(False)
        if hasattr(self, 'projection_line'):
            self.projection_line.setChecked(False)
        
        # Reset active line type
        self.active_line_type = None
        
        self.message_text.append("Graph cleared for mode switch")

# =======================================================================================================================================
    def clear_graph_for_mode(self, mode):
        """Clear graph lines for specific mode only"""
        if mode == 'road':
            # Clear road-specific lines
            for line_type in ['construction', 'surface', 'road_surface']:
                self.clear_line_type(line_type)
        elif mode == 'bridge':
            # Clear bridge-specific lines
            for line_type in ['deck_line', 'projection_line', 'construction_dots']:
                self.clear_line_type(line_type)

# =======================================================================================================================================
    def clear_line_type(self, line_type):
        """Clear a specific line type from the graph"""
        if line_type in self.line_types:
            # Remove artists
            for artist in self.line_types[line_type]['artists']:
                try:
                    if artist in self.ax.lines or artist in self.ax.collections:
                        artist.remove()
                except:
                    pass
            
            # Clear the lists
            self.line_types[line_type]['artists'] = []
            self.line_types[line_type]['polylines'] = []
            
            # Remove from all_graph_lines
            new_all_graph_lines = []
            for item in self.all_graph_lines:
                lt, points, artist, ann = item
                if lt != line_type:
                    new_all_graph_lines.append(item)
                else:
                    # Remove the annotation if it exists
                    if ann:
                        try:
                            ann.remove()
                        except:
                            pass
            
            self.all_graph_lines = new_all_graph_lines
            
            # For construction dots, also remove labels
            if line_type == 'construction_dots':
                texts_to_remove = []
                for text in self.ax.texts:
                    if hasattr(text, 'point_data') and text.point_data.get('line_type') == 'construction_dots':
                        texts_to_remove.append(text)
                
                for text in texts_to_remove:
                    try:
                        text.remove()
                    except:
                        pass
        
# =======================================================================================================================================
# ON CHECKBOX CHANGED 
    def on_checkbox_changed(self, state, line_type):
        if state == Qt.Checked:
            if line_type == 'construction_dots':
                # Check if bridge baseline is active
                self.active_line_type = line_type
                
                # Set up event listeners if not already set up
                if self.cid_click is None:
                    self.cid_click = self.canvas.mpl_connect('button_press_event', self.on_draw_click)
                    self.cid_key = self.canvas.mpl_connect('key_press_event', self.on_key_press)
                
                self.current_points = []
                self.current_artist = None
                self.current_redo_points = []
                
                self.message_text.append("Construction Dots Mode: Click on graph to add construction points")
                self.message_text.append("Double-click to complete the line")
                self.message_text.append("Click on the P1, P2 labels at the top to configure each point")
                
                self.canvas.draw()
                self.figure.tight_layout()
                return
            
            if line_type == 'zero':
                # Zero line handling remains the same
                if self.zero_line_set:
                    if self.zero_start_actor:
                        self.zero_start_actor.SetVisibility(True)
                    if self.zero_end_actor:
                        self.zero_end_actor.SetVisibility(True)
                    if self.zero_line_actor:
                        self.zero_line_actor.SetVisibility(True)
                    self.total_distance = self.zero_physical_dist
                    self.ax.set_xlim(0, self.total_distance)
                    self.update_chainage_ticks()

                    # Show scale section if zero line is set
                    if self.scale_section:
                        self.scale_section.setVisible(True)
                            
                    if self.zero_graph_line:
                        self.zero_graph_line.set_visible(True)
                    self.canvas.draw()
                    self.figure.tight_layout()
                    self.volume_slider.setValue(0)
                    self.update_scale_marker()
                    return
                else:
                    self.drawing_zero_line = True
                    self.zero_points = []
                    self.temp_zero_actors = []
                    self.message_text.append("Click two points on the point cloud to set zero line start and end.")
                    return
            

            # First, if there's an ongoing line of different type, finish it
            if self.active_line_type and self.active_line_type != line_type and self.current_points:
                self.message_text.append(f"Finishing {self.active_line_type.replace('_', ' ').title()} before switching to {line_type.replace('_', ' ').title()}")
                self.finish_current_polyline()
            
            self.active_line_type = line_type
            if self.cid_click is None:
                self.cid_click = self.canvas.mpl_connect('button_press_event', self.on_draw_click)
                self.cid_key = self.canvas.mpl_connect('key_press_event', self.on_key_press)
            
            self.current_points = []
            self.current_artist = None
            self.current_redo_points = []
            
            # Add instruction message
            line_names = {
                'surface': 'Surface Line',
                'construction': 'Construction Line',
                'road_surface': 'Road Surface Line',
                'deck_line': 'Deck Line',
                'projection_line': 'Projection Line'
            }
            if line_type in line_names:
                self.message_text.append(f"{line_names[line_type]} Mode: Click to add points, double-click to complete")
            
            self.canvas.draw()
            self.figure.tight_layout()
        
        else:  # State == Qt.Unchecked
            if line_type == 'zero':
                if self.zero_line_set:
                    if self.zero_start_actor:
                        self.zero_start_actor.SetVisibility(False)
                    if self.zero_end_actor:
                        self.zero_end_actor.SetVisibility(False)
                    if self.zero_line_actor:
                        self.zero_line_actor.SetVisibility(False)
                    if self.zero_graph_line:
                        self.zero_graph_line.set_visible(False)
                            
                    # Hide scale section when zero line is unchecked
                    if hasattr(self, 'scale_section'):
                        self.scale_section.setVisible(False)
                    
                    # Reset scale section to default format
                    if hasattr(self, 'scale_ax') and self.scale_ax is not None:
                        self.scale_ax.set_xticks(np.arange(0, self.total_distance + 1, 5))
                        self.scale_ax.set_xticklabels([f"{x:.0f}" for x in np.arange(0, self.total_distance + 1, 5)])
                        self.scale_canvas.draw()
                return
            
            # For other line types when unchecked
            if self.active_line_type == line_type and self.current_points:
                self.message_text.append(f"Finishing {line_type.replace('_', ' ').title()} before unchecking")
                self.finish_current_polyline()
            
            # Only disconnect if no non-zero checkboxes are checked
            if not (self.construction_line.isChecked() or self.surface_baseline.isChecked() or 
                    self.road_surface_line.isChecked() or self.deck_line.isChecked() or 
                    self.projection_line.isChecked() or self.construction_dots_line.isChecked()):
                
                if self.cid_click is not None:
                    self.canvas.mpl_disconnect(self.cid_click)
                    self.cid_click = None
                if self.cid_key is not None:
                    self.canvas.mpl_disconnect(self.cid_key)
                    self.cid_key = None
                
                self.active_line_type = None
                self.current_points = []
                if self.current_artist is not None:
                    self.current_artist.remove()
                    self.current_artist = None
                
                self.canvas.draw()
                self.figure.tight_layout()

# =======================================================================================================================================
# UPDATE CHAINAGE TICKS ON GRAPHS
    def update_chainage_ticks(self):
        """Update both the top Chainage Scale and the main graph X-axis with KM+interval ticks."""
        if not (self.zero_line_set and hasattr(self, 'zero_interval') and self.zero_interval and
                hasattr(self, 'zero_start_km') and self.zero_start_km is not None):
            # Fallback to simple distance if no proper chainage config
            if hasattr(self, 'scale_ax') and self.scale_ax:
                self.scale_ax.clear()
                self.scale_ax.axis('off')
                self.scale_canvas.draw_idle() if hasattr(self, 'scale_canvas') else None
            self.ax.set_xlabel('Distance (m)')
            self.ax.set_xticks(np.linspace(0, self.total_distance, 10))
            self.ax.set_xticklabels([f"{int(x)}m" for x in np.linspace(0, self.total_distance + 1, 10)])
            self.canvas.draw_idle()
            return

        # Calculate tick positions
        num_intervals = int(self.total_distance / self.zero_interval)
        tick_positions = [i * self.zero_interval for i in range(num_intervals + 1)]
        tick_labels = []
        current_km = self.zero_start_km
        remaining = self.total_distance
        for i in range(num_intervals + 1):
            interval_value = i * self.zero_interval
            if interval_value >= 1000:
                additional_km = int(interval_value // 1000)
                current_km += additional_km
                interval_value %= 1000
            label = f"{current_km}+{int(interval_value):03d}"
            tick_labels.append(label)

        # === UPDATE TOP CHAINAGE SCALE (Orange bar) ===
        if hasattr(self, 'scale_ax') and self.scale_ax:
            self.scale_ax.clear()
            self.scale_ax.plot([0, self.total_distance], [0, 0], color='black', linewidth=3)
            self.scale_ax.set_xlim(0, self.total_distance)
            self.scale_ax.set_ylim(-0.1, 1.2)
            self.scale_ax.set_yticks([])
            self.scale_ax.set_xticks(tick_positions)
            self.scale_ax.set_xticklabels(tick_labels, rotation=15, ha='right', fontsize=8)
            self.scale_ax.set_title("Chainage Scale", fontsize=10, pad=10, color='#D35400')
            self.scale_ax.spines['bottom'].set_visible(True)
            self.scale_ax.spines['top'].set_visible(False)
            self.scale_ax.spines['left'].set_visible(False)
            self.scale_ax.spines['right'].set_visible(False)
            self.scale_ax.tick_params(axis='x', which='both', length=8, width=1, colors='black')
            self.scale_ax.set_facecolor('#FFE5B4')  # Light orange background for better visibility
            if hasattr(self, 'scale_canvas'):
                self.scale_canvas.draw_idle()

        # === UPDATE MAIN GRAPH X-AXIS ===
        self.ax.set_xlim(0, self.total_distance)
        self.ax.set_xticks(tick_positions)
        self.ax.set_xticklabels(tick_labels, rotation=15, ha='right', fontsize=8)
        self.ax.set_xlabel('Chainage (KM + Interval)', fontsize=10, labelpad=10)
        self.ax.grid(True, axis='x', linestyle='--', alpha=0.6, linewidth=1.2)

        # Improve Y-axis readability
        self.ax.tick_params(axis='y', labelsize=10)
        self.ax.set_ylabel('Relative Elevation (m)', fontsize=10, labelpad=10)

        self.canvas.draw_idle()

# =======================================================================================================================================
# UPDATE SCALE MARKER BASED ON SLIDER
    def update_scale_marker(self):
        """Update red marker and chainage label when volume slider moves"""
        if not self.zero_line_set or not hasattr(self, 'scale_ax'):
            return

        value = self.volume_slider.value()
        pos = value / 100.0 * self.total_distance

        # Update vertical red line
        self.scale_marker.set_data([pos, pos], [0, 1])

        # === SAFE CHAINAGE LABEL ===
        interval = int(self.zero_interval)
        start_km = getattr(self, 'zero_start_km', 0) if hasattr(self, 'zero_start_km') else 0

        # Find nearest interval mark
        interval_number = int(round(pos / interval))
        interval_value_meters = interval_number * interval

        marker_label = f"Chainage: {start_km}+{interval_value_meters:03d}"

        # Remove old label
        if hasattr(self, 'scale_marker_label'):
            try:
                self.scale_marker_label.remove()
            except:
                pass

        # Add new label
        self.scale_marker_label = self.scale_ax.text(
            pos, 1.1, marker_label,
            color='red', fontsize=10, fontweight='bold',
            ha='center', va='bottom',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="red", alpha=0.9, linewidth=1)
        )

        # Update bottom indicator line
        if not hasattr(self, 'scale_marker_bottom'):
            self.scale_marker_bottom, = self.scale_ax.plot([pos, pos], [0, 0.1], color='red', linewidth=2)
        else:
            self.scale_marker_bottom.set_data([pos, pos], [0, 0.1])

        self.scale_canvas.draw()

# =======================================================================================================================================
    def update_main_graph_marker(self, slider_value):
        """Update orange vertical marker on main 2D graph"""
        if not self.zero_line_set:
            return

        pos = slider_value / 100.0 * self.total_distance

        # Update vertical line
        if not hasattr(self, 'main_graph_marker'):
            self.main_graph_marker = self.ax.axvline(x=pos, color='orange',
                                                     linestyle='--', alpha=0.7, linewidth=2)
        else:
            self.main_graph_marker.set_xdata([pos, pos])

        # Get safe chainage label
        chainage_label = self.get_chainage_label(pos)

        # Update label
        if not hasattr(self, 'main_graph_marker_label'):
            self.main_graph_marker_label = self.ax.text(
                pos, self.ax.get_ylim()[1] * 0.95,
                f"← Chainage: {chainage_label}",
                color='orange', fontweight='bold', ha='right',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8)
            )
        else:
            self.main_graph_marker_label.set_position((pos, self.ax.get_ylim()[1] * 0.95))
            self.main_graph_marker_label.set_text(f"← Chainage: {chainage_label}")

        self.canvas.draw_idle()

# =======================================================================================================================================
    def on_graph_scrolled(self):
        """Update slider position when graph is manually scrolled"""
        if not hasattr(self, 'graph_horizontal_scrollbar') or not self.volume_slider:
            return
        
        scrollbar = self.graph_horizontal_scrollbar
        slider = self.volume_slider
        
        # Only update if slider is not being dragged
        if not slider.isSliderDown():
            scroll_value = scrollbar.value()
            scroll_max = scrollbar.maximum()
            
            if scroll_max > 0:
                slider_value = int((scroll_value / scroll_max) * slider.maximum())
                slider.blockSignals(True)  # Temporarily block signals to prevent loop
                slider.setValue(slider_value)
                slider.blockSignals(False)
                
                # Update the visual elements
                if self.zero_line_set:
                    self.update_scale_marker()
                    self.update_main_graph_marker(slider_value)

# =======================================================================================================================================
    def complete_line_with_double_click(self):
        """Complete the current line when double-clicked"""
        if self.active_line_type and len(self.current_points) > 1:
            self.finish_current_polyline()
            self.message_text.append(f"{self.active_line_type.replace('_', ' ').title()} completed with double-click")
        elif self.active_line_type and len(self.current_points) == 1:
            self.message_text.append("Need at least 2 points to create a line. Add more points before double-clicking.")              

# =======================================================================================================================================   
    def on_key_press(self, event):
        if event.key == 'escape' and self.active_line_type and self.current_points:
            self.finish_current_polyline()
            self.message_text.append(f"{self.active_line_type.replace('_', ' ').title()} completed with Escape key")

# =======================================================================================================================================
# Add a helper method to format chainage labels:
    def get_chainage_label(self, position):
        """Return formatted chainage string like '101+020' for any position"""
        if not self.zero_line_set or not hasattr(self, 'zero_interval') or self.zero_interval <= 0:
            return f"{position:.1f}m"

        interval = int(self.zero_interval)
        start_km = getattr(self, 'zero_start_km', 0) if hasattr(self, 'zero_start_km') else 0

        interval_number = int(round(position / interval))
        interval_value_meters = interval_number * interval

        return f"{start_km}+{interval_value_meters:03d}"

# =======================================================================================================================================
# UPDATE ZERO ACTORS
    def update_zero_actors(self):
        if not self.zero_line_set:
            return
        # Remove old actors
        if self.zero_start_actor:
            self.renderer.RemoveActor(self.zero_start_actor)
            if self.zero_start_actor in self.measurement_actors:
                self.measurement_actors.remove(self.zero_start_actor)
        if self.zero_end_actor:
            self.renderer.RemoveActor(self.zero_end_actor)
            if self.zero_end_actor in self.measurement_actors:
                self.measurement_actors.remove(self.zero_end_actor)
        if self.zero_line_actor:
            self.renderer.RemoveActor(self.zero_line_actor)
            if self.zero_line_actor in self.measurement_actors:
                self.measurement_actors.remove(self.zero_line_actor)
        
        # Recreate actors
        self.zero_start_actor = self.add_sphere_marker(self.zero_start_point, "Start", color="purple")
        self.zero_end_actor = self.add_sphere_marker(self.zero_end_point, "End", color="purple")
        self.zero_line_actor = self.add_line_between_points(self.zero_start_point, self.zero_end_point, "purple", show_label=False)
        self.zero_physical_dist = np.linalg.norm(self.zero_end_point - self.zero_start_point)
        self.total_distance = self.zero_physical_dist
        self.zero_start_z = self.zero_start_point[2] # Set reference zero elevation to Point_1 Z
        
        # Update both main graph and scale graph
        self.ax.set_xlim(0, self.total_distance)
        self.scale_ax.set_xlim(0, self.total_distance)
        
        if self.zero_graph_line:
            self.zero_graph_line.remove()
        self.zero_graph_line, = self.ax.plot([0, self.total_distance], [0, 0], color='purple', linewidth=3)
        
        # Update scale line
        self.scale_line.set_data([0, self.total_distance], [0.5, 0.5])
        
        # Update ticks for both graphs
        self.update_chainage_ticks()
        self.update_scale_ticks()  # Add this line
        
        self.volume_slider.setValue(0)
        self.scale_marker.set_data([0, 0], [0, 1])
        self.scale_canvas.draw()
        self.canvas.draw()
        self.figure.tight_layout()
        self.vtk_widget.GetRenderWindow().Render()

# =======================================================================================================================================
# In the update_scale_ticks method, improve the tick labels:
    def update_scale_ticks(self):
        """Rebuild the chainage scale below the 3D view with correct KM+Interval labels"""
        if not self.zero_line_set or not hasattr(self, 'zero_interval') or self.zero_interval <= 0:
            return

        self.scale_ax.clear()

        interval = int(self.zero_interval)
        start_km = getattr(self, 'zero_start_km', 0) if hasattr(self, 'zero_start_km') else 0

        tick_positions = []
        tick_labels = []

        current_pos = 0
        while current_pos <= self.total_distance + interval:
            tick_positions.append(current_pos)

            interval_number = int(round(current_pos / interval))
            interval_value_meters = interval_number * interval

            tick_labels.append(f"{start_km}+{interval_value_meters:03d}")

            current_pos += interval

        # Rebuild scale line and marker
        self.scale_line, = self.scale_ax.plot([0, self.total_distance], [0.5, 0.5],
                                              color='black', linewidth=3)
        self.scale_marker, = self.scale_ax.plot([0, 0], [0, 1], color='red',
                                                linewidth=2, linestyle='--')

        self.scale_ax.set_xticks(tick_positions)
        self.scale_ax.set_xticklabels(tick_labels, rotation=30, ha='right')
        self.scale_ax.set_xlim(0, self.total_distance)
        self.scale_ax.set_ylim(0, 1.2)
        self.scale_ax.set_yticks([])
        self.scale_ax.set_xlabel('Chainage (KM+Interval)', labelpad=10, fontweight='bold')
        self.scale_ax.set_title('Chainage Scale', fontweight='bold', pad=3)
        self.scale_ax.grid(True, axis='x', linestyle='--', alpha=0.3)
        self.scale_ax.spines['top'].set_visible(False)
        self.scale_ax.spines['right'].set_visible(False)
        self.scale_ax.spines['left'].set_visible(False)

        self.scale_section.setVisible(True)
        self.scale_canvas.draw()

# =======================================================================================================================================
# EDIT ZERO LINE
    def edit_zero_line(self):
        if not self.zero_line_set:
            return
        dialog = ZeroLineDialog(
            self.zero_start_point, self.zero_end_point,
            self.zero_start_km, self.zero_start_chain,
            self.zero_end_km, self.zero_end_chain,
            self.zero_interval,
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            try:
                p1, p2 = dialog.get_points()
                if p1 is not None and p2 is not None:
                    self.zero_start_point = p1
                    self.zero_end_point = p2
                
                # Store the configuration
                self.zero_start_km = int(dialog.km1_edit.text() or 0)
                self.zero_start_chain = float(dialog.chain1_edit.text() or 0)
                self.zero_end_km = int(dialog.km2_edit.text() or 0)
                self.zero_end_chain = float(dialog.chain2_edit.text() or 0)
                self.zero_interval = int(dialog.interval_edit.text() or 20)
                
                # IMPORTANT: Calculate the total chainage distance
                # Convert both to absolute meters for calculation
                start_abs_m = self.zero_start_km * 1000 + self.zero_start_chain
                end_abs_m = self.zero_end_km * 1000 + self.zero_end_chain
                self.zero_total_chainage_m = end_abs_m - start_abs_m
                
                # Update visual elements
                self.update_zero_actors()
                self.update_chainage_ticks()
                
                # Update scale section with proper formatting
                self.update_scale_ticks()
                
                # Update marker position
                current_slider_value = self.volume_slider.value()
                self.update_scale_marker()
                self.update_main_graph_marker(current_slider_value)
                
                # Make sure scale section is visible
                self.scale_section.setVisible(True)
                
                self.canvas.draw()
                self.figure.tight_layout()
                self.message_text.append("Zero line configuration updated.")
                
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers.")

# =======================================================================================================================================
    def edit_construction_dots_line(self):
        if not self.construction_dots_line.isChecked():
            return
        
        # Check if bridge baseline is active
        if self.bridge_baseline.text() != "Hide Bridge Baseline":
            QMessageBox.warning(self, "Not Available", 
                              "Construction dots are only available when Bridge Baseline is active.\n"
                              "Please click 'Bridge Baseline' button first.")
            self.construction_dots_line.setChecked(False)
            return
        
        # Start construction dots drawing mode
        self.message_text.append("Construction Dots Mode Active")
        self.message_text.append("Click on the graph to add construction dots (P1, P2, etc.)")
        self.message_text.append("Click on the labels (P1, P2) to configure each construction point")
        
        # Enable drawing mode for construction dots
        if self.cid_click is None:
            self.cid_click = self.canvas.mpl_connect('button_press_event', self.on_draw_click)
            self.cid_key = self.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        self.active_line_type = 'construction_dots'
        self.current_points = []
        self.current_artist = None
        self.current_redo_points = []
        
        # Make sure the graph is ready
        self.canvas.draw()
        self.figure.tight_layout()
        # dialog = ConstructionDotsLineDialog(self)
        # if dialog.exec_() == QDialog.Accepted:
        #     config = dialog.get_configuration()
        #     self.message_text.append(f"Construction Dots Config: Spacing: {config['spacing']}, Size: {config['size']}")
            # Add further logic here if needed (e.g., apply construction dots settings)

# =======================================================================================================================================
    def edit_deck_line(self):
        if not self.deck_line.isChecked():
            return
        # dialog = DeckLineDialog(self)
        # if dialog.exec_() == QDialog.Accepted:
        #     config = dialog.get_configuration()
        #     self.message_text.append(f"Deck Line Config: Thickness: {config['thickness']}, Material: {config['material']}")
            # Add further logic here if needed (e.g., apply deck line settings)

# =========================================================================================================================================================
# # CURVE BUTTON HANDLER
    def on_curve_button_clicked(self, event=None):
        """Handle Curve button and annotation clicks"""
        # Clicked on any curve label → edit
        if event is not None and hasattr(event, 'artist') and event.artist in self.curve_labels:
            self.edit_current_curve()
            return

        # Curve active → ask to complete
        if self.curve_active:
            reply = QMessageBox.question(
                self,
                "Complete Curve",
                "Do you want to complete the current curve segment?\n\n"
                "The curve labels will remain on the graph.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.complete_current_curve()
            return

        # Start new curve
        self.start_new_curve()


# =========================================================================================================================================================
    def start_new_curve(self):
        """Open dialog and start adding curve labels from current point onward"""
        dialog = CurveDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return

        # Extract full config from dialog
        config = dialog.get_configuration()

        # Validate angle
        if config['angle'] <= 0:
            QMessageBox.warning(self, "Invalid Angle", "Please enter an angle greater than 0.")
            return

        # Get last surface point X
        last_x = self.get_last_surface_x()
        if last_x is None:
            QMessageBox.critical(self, "Error", "Draw at least one point on Surface Line first.")
            return
        
# --------------------------------------------------------
        # NEW: convert chainage → real 3D point (the actual clicked surface point)
        # Find the surface point that has this chainage
        found = False
        for line_type in ['surface']:
            for polyline in reversed(self.line_types[line_type]['polylines']):  # newest first
                for dist, rel_z in reversed(polyline):
                    if abs(dist - last_x) < 0.5:  # small tolerance
                        t = dist / self.total_distance
                        dir_vec = self.zero_end_point - self.zero_start_point
                        pos = self.zero_start_point + t * dir_vec
                        pos[2] = self.zero_start_z + rel_z
                        self.curve_start_point_3d = pos.copy()
                        found = True
                        break
                if found:
                    break
            if found:
                break

        if not found:
            # fallback – just use zero line height
            t = last_x / self.total_distance
            dir_vec = self.zero_end_point - self.zero_start_point
            pos = self.zero_start_point + t * dir_vec
            pos[2] = self.zero_start_z
            self.curve_start_point_3d = pos.copy()
# ---------------------------------------------------------------

        # === START CURVE MODE ===
        self.curve_active = True
        self.curve_start_x = last_x

        # Store config for auto-labeling new points during drawing
        self.current_curve_config = config

        # Clear any previous curve labels
        self.clear_curve_labels()

        # Add first label using the full config from dialog
        self.add_curve_label_at_x(last_x, config)

        # Format display text for button
        outer = config['outer_curve']
        inner = config['inner_curve']
        curve_type = "O&I" if outer and inner else ("O" if outer else ("I" if inner else ""))
        display_text = f"{config['angle']:.1f}° - {curve_type}" if curve_type else f"{config['angle']:.1f}°"

        # Update Curve button appearance
        self.preview_button.setText(f"Curve ({display_text})")
        self.preview_button.setStyleSheet("""
            QPushButton { 
                background-color: #FF5722; 
                color: white; 
                padding: 12px; 
                border-radius: 6px;
                font-size: 15px; 
                font-weight: bold; 
            }
            QPushButton:hover { background-color: #F57C00; }
        """)

        # Log in message area
        chainage = self.get_chainage_label(last_x)
        self.message_text.append(f"Curve started: '{display_text}' at chainage {chainage}")
        self.message_text.append("Every new Surface point will now get this curve label at the top.")
        self.message_text.append("Click any curve label to edit it individually.")
        self.message_text.append("Click 'Curve' button again to finish the segment.")

        self.canvas.draw_idle()

# ==============================================================================================================================================================
    def add_curve_label_at_x(self, x, config=None):
        """
        Add a curve label at position x.
        config is a dict: {'angle': 5.0, 'outer_curve': True, 'inner_curve': False}
        If None, uses default from current_curve_text
        """
        if config is None:
            # Extract from current text if available
            # Fallback to empty
            angle = 5.0
            outer = False
            inner = False
            if self.current_curve_text:
                try:
                    parts = self.current_curve_text.replace('°', '').split(' - ')
                    angle = float(parts[0])
                    type_part = parts[1] if len(parts) > 1 else ""
                    outer = 'O' in type_part
                    inner = 'I' in type_part
                except:
                    angle = 5.0
                    outer = False
                    inner = False
            config = {'angle': angle, 'outer_curve': outer, 'inner_curve': inner}

        # Format display text
        curve_type = "O&I" if config['outer_curve'] and config['inner_curve'] else \
                     ("O" if config['outer_curve'] else ("I" if config['inner_curve'] else ""))
        display_text = f"{config['angle']:.1f}° - {curve_type}" if curve_type else f"{config['angle']:.1f}°"

        # Create small label like construction dots
        label = self.ax.text(
            x, 1.02,
            display_text,
            transform=self.ax.get_xaxis_transform(),
            ha='center', va='bottom',
            fontsize=9,
            fontweight='bold',
            color='darkred',
            bbox=dict(
                boxstyle="round,pad=0.4",
                facecolor="yellow",
                edgecolor="red",
                linewidth=1.8,
                alpha=0.9
            ),
            zorder=100,
            picker=True
        )

        # Store both artist and its config
        self.curve_labels.append((label, config))

        # Reconnect picker
        if self.curve_pick_id:
            self.canvas.mpl_disconnect(self.curve_pick_id)

        def on_pick(ev):
            # Find which label was clicked
            for artist, cfg in self.curve_labels:
                if ev.artist == artist:
                    self.edit_individual_curve_label(artist, cfg)
                    break

        self.curve_pick_id = self.canvas.mpl_connect('pick_event', on_pick)

# ===========================================================================================================================================================
    def edit_individual_curve_label(self, label_artist, current_config):
        """Open dialog to edit ONE specific curve label"""
        dialog = CurveDialog(self)

        # Pre-fill with current values
        dialog.angle_edit.setText(f"{current_config['angle']:.1f}")
        dialog.outer_checkbox.setChecked(current_config['outer_curve'])
        dialog.inner_checkbox.setChecked(current_config['inner_curve'])

        if dialog.exec_() != QDialog.Accepted:
            return

        new_config = dialog.get_configuration()
        new_angle = new_config['angle']
        if new_angle <= 0:
            QMessageBox.warning(self, "Invalid Angle", "Angle must be greater than 0.")
            return

        # Format new display text
        outer = new_config['outer_curve']
        inner = new_config['inner_curve']
        curve_type = "O&I" if outer and inner else ("O" if outer else ("I" if inner else ""))
        new_text = f"{new_angle:.1f}° - {curve_type}" if curve_type else f"{new_angle:.1f}°"

        # Update only this label's text
        label_artist.set_text(new_text)

        # Update stored config for this label
        for i, (artist, cfg) in enumerate(self.curve_labels):
            if artist == label_artist:
                self.curve_labels[i] = (artist, new_config)
                break

        self.message_text.append(f"Updated curve label to: {new_text}")
        self.canvas.draw_idle()

# ===========================================================================================================================================================
    def edit_current_curve(self):
        """Edit curve angle/type – updates all existing labels"""
        if not self.curve_active:
            return

        dialog = CurveDialog(self)
        # Pre-fill current values (you can extract from self.current_curve_text if needed)
        # For simplicity, just open fresh – user can re-enter
        if dialog.exec_() != QDialog.Accepted:
            return

        config = dialog.get_configuration()
        angle = config['angle']
        if angle <= 0:
            QMessageBox.warning(self, "Invalid", "Angle must be > 0")
            return

        outer = config['outer_curve']
        inner = config['inner_curve']
        curve_type = "O&I" if outer and inner else ("O" if outer else ("I" if inner else ""))
        new_text = f"{angle:.1f}° - {curve_type}" if curve_type else f"{angle:.1f}°"

        # Update stored text
        self.current_curve_text = new_text

        # Update ALL existing curve labels
        for label in self.curve_labels:
            label.set_text(new_text)

        # Update button
        self.preview_button.setText(f"Curve ({new_text})")

        self.message_text.append(f"Curve updated to: {new_text}")
        self.canvas.draw_idle()

# ===========================================================================================================================================================
    def complete_current_curve(self):
        """End curve mode – keep all labels"""
        if not self.curve_active:
            return

        self.curve_active = False
        self.curve_start_x = None

        # Reset button
        self.preview_button.setText("Curve")
        self.preview_button.setStyleSheet("""
            QPushButton { background-color: #808080; color: white; padding: 12px; border-radius: 6px;
                          font-size: 15px; font-weight: bold; }
            QPushButton:hover { background-color: #6E6E6E; }
        """)

        self.message_text.append(f"Curve completed! {len(self.curve_labels)} labels remain on graph.")
        self.canvas.draw_idle()


# ===========================================================================================================================================================
    def clear_curve_labels(self):
        """Remove all curve labels (used on new curve or reset)"""
        for label in self.curve_labels:
            try:
                label.remove()
            except:
                pass
        self.curve_labels = []

        if self.curve_pick_id:
            self.canvas.mpl_disconnect(self.curve_pick_id)
            self.curve_pick_id = None

# ===========================================================================================================================================================
    def get_last_surface_x(self):
        """
        Returns the X-coordinate (distance along zero line) of the most recent point
        on the Surface Line (either from completed polylines or current drawing).
        Returns None if no surface points exist.
        """
        # Check completed surface polylines (in reverse order - last one first)
        for polyline in reversed(self.line_types['surface']['polylines']):
            if polyline:  # if not empty
                return polyline[-1][0]  # return X of last point

        # Check if currently drawing a surface line
        if self.active_line_type == 'surface' and self.current_points:
            if len(self.current_points) > 0:
                return self.current_points[-1][0]

        # No surface points found
        return None

# ===========================================================================================================================================================
    def undo_graph(self):
        if self.active_line_type is None:
            return
    
        if self.active_line_type == 'construction_dots' and self.current_points:
            # For construction dots, remove the last point only
            if len(self.current_points) > 0:
                popped = self.current_points.pop()
                self.current_redo_points.append(popped)
                
                # Remove the last point label if it exists
                if self.current_point_labels:
                    label = self.current_point_labels.pop()
                    if label and label in self.ax.texts:
                        label.remove()
                
                # Remove the last visual dot if it exists
                if hasattr(self, 'construction_dot_artists') and self.construction_dot_artists:
                    artist = self.construction_dot_artists.pop()
                    try:
                        artist.remove()
                    except:
                        pass
                
                self.canvas.draw()
                self.figure.tight_layout()
            return
            
        # Original logic for other line types
        if self.current_points:
            if len(self.current_points) > 0:
                popped = self.current_points.pop()
                self.current_redo_points.append(popped)
                color = self.line_types[self.active_line_type]['color']
                
                # No labels to remove for other line types
                
                if self.current_points:
                    xs = [p[0] for p in self.current_points]
                    ys = [p[1] for p in self.current_points]
                    if self.current_artist is None:
                        self.current_artist, = self.ax.plot(xs, ys, color=color, linewidth=2, marker='o', markersize=5)
                    else:
                        self.current_artist.set_data(xs, ys)
                else:
                    if self.current_artist is not None:
                        self.current_artist.remove()
                        self.current_artist = None
                
                self.canvas.draw()
                self.figure.tight_layout()
        elif self.all_graph_lines:
            lt, points, artist, ann = self.all_graph_lines.pop()
            artist.remove()
            if ann:  # Only remove annotation if it exists
                ann.remove()
            self.line_types[lt]['artists'].pop()
            self.line_types[lt]['polylines'].pop()
            self.redo_stack.append((lt, points))
            
            # Remove any stored point labels for this polyline (only for construction dots)
            if lt == 'construction_dots' and self.point_labels:
                # Remove the last n labels where n is the number of points
                for _ in range(len(points)):
                    if self.point_labels:
                        label = self.point_labels.pop()
                        if label and label in self.ax.texts:
                            label.remove()
            
            self.canvas.draw()
            self.figure.tight_layout()

# ===========================================================================================================================================================
    def redo_graph(self):
        if self.active_line_type is None:
            return
        
        if self.current_redo_points:
            if len(self.current_redo_points) > 0:
                point = self.current_redo_points.pop()
                self.current_points.append(point)
                color = self.line_types[self.active_line_type]['color']
                xs = [p[0] for p in self.current_points]
                ys = [p[1] for p in self.current_points]
                
                # Add point label only for construction dots
                if self.active_line_type == 'construction_dots':
                    label = self.add_point_label(point[0], point[1], len(self.current_points), self.active_line_type)
                    if label:  # Only append if label was created
                        self.current_point_labels.append(label)
                
                if self.current_artist is None:
                    self.current_artist, = self.ax.plot(xs, ys, color=color, linewidth=2, marker='o', markersize=5)
                else:
                    self.current_artist.set_data(xs, ys)
                
                self.canvas.draw()
                self.figure.tight_layout()
        elif self.redo_stack:
            lt, points = self.redo_stack.pop()
            color = self.line_types[lt]['color']
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            new_artist, = self.ax.plot(xs, ys, color=color, linewidth=2, marker='o', markersize=5)
            
            # Re-add point labels only for construction dots
            if lt == 'construction_dots':
                for i, (x, y) in enumerate(points, 1):
                    label = self.add_point_label(x, y, i, lt)
                    if label:  # Only append if label was created
                        self.point_labels.append(label)
            
            # Calculate total length in meters
            length = 0.0
            for i in range(1, len(points)):
                dx = points[i][0] - points[i-1][0]
                dy = points[i][1] - points[i-1][1]
                length += np.sqrt(dx**2 + dy**2)
            
            # Annotate the length at the end point (only for non-construction dots)
            if lt != 'construction_dots':
                end_x, end_y = points[-1]
                ann = self.ax.annotate(f'{length:.2f}m', xy=(end_x, end_y), xytext=(5, 5),
                                       textcoords='offset points',
                                       bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7),
                                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            else:
                ann = None
            
            self.all_graph_lines.append((lt, points, new_artist, ann))
            self.line_types[lt]['artists'].append(new_artist)
            self.line_types[lt]['polylines'].append(points[:])
            
            self.canvas.draw()
            self.figure.tight_layout()

# ===========================================================================================================================================================
    def finish_current_polyline(self):
        if self.active_line_type == 'construction_dots':
            # For construction dots - store as individual points without connecting line
            if len(self.current_points) > 0:
                # Create individual point markers for each point
                color = self.line_types[self.active_line_type]['color']
                
                # Plot all points as separate markers
                xs = [p[0] for p in self.current_points]
                ys = [p[1] for p in self.current_points]
                
                # Create a single scatter plot for all construction dots
                # This makes it easier to manage as a single artist
                scatter_artist = self.ax.scatter(xs, ys, color=color, s=100, marker='o', zorder=5)
                
                self.line_types[self.active_line_type]['artists'].append(scatter_artist)
                self.line_types[self.active_line_type]['polylines'].append(self.current_points[:])

                # Add curve labels to all points in this completed polyline if curve is active
                if self.active_line_type == 'surface' and self.curve_active and self.current_curve_text:
                    for px, py in self.current_points:
                        self.add_curve_label_at_x(px)
                

                for label in self.current_point_labels:
                    if label:
                        self.point_labels.append(label)
                
                self.all_graph_lines.append((self.active_line_type, self.current_points[:], scatter_artist, None))
                
                self.message_text.append(f"Construction dots completed with {len(self.current_points)} points")
                
                self.current_points = []
                self.current_artist = None
                self.current_redo_points = []
                self.current_point_labels = []
                
                # Clear temporary construction dot artists
                if hasattr(self, 'construction_dot_artists'):
                    for artist in self.construction_dot_artists:
                        try:
                            artist.remove()
                        except:
                            pass
                    self.construction_dot_artists = []
                
                self.canvas.draw()
                self.figure.tight_layout()
            elif len(self.current_points) == 1:
                self.message_text.append("Need at least 1 point for construction dots")
            return
        
        # For other line types (original code remains the same)
        if len(self.current_points) > 1 and self.active_line_type:
            xs = [p[0] for p in self.current_points]
            ys = [p[1] for p in self.current_points]
            color = self.line_types[self.active_line_type]['color']
            line_artist, = self.ax.plot(xs, ys, color=color, linewidth=2, marker='o', markersize=5)
            
            self.line_types[self.active_line_type]['artists'].append(line_artist)
            self.line_types[self.active_line_type]['polylines'].append(self.current_points[:])
            

            # Save the polyline to the current mode's data
            if self.current_mode == 'road' and self.active_line_type in ['construction', 'surface', 'road_surface', 'zero']:
                if self.active_line_type not in self.road_lines_data:
                    self.road_lines_data[self.active_line_type] = {'polylines': [], 'artists': []}
                self.road_lines_data[self.active_line_type]['polylines'].append(self.current_points.copy())
                
            elif self.current_mode == 'bridge' and self.active_line_type in ['deck_line', 'projection_line', 'construction_dots', 'zero']:
                if self.active_line_type not in self.bridge_lines_data:
                    self.bridge_lines_data[self.active_line_type] = {'polylines': [], 'artists': []}
                self.bridge_lines_data[self.active_line_type]['polylines'].append(self.current_points.copy())
            
            length = 0.0
            for i in range(1, len(self.current_points)):
                dx = self.current_points[i][0] - self.current_points[i-1][0]
                dy = self.current_points[i][1] - self.current_points[i-1][1]
                length += np.sqrt(dx**2 + dy**2)
            
            if self.active_line_type != 'construction_dots':
                end_x, end_y = self.current_points[-1]
                ann = self.ax.annotate(f'{length:.2f}m', xy=(end_x, end_y), xytext=(5, 5),
                                    textcoords='offset points',
                                    bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7),
                                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            else:
                ann = None
            
            self.all_graph_lines.append((self.active_line_type, self.current_points[:], line_artist, ann))
            self.current_redo_points = []
            self.current_point_labels = []
            
            self.canvas.draw()
            self.figure.tight_layout()
        
        self.current_points = []
        if self.current_artist is not None:
            self.current_artist.remove()
            self.current_artist = None
        self.message_text.append(f"{self.active_line_type.replace('_', ' ').title()} completed")

# ===========================================================================================================================================================
    def add_point_label(self, x, y, point_number, line_type):
        """Add a small label above the clicked point on the graph - ONLY for construction dots"""
        # Only create labels for construction dots
        if line_type != 'construction_dots':
            return None
        
        # Create a small label (like P1, P2, etc.)
        label = f'P{point_number}'
        
        # For construction dots, place at the TOP of the graph area
        label_x = x
        label_y = 1.05  # 5% above the top of the graph area
        
        # Make construction dots labels clickable with distinctive appearance
        text_obj = self.ax.text(
            label_x, label_y, label, 
            transform=self.ax.get_xaxis_transform(),  # x in data coords, y in axes coords
            fontsize=10, 
            color='red',
            fontweight='bold',
            ha='center', 
            va='center',
            bbox=dict(
                boxstyle='round,pad=0.5', 
                facecolor='yellow', 
                alpha=0.9,
                edgecolor='red',
                linewidth=2
            ),
            picker=True  # Make it clickable - THIS IS IMPORTANT!
        )
        
        # Store point data for click handling
        text_obj.point_data = {
            'type': 'construction_dot',
            'point_number': point_number,
            'x': x,
            'y': y,
            'line_type': line_type
        }
        
        return text_obj
    
# ===========================================================================================================================================================
    def on_draw_click(self, event):
        if event.inaxes != self.ax or self.active_line_type is None:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return

        # Get current time for double-click detection
        current_time = time.time()
        time_diff = current_time - self.last_click_time

        # Handle double-click (for line completion)
        if time_diff < self.double_click_threshold and len(self.current_points) > 1:
            self.finish_current_polyline()
            self.last_click_time = 0
            return

        # For construction dots - separate handling (your existing code)
        if self.active_line_type == 'construction_dots':
            if len(self.current_points) == 0:
                self.current_points.append((x, y))
                label = self.add_point_label(x, y, len(self.current_points), self.active_line_type)
                if label:
                    self.current_point_labels.append(label)

                color = self.line_types[self.active_line_type]['color']
                self.current_artist, = self.ax.plot([x], [y], color=color, marker='o', markersize=8, linestyle='')
            else:
                self.current_points.append((x, y))
                label = self.add_point_label(x, y, len(self.current_points), self.active_line_type)
                if label:
                    self.current_point_labels.append(label)

                color = self.line_types[self.active_line_type]['color']
                new_artist, = self.ax.plot([x], [y], color=color, marker='o', markersize=8, linestyle='')

                if not hasattr(self, 'construction_dot_artists'):
                    self.construction_dot_artists = []
                self.construction_dot_artists.append(new_artist)

            self.last_click_time = current_time
            self.canvas.draw_idle()
            return

        # For other line types (including surface)
        if len(self.current_points) == 0:
            self.current_points.append((x, y))
        else:
            self.current_points.append((x, y))

        # Update current artist with markers
        color = self.line_types[self.active_line_type]['color']
        xs = [p[0] for p in self.current_points]
        ys = [p[1] for p in self.current_points]

        if self.current_artist is None:
            self.current_artist, = self.ax.plot(xs, ys, color=color, linewidth=2, marker='o', markersize=5)
        else:
            self.current_artist.set_data(xs, ys)
            self.current_artist.set_color(color)

        # =====================================================
        # SPECIAL: Add curve label when drawing Surface Line
        # =====================================================
        if self.active_line_type == 'surface' and self.curve_active:
            latest_x = self.current_points[-1][0]  # X of the newly added point
            self.add_curve_label_at_x(latest_x)

        self.last_click_time = current_time
        self.canvas.draw_idle()

# ===========================================================================================================================================================
    def load_point_cloud(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Open Point Cloud File", "",
            "Point Cloud Files (*.ply *.pcd *.xyz);;All Files (*)")
        if not file_path:
            return
        try:
            # --- Store the loaded file path and name for later use ---
            self.loaded_file_path = file_path
            self.loaded_file_name = os.path.splitext(os.path.basename(file_path))[0]
            # Show progress bar with file name
            self.show_progress_bar(file_path)
            self.update_progress(10, "Starting file loading...")
            # Read the file directly without intermediate processing steps
            if file_path.endswith('.ply') or file_path.endswith('.pcd'):
                self.update_progress(30, "Loading point cloud data...")
                self.point_cloud = o3d.io.read_point_cloud(file_path)
  
            elif file_path.endswith('.xyz'):
                self.update_progress(30, "Loading XYZ data...")
                # For XYZ files, use numpy's faster loading
                data = np.loadtxt(file_path, usecols=(0, 1, 2)) # Only load XYZ columns
                self.point_cloud = o3d.geometry.PointCloud()
                self.point_cloud.points = o3d.utility.Vector3dVector(data[:, :3])
            if not self.point_cloud.has_points():
                raise ValueError("No points found in the file.")
            # Skip color processing if not needed for faster loading
            if self.point_cloud.has_colors():
                self.update_progress(70, "Processing colors...")
            else:
                self.update_progress(70, "Preparing visualization...")
            # Directly convert to VTK format without intermediate steps
            self.update_progress(90, "Creating visualization...")
            self.display_point_cloud()
            # Final update before hiding
            self.update_progress(100, "Loading complete!")
            QTimer.singleShot(100, self.hide_progress_bar)
        except Exception as e:
            self.hide_progress_bar()


# =======================================================================================================================================
    def display_point_cloud(self):
        if not self.point_cloud:
            return
        # Clear previous point cloud if any
        if self.point_cloud_actor:
            self.renderer.RemoveActor(self.point_cloud_actor)
        self.update_progress(92, "Converting to VTK format...")
        # Convert Open3D point cloud to VTK format
        points = np.asarray(self.point_cloud.points)
        # Create VTK points
        vtk_points = vtk.vtkPoints()
        for i, point in enumerate(points):
            vtk_points.InsertNextPoint(point[0], point[1], point[2])
            # Update progress every 1000 points
            if i % 1000 == 0:
                progress = 92 + int(6 * (i / len(points)))
                self.update_progress(min(progress, 98), f"Processing points: {i}/{len(points)}")
        # Create VTK polydata
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(vtk_points)
        # Create vertex cells
        vertices = vtk.vtkCellArray()
        for i in range(points.shape[0]):
            vertices.InsertNextCell(1)
            vertices.InsertCellPoint(i)
        polydata.SetVerts(vertices)
        # Add color information if available
        if self.point_cloud.has_colors():
            self.update_progress(95, "Processing colors...")
            colors = np.asarray(self.point_cloud.colors) * 255 # Convert from 0-1 to 0-255
            vtk_colors = vtk.vtkUnsignedCharArray()
            vtk_colors.SetNumberOfComponents(3)
            vtk_colors.SetName("Colors")
            for color in colors:
                vtk_colors.InsertNextTuple3(color[0], color[1], color[2])
            polydata.GetPointData().SetScalars(vtk_colors)
        # Create mapper and actor
        self.update_progress(97, "Creating visualization...")
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        self.point_cloud_actor = vtk.vtkActor()
        self.point_cloud_actor.SetMapper(mapper)
        self.point_cloud_actor.GetProperty().SetPointSize(2)
        # Only set color if no vertex colors are present
        if not self.point_cloud.has_colors():
            self.point_cloud_actor.GetProperty().SetColor(self.colors.GetColor3d("Black"))
        self.renderer.AddActor(self.point_cloud_actor)
        self.renderer.ResetCamera()
        self.update_progress(99, "Finalizing...")
        self.vtk_widget.GetRenderWindow().Render()
        self.update_progress(100, "Ready!")

# ========================================================================================================
# Define function for the mesurement type:
    def set_measurement_type(self, m_type):
        """Set the measurement type and configure the UI and state accordingly."""
        if not self.measurement_active:
            return
        self.measurement_active = True
        self.current_measurement = m_type
        self.measurement_started = False
        self.plotting_active = True
        # Only clear measurement points if not continuing measurement line
        if m_type != 'vertical_line' or not hasattr(self, 'measurement_line_points'):
            self.measurement_points = []
        # Configure based on measurement type
        if m_type == 'polygon':
            self.complete_polygon_button.setVisible(True)
            self.complete_polygon_button.setStyleSheet("""
            QPushButton {
                background-color: #98FB98; /* Light green */
                color: black;
                border: 1px solid gray;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7DCE7D; /* Slightly darker green on hover */
            }
            """)
            self.measurement_started = True
        elif m_type == 'horizontal_line':
            self.presized_button.setVisible(True)
        elif m_type == 'vertical_line':
                print("Vertical line selected. Click 2 points (A, B) for height measurement.")
                self.measurement_points = [] # Clear previous points
                self.presized_button.setVisible(True)
                return
        else:
            # Hide the presized button for other measurement types
            self.presized_button.setVisible(False)

# =================================================================================================================================
# Define the function for the update the mesurement metrics as per the selected metrics::
    def update_measurement_metrics(self):
        """Update all measurements when the units change"""
        if not hasattr(self, 'measurement_points') or not self.measurement_points:
            return
        # Get the current units suffix
        units_suffix = self.get_units_suffix()
        # Update all measurement labels
        for actor in self.measurement_actors:
            if isinstance(actor, vtk.vtkFollower):
                try:
                    text_source = actor.GetMapper().GetInputConnection(0, 0).GetProducer()
                    if isinstance(text_source, vtk.vtkVectorText):
                        text = text_source.GetText()
                        if text and any(x in text for x in ['m', 'ft', 'cm', 'mm']):
                            # This is a measurement label - update it
                            if '=' in text: # Angle label
                                continue # Don't modify angle labels
              
                            # Extract the numeric value
                            try:
                                value_str = text.split('=')[-1].strip().rstrip('m').rstrip('cm').rstrip('mm')
                                value_meters = float(value_str)
                                converted_value = self.convert_to_current_units(value_meters)
                                new_text = f"{converted_value:.2f}{units_suffix}"
                                text_source.SetText(new_text)
                            except:
                                continue
                except:
                    continue
        self.vtk_widget.GetRenderWindow().Render()

# ==================================================================================================================================
    def get_current_units(self):
        """Get the current units and conversion factor from meters"""
        current_units = self.metrics_combo.currentText()
        if current_units == "Meter":
            return "m", 1.0
        elif current_units == "Centimeter":
            return "cm", 100.0
        elif current_units == "Millimeter":
            return "mm", 1000.0
        return "m", 1.0
    
# ==================================================================================================================================
# Convert the metrics from meter to cm and mm::
    def convert_to_current_units(self, value_in_meters):
        """Convert a value in meters to the currently selected units"""
        current_units = self.metrics_combo.currentText()
        if current_units == "Meter":
            return value_in_meters
        elif current_units == "Centimeter":
            return value_in_meters * 100
        elif current_units == "Millimeter":
            return value_in_meters * 1000
        return value_in_meters
    
# ==================================================================================================================================
# Define the function for the get curent metrics of measurement
    def get_units_suffix(self):
        """Get the suffix for the current units"""
        current_units = self.metrics_combo.currentText()
        if current_units == "Meter":
            return "m"
        elif current_units == "Centimeter":
            return "cm"
        elif current_units == "Millimeter":
            return "mm"
        return ""
    
# ==================================================================================================================================
# Define function to add sphere marker:
    def add_sphere_marker(self, point, label=None, radius = 0.07, color="Red"):
        """Add a sphere marker at the specified position with optional label"""
        sphere = vtkSphereSource()
        sphere.SetRadius(radius)
        sphere.SetCenter(point[0], point[1], point[2])
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())
        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(self.colors.GetColor3d(color)) # Use specified color
        if hasattr(self, 'measurement_points'):
            actor.point_index = len(self.measurement_points) - 1 # Store reference
        self.renderer.AddActor(actor)
        self.measurement_actors.append(actor)
        # Add label if provided
        if label:
            text = vtk.vtkVectorText()
            text.SetText(label)
            text_mapper = vtk.vtkPolyDataMapper()
            text_mapper.SetInputConnection(text.GetOutputPort())
            text_actor = vtk.vtkFollower()
            text_actor.SetMapper(text_mapper)
            text_actor.SetScale(0.1, 0.1, 0.1)
            text_actor.AddPosition(point[0] + 0.15, point[1] + 0.15, point[2])
            text_actor.GetProperty().SetColor(self.colors.GetColor3d("White"))
            self.renderer.AddActor(text_actor)
            text_actor.SetCamera(self.renderer.GetActiveCamera())
            self.measurement_actors.append(text_actor)
        self.vtk_widget.GetRenderWindow().Render()
        return actor # Return the sphere actor
    
# ==================================================================================================================================
    def find_nearest_point_in_neighborhood(self, click_pos, search_radius=4):
        """Find the nearest point in a neighborhood around the click position.
        Args:
            click_pos: (x, y) tuple of screen coordinates
            search_radius: radius in pixels to search around the click position
        Returns:
            The closest point's 3D coordinates, or None if no points found
        """
        if not hasattr(self, 'point_cloud') or not self.point_cloud:
            return None
        points = np.asarray(self.point_cloud.points)
        if len(points) == 0:
            return None
        # Convert all points to display coordinates
        renderer = self.renderer
        display_coords = []
        for point in points:
            try:
                display_coord = renderer.WorldToDisplay(point[0], point[1], point[2])
                display_coords.append(display_coord[:2]) # Only need x,y
            except:
                continue
        if not display_coords:
            return None
        display_coords = np.array(display_coords)
        # Calculate distances from click position
        distances = np.sqrt(
            (display_coords[:, 0] - click_pos[0])**2 +
            (display_coords[:, 1] - click_pos[1])**2
        )
        # Find the closest point within radius
        valid_indices = np.where(distances <= search_radius)[0]
        if len(valid_indices) == 0:
            return None
        closest_idx = valid_indices[np.argmin(distances[valid_indices])]
        return points[closest_idx]
    
# =========================================================================================================================================
# Define function for connect two points:
    def add_line_between_points(self, p1, p2, color, label=None, show_label=True):
        line = vtkLineSource()
        line.SetPoint1(p1[0], p1[1], p1[2])
        line.SetPoint2(p2[0], p2[1], p2[2])
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(line.GetOutputPort())
        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(self.colors.GetColor3d(color))
        actor.GetProperty().SetLineWidth(2)
        self.renderer.AddActor(actor)
        self.measurement_actors.append(actor)
        if show_label:
            # Calculate distance for label if not provided
            if label is None:
                distance_meters = sqrt(sum((p1 - p2) ** 2))
                units_suffix, conversion_factor = self.get_current_units()
                distance = distance_meters * conversion_factor
                label = f"{distance:.2f} "
            # Calculate midpoint for label position
            midpoint = [(p1[0] + p2[0])/2,
                        (p1[1] + p2[1])/2,
                        (p1[2] + p2[2])/2]
            # Calculate direction vector
            direction = np.array([p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2]])
            direction_norm = np.linalg.norm(direction)
            # Only add perpendicular offset if direction is not zero
            if direction_norm > 1e-10: # Small threshold to avoid division by zero
                direction = direction / direction_norm
                perpendicular = np.cross(direction, [0, 0, 1]) # Cross with Z-axis for perpendicular vector
                perpendicular_norm = np.linalg.norm(perpendicular)
  
                if perpendicular_norm > 1e-10: # Check if perpendicular vector is valid
                    perpendicular = perpendicular / perpendicular_norm
                    label_pos = midpoint + perpendicular * 0.5 # Small offset
                else:
                    # Fallback if line is vertical
                    label_pos = midpoint + np.array([0, 1, 0]) * 0.5
            else:
                # Points are identical or very close
                label_pos = midpoint
            text = vtk.vtkVectorText()
            text.SetText(label)
            text_mapper = vtk.vtkPolyDataMapper()
            text_mapper.SetInputConnection(text.GetOutputPort())
            text_actor = vtk.vtkFollower()
            text_actor.SetMapper(text_mapper)
            text_actor.SetScale(0.5, 0.5, 0.5) # Increased size to 0.5
            text_actor.AddPosition(label_pos[0], label_pos[1], label_pos[2])
            text_actor.GetProperty().SetColor(self.colors.GetColor3d("Blue")) # Blue color
            self.renderer.AddActor(text_actor)
            text_actor.SetCamera(self.renderer.GetActiveCamera())
            self.measurement_actors.append(text_actor)
            self.vtk_widget.GetRenderWindow().Render()
            return actor
        
# ==================================================================================================================================
# Define function add angle label on point cloud data point:
    def add_angle_label(self, a, b, c, label, offset=0.8):
        """Add a label showing the angle between points a-b-c at position b"""
        # Calculate position slightly away from point b
        direction = (a - b) + (c - b)
        direction = direction / np.linalg.norm(direction)
        position = b + direction * offset
        text = vtk.vtkVectorText()
        text.SetText(label)
        text_mapper = vtk.vtkPolyDataMapper()
        text_mapper.SetInputConnection(text.GetOutputPort())
        text_actor = vtk.vtkFollower()
        text_actor.SetMapper(text_mapper)
        text_actor.SetScale(0.1, 0.1, 0.1)
        text_actor.AddPosition(position[0], position[1], position[2])
        text_actor.GetProperty().SetColor(self.colors.GetColor3d("White"))
        self.renderer.AddActor(text_actor)
        text_actor.SetCamera(self.renderer.GetActiveCamera())
        self.measurement_actors.append(text_actor)
        self.vtk_widget.GetRenderWindow().Render()
        
# =========================================================================================================
    def add_text_label(self, position, text, color="Blue", scale=0.5, z_offset=0.0):
        """Add a text label at specified position"""
        try:
            pos = [position[0], position[1], position[2] + z_offset]
            # If text contains non-ASCII (like °), use BillboardTextActor3D
            if any(ord(c) > 127 for c in text):
                text_actor = vtk.vtkBillboardTextActor3D()
                text_actor.SetInput(text)
                text_actor.SetPosition(pos)
                text_actor.GetTextProperty().SetColor(self.colors.GetColor3d(color))
                text_actor.GetTextProperty().SetFontSize(int(scale * 80))
                # text_actor.GetTextProperty().BoldOn()
                self.renderer.AddActor(text_actor)
                self.measurement_actors.append(text_actor)
            else:
                # Default ASCII rendering using VectorText
                text_source = vtk.vtkVectorText()
                text_source.SetText(text)
                text_mapper = vtk.vtkPolyDataMapper()
                text_mapper.SetInputConnection(text_source.GetOutputPort())
                text_actor = vtk.vtkFollower()
                text_actor.SetMapper(text_mapper)
                text_actor.SetScale(scale, scale, scale)
                text_actor.AddPosition(position[0], position[1], position[2])
                text_actor.GetProperty().SetColor(self.colors.GetColor3d(color))
                text_actor.SetCamera(self.renderer.GetActiveCamera())
                self.renderer.AddActor(text_actor)
                self.measurement_actors.append(text_actor)
            # Render update
            self.vtk_widget.GetRenderWindow().Render()
        except Exception as e:
            print(f"Error adding text label: {e}")
            
# ==================================================================================================================================
    def on_click(self, obj, event):
        if self.drawing_zero_line:
            interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
            pos = interactor.GetEventPosition()
            # Pick point accurately
            cell_picker = vtk.vtkCellPicker()
            cell_picker.SetTolerance(0.0005)
            cell_picker.Pick(pos[0], pos[1], 0, self.renderer)
            clicked_point = None
            if cell_picker.GetCellId() != -1:
                clicked_point = np.array(cell_picker.GetPickPosition())
                points = np.asarray(self.point_cloud.points)
                if len(points) > 0:
                    distances = np.sum((points - clicked_point)**2, axis=1)
                    nearest_idx = np.argmin(distances)
                    clicked_point = points[nearest_idx]
            if clicked_point is None:
                clicked_point = self.find_nearest_point_in_neighborhood(pos)
            if clicked_point is None:
                return
            self.zero_points.append(clicked_point)
            label = "Start" if len(self.zero_points) == 1 else "End"
            actor = self.add_sphere_marker(clicked_point, label, color="purple")
            self.temp_zero_actors.append(actor)
            # When both points are picked
            if len(self.zero_points) == 2:
                self.drawing_zero_line = False
                # Open dialog with current picked points
                dialog = ZeroLineDialog(
                    point1=self.zero_points[0],
                    point2=self.zero_points[1],
                    km1=None,
                    chain1=None,
                    km2=None,
                    chain2=None,
                    interval=20.0,
                    parent=self
                )
                if dialog.exec_() == QDialog.Accepted:
                    try:
                        # Get updated coordinates from dialog (user can edit them)
                        p1, p2 = dialog.get_points()
                        if p1 is None or p2 is None:
                            raise ValueError("Invalid or empty coordinates for one or both points.")

                        # Update zero line points and state
                        self.zero_start_point = np.array(p1, dtype=float)
                        self.zero_end_point = np.array(p2, dtype=float)
                        self.zero_start_z = float(p1[2])  # Reference elevation from Point 1 Z

                        # Read KM values (optional, can be empty → None)
                        km1_text = dialog.km1_edit.text().strip()
                        km2_text = dialog.km2_edit.text().strip()
                        self.zero_start_km = int(km1_text) if km1_text else None
                        self.zero_end_km = int(km2_text) if km2_text else None

                        # Read interval (default 20.0 if empty)
                        # interval_text = dialog.interval_edit.text().strip()
                        # self.zero_interval = float(interval_text) if interval_text else 20.0
                        # #self.zero_interval = int(dialog.interval_edit.text().strip() or "20")


                        # === Read and validate Interval (must be positive integer) ===
                        interval_text = dialog.interval_edit.text().strip()
                        try:
                            interval_val = int(interval_text)
                            if interval_val <= 0:
                                raise ValueError("Interval must be greater than 0")
                            self.zero_interval = interval_val
                        except (ValueError, TypeError):
                            self.zero_interval = 20  # Safe default
                            self.message_text.append("Warning: Invalid interval entered. Using default 20m.")
                        
                        # Calculate total distance
                        self.total_distance = np.linalg.norm(self.zero_end_point - self.zero_start_point)
                        self.original_total_distance = self.total_distance
                        self.zero_line_set = True

                        # Update 3D actors (keep the temporary spheres as final markers)
                        self.zero_start_actor = self.temp_zero_actors[0]
                        self.zero_end_actor = self.temp_zero_actors[1]
                        self.zero_line_actor = self.add_line_between_points(
                            self.zero_start_point, self.zero_end_point, "purple", show_label=False
                        )

                        # Update 2D graph
                        self.ax.set_xlim(0, self.total_distance)
                        if hasattr(self, 'zero_graph_line') and self.zero_graph_line:
                            self.zero_graph_line.remove()
                        self.zero_graph_line, = self.ax.plot([0, self.total_distance], [0, 0],
                                                            color='purple', linewidth=3)

                        # Update ticks and scale
                        self.update_chainage_ticks()
                        self.update_scale_ticks()
                        if hasattr(self, 'scale_section'):
                            self.scale_section.setVisible(True)

                        # Redraw
                        self.canvas.draw()
                        self.figure.tight_layout()

                        # === SAVE ZERO LINE CONFIG TO JSON IN CURRENT DESIGN LAYER ===
                        self.save_zero_line_config_to_current_layer()

                        # Success messages
                        self.message_text.append("✓ Zero Line configured and saved successfully!")
                        self.message_text.append(f"   Length: {self.total_distance:.2f} m")
                        self.message_text.append(f"   Interval: {self.zero_interval:.1f} m")
                        if self.zero_start_km is not None:
                            self.message_text.append(f"   Start KM: {self.zero_start_km}+000")

                    except ValueError as e:
                        QMessageBox.warning(self, "Invalid Input", f"{str(e)}")
                        self.reset_zero_drawing()
                else:
                    # Dialog cancelled
                    self.reset_zero_drawing()
                    self.message_text.append("Zero line configuration cancelled.")

            self.vtk_widget.GetRenderWindow().Render()
            return  # Important: return early if we were drawing zero line
#-------------------------------------
        if not self.measurement_active or not self.current_measurement or self.freeze_view or not self.plotting_active:
            return
        interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        pos = interactor.GetEventPosition()
        # First try using cell picker which can pick between points
        cell_picker = vtk.vtkCellPicker()
        cell_picker.SetTolerance(0.0005) # Small tolerance for accurate picking
        cell_picker.Pick(pos[0], pos[1], 0, self.renderer)
        clicked_point = None
        if cell_picker.GetCellId() != -1:
            # Get the picked position in world coordinates
            clicked_point = np.array(cell_picker.GetPickPosition())
            # Find the nearest actual point in the point cloud to our picked position
            points = np.asarray(self.point_cloud.points)
            if len(points) > 0:
                distances = np.sum((points - clicked_point)**2, axis=1)
                nearest_idx = np.argmin(distances)
                clicked_point = points[nearest_idx]
        # If still no point found, use the neighborhood search
        if clicked_point is None:
            clicked_point = self.find_nearest_point_in_neighborhood(pos)
        if clicked_point is None:
            return # No point found
        # Handle vertical line case (after measurement line is set)
        if self.current_measurement == 'vertical_line':
            # Add point to measurement_points (for vertical line)
            self.measurement_points.append(clicked_point)
            point_label = chr(65 + len(self.measurement_points) - 1) # A, B
            # Visualize the point
            self.add_sphere_marker(clicked_point, point_label, color="Blue")
            self.process_vertical_line_measurement()
            self.vtk_widget.GetRenderWindow().Render()
            return
        # Handle horizontal line measurement
        if self.current_measurement == 'horizontal_line':
            # Add point to measurement
            self.measurement_points.append(clicked_point)
            # Visualize point
            self.add_sphere_marker(clicked_point, color="Blue")
            self.process_horizontal_line_measurement()
            self.vtk_widget.GetRenderWindow().Render()
            return
        # Handle polygon measurement
        if self.current_measurement == 'polygon' :
            # For first point, just add it
            if len(self.measurement_points) == 0:
                self.measurement_points.append(clicked_point)
                point_label = 'A' # First point is always A
                self.add_sphere_marker(clicked_point, point_label)
  
                self.vtk_widget.GetRenderWindow().Render()
                return
      
            # For regular clicks (adding points)
            point_label = chr(65 + len(self.measurement_points)) # A, B, C, etc.
            self.measurement_points.append(clicked_point)
            self.add_sphere_marker(clicked_point, point_label)
            # If this is at least the second point, draw a line
            if len(self.measurement_points) >= 2:
                p1 = self.measurement_points[-2]
                p2 = self.measurement_points[-1]
                self.add_line_between_points(p1, p2, "Purple")
               
        interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.vtk_widget.GetRenderWindow().Render()
        
# ===========================================================================================================================================================
    def reset_zero_drawing(self):
        for actor in self.temp_zero_actors:
            self.renderer.RemoveActor(actor)
            if actor in self.measurement_actors:
                self.measurement_actors.remove(actor)
        self.temp_zero_actors = []
        self.zero_points = []
        
        # Reset scale to default
        self.scale_ax.set_xticks(np.arange(0, self.total_distance + 1, 5))
        self.scale_ax.set_xticklabels([f"{x:.0f}" for x in np.arange(0, self.total_distance + 1, 5)])
        self.scale_canvas.draw()
        
# =================================================================================================================
# Define function for the connect the points which is already drawn on point cloud data:
    def connect_signals(self):
        # Connect UI signals
        self.reset_action_button.clicked.connect(self.reset_action)
        self.reset_all_button.clicked.connect(self.reset_all)
        self.preview_button.clicked.connect(self.on_curve_button_clicked)
        self.threed_map_button.clicked.connect(self.map_baselines_to_3d_planes)
        self.save_button.clicked.connect(self.save_current_design_layer)
        
        # Connect button signals that were commented out
        self.create_project_button.clicked.connect(self.open_create_project_dialog)
        self.existing_worksheet_button.clicked.connect(self.open_existing_worksheet)

        self.new_worksheet_button.clicked.connect(self.open_new_worksheet_dialog)
        self.new_design_button.clicked.connect(self.open_create_new_design_layer_dialog)
        self.new_construction_button.clicked.connect(self.open_construction_new_dialog)
        self.new_measurement_button.clicked.connect(self.open_measurement_dialog)
        self.load_button.clicked.connect(self.load_point_cloud)
        self.help_button.clicked.connect(self.show_help_dialog)
        
        # Connect checkbox signals
        self.zero_line.stateChanged.connect(lambda state: self.on_checkbox_changed(state, 'zero'))
        self.surface_baseline.stateChanged.connect(lambda state: self.on_checkbox_changed(state, 'surface'))
        self.construction_line.stateChanged.connect(lambda state: self.on_checkbox_changed(state, 'construction'))
        self.road_surface_line.stateChanged.connect(lambda state: self.on_checkbox_changed(state, 'road_surface'))
        self.bridge_zero_line.stateChanged.connect(lambda state: self.on_checkbox_changed(state, 'zero'))
        self.projection_line.stateChanged.connect(lambda state: self.on_checkbox_changed(state, 'projection_line'))
        self.construction_dots_line.stateChanged.connect(lambda state: self.on_checkbox_changed(state, 'construction_dots'))
        self.deck_line.stateChanged.connect(lambda state: self.on_checkbox_changed(state, 'deck_line'))
        
        # Connect pencil button signals
        self.zero_pencil.clicked.connect(self.edit_zero_line)
        self.bridge_zero_pencil.clicked.connect(self.edit_zero_line)
        self.construction_dots_pencil.clicked.connect(self.edit_construction_dots_line)
        self.deck_pencil.clicked.connect(self.edit_deck_line)
        self.add_material_line_button.clicked.connect(self.open_material_line_dialog)
   
        self.volume_slider.valueChanged.connect(self.volume_changed)
        
        # Connect graph hover event
        self.cid_hover = self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        
        # Connect undo/redo buttons
        self.undo_button.clicked.connect(self.undo_graph)
        self.redo_button.clicked.connect(self.redo_graph)


        # Add both left and right click events
        self.vtk_widget.GetRenderWindow().GetInteractor().AddObserver(
            "LeftButtonPressEvent", self.on_click)
        # Add key press event (Space bar for freeze/unfreeze, Escape for plotting toggle)
        self.vtk_widget.GetRenderWindow().GetInteractor().AddObserver(
            "KeyPressEvent", self.on_key_press)

# ===========================================================================================================================================================
    def on_slider_changed(self, value):
        """Handle slider change with graph scrolling"""
        # Call the original volume_changed logic
        print(f"Volume slider changed to: {value}%")
        if self.zero_line_set:
            self.update_scale_marker()
        
        # Scroll the graph
        self.scroll_graph_with_slider(value)
        
        # Also update the main graph marker if zero line is set
        if self.zero_line_set:
            self.update_main_graph_marker(value)

# ==================================================================================================================================
    def process_vertical_line_measurement(self):
        """Process vertical line measurement and calculate volume for round pillar if applicable."""
        if len(self.measurement_points) != 2:
            return
        point_a = self.measurement_points[0]
        point_b = self.measurement_points[1]
        self.vertical_points = [point_a, point_b]
        # Calculate vertical height in meters (difference in Z coordinates)
        self.vertical_height_meters = np.linalg.norm(point_b - point_a)
        self.plotting_active = False
        # Get current units
        units_suffix, conversion_factor = self.get_current_units()
        height = self.vertical_height_meters * conversion_factor
        # Draw the vertical line and store the actor
        self.main_line_actor = self.add_line_between_points(point_a, point_b, "Red", f"AB={height:.2f}{units_suffix}")
        # Store reference to the distance label actor (the last added actor)
        if self.measurement_actors:
            self.distance_label_actor = self.measurement_actors[-1]
        self.point_a_actor = self.add_sphere_marker(point_a, "A")
        self.point_b_actor = self.add_sphere_marker(point_b, "B")
        # Output the height
        self.message_text.append(f"--- Vertical Height ---\n AB = {height:.2f} {units_suffix}")
        # Check if point B is on baseline
        on_baseline = False
        if hasattr(self, 'baseline_actors') and self.baseline_actors:
            baseline_actor = self.baseline_actors[0]
            bounds = baseline_actor.GetBounds()
            baseline_z = bounds[4] # Minimum Z of the baseline plane
            if abs(point_b[2] - baseline_z) < 0.001: # Account for floating point precision
                on_baseline = True
        # Initialize line_data if it doesn't exist
        if not hasattr(self, 'line_data'):
            self.line_data = {}
        # Store basic line data
        self.line_data = {
            'length': height,
            'points': {
                'A': point_a,
                'B': point_b
            },
            'on_baseline': on_baseline
        }
        self.vtk_widget.GetRenderWindow().Render()
        
# ==================================================================================================================================
    def process_horizontal_line_measurement(self):
        """Process horizontal line measurement with two points"""
        if len(self.measurement_points) != 2:
            return
        point_p = self.measurement_points[0]
        point_q = self.measurement_points[1]
        self.horizontal_points = [point_p, point_q]
        # Calculate distance between P and Q
        distance_meters = np.linalg.norm(point_q - point_p)
        self.horizontal_length_meters = distance_meters
        self.plotting_active = False
        units_suffix, conversion_factor = self.get_current_units()
        distance = distance_meters * conversion_factor
        # Draw main horizontal line (red) and store reference
        self.horizontal_line_actor = self.add_line_between_points(point_p, point_q, "Red", f"PQ={distance:.2f}{units_suffix}")
        # Store reference to the distance label actor (the last added actor)
        if self.measurement_actors:
            self.horizontal_distance_label_actor = self.measurement_actors[-1]
        # Add point markers and store references
        self.point_p_actor = self.add_sphere_marker(point_p, "P")
        self.point_q_actor = self.add_sphere_marker(point_q, "Q")
        # Initialize line_data if it doesn't exist
        if not hasattr(self, 'line_data'):
            self.line_data = {}
        # Store basic line data
        self.line_data = {
            'length': distance,
            'points': {
                'P': point_p,
                'Q': point_q
            }
        }
        # Output results
        self.message_text.append(f"--- Horizontal line ---\n PQ: {distance:.2f} {units_suffix}")
        
# ===========================================================================================================================
# Define function for the Polygon Measurements:
    def process_polygon_measurement(self):
        """Process polygon measurement on any plane using triangulation for area calculation"""
        if len(self.measurement_points) < 3:
            return
        # Store polygon points and actors for saving to JSON later
        self.polygon_points = [p.tolist() for p in self.measurement_points]
        self.polygon_actors = list(self.measurement_actors)
        points = self.measurement_points
        n = len(points)
        # Find the best fitting plane
        centroid, normal = find_best_fitting_plane(points)
        # Get current units
        units_suffix, conversion_factor = self.get_current_units()
        # Project points onto the best-fit plane
        projected_points = []
        for point in points:
            v = point - centroid
            dist = np.dot(v, normal)
            projected = point - dist * normal
            projected_points.append(projected)
        projected_points = np.array(projected_points)
        perimeter_meters = 0.0
        # Calculate all side lengths
        lengths = []
        for i in range(n):
            p1 = projected_points[i]
            p2 = projected_points[(i+1)%n]
            length_meters = np.linalg.norm(p2 - p1)
            perimeter_meters += length_meters
            length = length_meters * conversion_factor
            label = f"{chr(65+i)}{chr(65+(i+1)%n)}"
            lengths.append((label, length))
        # Calculate all internal angles
        angles = []
        for i in range(n):
            a = projected_points[i]
            b = projected_points[(i+1)%n]
            c = projected_points[(i+2)%n]
            ba = a - b
            bc = c - b
            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
            angle = degrees(np.arccos(cosine_angle))
            label = chr(65 + (i+1)%n) # B, C, etc.
            angles.append((label, angle))
        # Calculate area using triangulation (Delaunay triangulation)
        try:
            from scipy.spatial import Delaunay
            # Project points to 2D plane (using the two most significant dimensions)
            abs_normal = np.abs(normal)
            if abs_normal[0] > abs_normal[1] and abs_normal[0] > abs_normal[2]:
                # Most aligned with YZ plane
                coords = projected_points[:, [1, 2]] # Use Y and Z coordinates
            elif abs_normal[1] > abs_normal[2]:
                # Most aligned with XZ plane
                coords = projected_points[:, [0, 2]] # Use X and Z coordinates
            else:
                # Most aligned with XY plane (default)
                coords = projected_points[:, [0, 1]] # Use X and Y coordinates
            # Perform Delaunay triangulation
            tri = Delaunay(coords)
            # Calculate area of each triangle and sum them up
            area_meters = 0.0
            for simplex in tri.simplices:
                # Get the 3 points of the triangle
                a, b, c = projected_points[simplex]
                # Calculate area of triangle using cross product
                area_meters += 0.5 * np.linalg.norm(np.cross(b - a, c - a))
        except ImportError:
            # Fallback to shoelace formula if scipy not available
            self.message_text.append("Note: scipy not available, using shoelace formula instead")
            x = projected_points[:,0]
            y = projected_points[:,1]
            z = projected_points[:,2]
            # Find which plane we're most aligned with
            if abs_normal[0] > abs_normal[1] and abs_normal[0] > abs_normal[2]:
                # Most aligned with YZ plane
                area_meters = 0.5 * np.abs(np.dot(y, np.roll(z,1)) - np.dot(z, np.roll(y,1)))
            elif abs_normal[1] > abs_normal[2]:
                # Most aligned with XZ plane
                area_meters = 0.5 * np.abs(np.dot(x, np.roll(z,1)) - np.dot(z, np.roll(x,1)))
            else:
                # Most aligned with XY plane (default)
                area_meters = 0.5 * np.abs(np.dot(x, np.roll(y,1)) - np.dot(y, np.roll(x,1)))
        # Convert area
        if units_suffix == "cm":
            area = area_meters * 10000
            perimeter = perimeter_meters * 100
            area_suffix = "square cm"
            perimeter_suffix = "cm"
        elif units_suffix == "mm":
            area = area_meters * 1000000
            perimeter = perimeter_meters * 1000
            area_suffix = "square mm"
            perimeter_suffix = "mm"
        else:
            area = area_meters
            perimeter = perimeter_meters
            area_suffix = "square meter"
            perimeter_suffix = "m"
        # Add angle labels to the 3D view
        for i in range(n):
            a = points[i]
            b = points[(i+1)%n]
            c = points[(i+2)%n]
            angle_label = angles[i][1]
            self.add_angle_label(b, a, c, f"{angle_label:.1f}°", offset=0.8)
        # Output results
        self.polygon_area_meters = area_meters
        self.polygon_perimeter_meters = perimeter_meters
        self.message_text.append(f"Polygon Surface Area = {area:.2f} {area_suffix}")
        self.message_text.append(f"Polygon Perimeter = {perimeter:.2f} {perimeter_suffix}")
        
# ==================================================================================================================================
    def complete_polygon(self):
        self.plotting_active = False
        if self.current_measurement != 'polygon' and self.current_measurement != 'round_pillar_polygon':
            return
        if len(self.measurement_points) < 3:
            self.message_text.append("Need at least 3 points to complete a polygon")
            return
        # Connect last point to first point
        p1 = self.measurement_points[-1]
        p2 = self.measurement_points[0]
        # Only add the line if it doesn't already exist
        line_exists = False
        for actor in self.measurement_actors:
            if isinstance(actor.GetMapper().GetInput(), vtk.vtkLineSource):
                pos1 = actor.GetMapper().GetInput().GetPoint(0)
                pos2 = actor.GetMapper().GetInput().GetPoint(1)
                if (np.allclose(pos1, p1) and np.allclose(pos2, p2)) or \
                (np.allclose(pos1, p2) and np.allclose(pos2, p1)):
                    line_exists = True
                    break
        if not line_exists:
            if self.current_measurement == 'round_pillar_polygon':
                self.add_line_between_points(p1, p2, "Purple", show_label=False)
            else:
                self.add_line_between_points(p1, p2, "Purple")
        # Process the polygon measurement
        if self.current_measurement == 'polygon' :
            self.process_polygon_measurement()
        # Hide the Complete Polygon button after completing
        self.complete_polygon_button.setVisible(False)
        self.complete_polygon_button.setStyleSheet("") # Reset to default style
        self.vtk_widget.GetRenderWindow().Render()
        
# ==================================================================================================================================
#Define the function for the handle the Presized button action:
    def handle_presized_button(self):
        """Handle the Presized button click for round pillar measurement."""
        if (hasattr(self, 'current_measurement') and
            self.current_measurement == 'horizontal_line' and
            hasattr(self, 'measurement_points') and
            len(self.measurement_points) >= 2 and
            hasattr(self, 'polygon_area_meters') and
            self.polygon_area_meters > 0):
            try:
                # Get points A and B from the original measurement
                point_p = self.measurement_points[0]
                point_q = self.measurement_points[1]
                point_r = np.array([point_q[0], point_q[1], point_p[2]])
  
                distance_meters = self.create_presized_horizontal_line()
                # Convert to current units
                units_suffix, conversion_factor = self.get_current_units()
                distance_PR = distance_meters * conversion_factor
                # Calculate volume and surface area using the round pillar polygon data
                surface_area_meters = self.polygon_area_meters
                perimeter_meters = self.polygon_perimeter_meters
                volume_meters = surface_area_meters * distance_meters
                outer_surface_meters = perimeter_meters * distance_meters
                self.polygon_volume_meters = volume_meters
                self.polygon_outer_surface_meters = outer_surface_meters
                if hasattr(self, "all_presized_horizontal_lines") and self.all_presized_horizontal_lines:
                    self.all_presized_horizontal_lines[-1]["volume"] = volume_meters
                    self.all_presized_horizontal_lines[-1]["outer_surface"] = outer_surface_meters
                # Convert measurements to current units
                if units_suffix == "cm":
                    surface_area = surface_area_meters * 10000 # m² to cm²
                    volume = volume_meters * 1000000 # m³ to cm³
                    outer_surface = outer_surface_meters * 10000 # m² to cm²
                    perimeter = perimeter_meters * 100
                    area_suffix = "square cm"
                    volume_suffix = "cubic cm"
                    perimeter_suffix = "centi meter"
                elif units_suffix == "mm":
                    surface_area = surface_area_meters * 1000000 # m² to mm²
                    volume = volume_meters * 1000000000 # m³ to mm³
                    outer_surface = outer_surface_meters * 1000000 # m² to mm²
                    perimeter = perimeter_meters * 1000
                    area_suffix = "square mm"
                    volume_suffix = "cubic mm"
                    perimeter_suffix = "mili meter"
                else:
                    surface_area = surface_area_meters
                    volume = volume_meters
                    outer_surface = outer_surface_meters
                    perimeter = perimeter_meters
                    area_suffix = "square meter"
                    volume_suffix = "cubic meter"
                    perimeter_suffix = "meter"
  
                # Calculate centroid for label placement
                if hasattr(self, 'measurement_points') and len(self.measurement_points) >= 3:
                    polygon_points = np.array(self.measurement_points)
                    centroid = np.mean(polygon_points, axis=0)
                else:
                    centroid = (point_p + point_r) / 2
  
                # Add labels for volume and outer surface
                self.add_text_label(centroid + np.array([0, 3, 2]), f"Polygon Volume = {volume:.2f} {volume_suffix}, "f"Polygon Outer Surface = {outer_surface:.2f} {area_suffix}", "Green")
                self.add_text_label(centroid + np.array([0, 3, 1]), f"Polygon Area = {surface_area:.2f} {area_suffix}, "f"Polygon Perimeter = {perimeter:.2f} {perimeter_suffix}", "Green")
                # Output results
                self.message_text.append(f"Surface Area of Polygon = {surface_area:.2f} {area_suffix}\n")
                self.message_text.append(f"Volume of Polygon = {volume:.2f} {volume_suffix}\n")
                self.message_text.append(f"Outer Surface Area of Polygon= {outer_surface:.2f} {area_suffix}")
            except Exception as e:
                self.message_text.append(f"Error creating presized polygon volume measurements")
            self.vtk_widget.GetRenderWindow().Render()
            return
        if (hasattr(self, 'current_measurement') and self.current_measurement == 'vertical_line' and \
            hasattr(self, 'measurement_points') and len(self.measurement_points) >= 2):
            # Vertical line case
            try:
                self.create_presized_vertical_line()
                # self.output_list.addItem("Presized vertical line created")
  
            except Exception as e:
                self.message_text.append(f"Error creating presized vertical line")
        if (hasattr(self, 'current_measurement') and self.current_measurement == 'horizontal_line' and \
            hasattr(self, 'measurement_points') and len(self.measurement_points) >= 2):
            # Horizontal line case
            try:
                self.create_presized_horizontal_line()
                # self.output_list.addItem("Presized horizontal line created")
  
            except Exception as e:
                self.message_text.append(f"Error creating presized horizontal line")
                
# ===========================================================================================================================
# define the function for the create a presized horizontal line::
    def create_presized_horizontal_line(self):
        """Create a new straight horizontal line from point P to point R with offset points in XY, XZ, YZ planes"""
        if not hasattr(self, 'measurement_points') or len(self.measurement_points) < 2:
            return
        try:
            # Get points P and Q from the original measurement
            point_p = self.measurement_points[0]
            point_q = self.measurement_points[1]
            # Create point R: same X, Y as Q but Z as P
            point_r = np.array([point_q[0], point_q[1], point_p[2]])
            # Calculate 3D distance between P and R
            distance_meters = np.linalg.norm(point_r - point_p)
            self.plotting_active = False
            # Store points & length for saving later
            self.presized_horizontal_points = [point_p.tolist(), point_r.tolist()] # [P, R]
            self.presized_horizontal_length_meters = distance_meters
            # Store for multiple saving
            if not hasattr(self, "all_presized_horizontal_lines"):
                self.all_presized_horizontal_lines = []
            self.all_presized_horizontal_lines.append({
                "points": {"P": point_p.tolist(), "R": point_r.tolist()},
                "length_m": distance_meters
            })
            # Convert distance to current units
            units_suffix, conversion_factor = self.get_current_units()
            distance = distance_meters * conversion_factor
            # 1. Change horizontal line color from Red to LightGrey
            if self.horizontal_line_actor is not None:
                self.horizontal_line_actor.GetProperty().SetColor(self.colors.GetColor3d("LightGrey"))
                # self.output_list.addItem("Horizontal line color changed to LightGrey")
            # 2. Change point Q sphere color to LightGrey
            if hasattr(self, 'point_q_actor') and self.point_q_actor is not None:
                self.point_q_actor.GetProperty().SetColor(self.colors.GetColor3d("LightGrey"))
                # self.output_list.addItem("Point Q sphere color changed to LightGrey")
            # 3. Change point Q label color to LightGrey
            for actor in self.measurement_actors:
                if isinstance(actor, vtk.vtkFollower):
                    try:
                        text_source = actor.GetMapper().GetInputConnection(0, 0).GetProducer()
                        if isinstance(text_source, vtk.vtkVectorText) and text_source.GetText() == "Q":
                            actor.GetProperty().SetColor(self.colors.GetColor3d("LightGrey"))
                            # self.output_list.addItem("Point Q label color changed to LightGrey")
                            break
                    except:
                        continue
            # 4. Change distance label color to LightGrey and reposition it above the original PQ line
            if hasattr(self, 'horizontal_distance_label_actor') and self.horizontal_distance_label_actor is not None:
                self.horizontal_distance_label_actor.GetProperty().SetColor(self.colors.GetColor3d("LightGrey"))
                # self.output_list.addItem("Horizontal distance label color changed to LightGrey and repositioned")
            # Draw the new straight horizontal line from P to R in red
            self.presized_horizontal_line_actor = self.add_line_between_points(point_p, point_r, "Red", f"PR={distance:.2f}{units_suffix}")
            # Add point R marker with label
            self.point_r_actor = self.add_sphere_marker(point_r, "R", color="Red")
            return distance_meters
        except Exception as e:
            self.message_text.append(f"Error creating presized horizontal line: {str(e)}")
            
# ===========================================================================================================================
# Define the function for the Create Presized Vertical Line::
    def create_presized_vertical_line(self):
        """Create a new vertical line from point A to point C (same height as B) when Presized is clicked"""
        if not hasattr(self, 'measurement_points') or len(self.measurement_points) < 2:
            return
        try:
            # Get points A and B from the original measurement
            point_a = self.measurement_points[0]
            point_b = self.measurement_points[1]
            # Create point C at the same height as B but directly above A
            point_c = np.array([point_a[0], point_a[1], point_b[2]])
            # Calculate the distance between A and C (vertical height)
            distance_meters = np.linalg.norm(point_c - point_a)
            # Convert distance to current units
            units_suffix, conversion_factor = self.get_current_units()
            distance = distance_meters * conversion_factor
            self.presized_vertical_points = [point_a.tolist(), point_c.tolist()] # [A, C]
            self.presized_height_meters = distance_meters
            # Store for multiple saving
            if not hasattr(self, "all_presized_vertical_lines"):
                self.all_presized_vertical_lines = []
            self.all_presized_vertical_lines.append({
                "points": {"A": point_a.tolist(), "C": point_c.tolist()},
                "height_m": distance_meters
            })
            # 1. Change original AB line color from Red to LightGrey
            if hasattr(self, 'main_line_actor') and self.main_line_actor is not None:
                self.main_line_actor.GetProperty().SetColor(self.colors.GetColor3d("LightGrey"))
                # self.output_list.addItem("Vertical line AB color changed to LightGrey")
            # 2. Change point B sphere color to LightGrey
            if hasattr(self, 'point_b_actor') and self.point_b_actor is not None:
                self.point_b_actor.GetProperty().SetColor(self.colors.GetColor3d("LightGrey"))
                # self.output_list.addItem("Point B sphere color changed to LightGrey")
            # 3. Change point B label color to LightGrey
            for actor in self.measurement_actors:
                if isinstance(actor, vtk.vtkFollower):
                    try:
                        text_source = actor.GetMapper().GetInputConnection(0, 0).GetProducer()
                        if isinstance(text_source, vtk.vtkVectorText) and text_source.GetText() == "B":
                            actor.GetProperty().SetColor(self.colors.GetColor3d("LightGrey"))
                            # self.output_list.addItem("Point B label color changed to LightGrey")
                            break
                    except:
                        continue
            # 4. Change distance label color to LightGrey
            if hasattr(self, 'distance_label_actor') and self.distance_label_actor is not None:
                self.distance_label_actor.GetProperty().SetColor(self.colors.GetColor3d("LightGrey"))
                # self.output_list.addItem("Vertical distance label color changed to LightGrey and repositioned")
            # Draw the new vertical line from A to C in red
            self.presized_line_actor = self.add_line_between_points(point_a, point_c, "Red",f"AC={distance:.2f}{units_suffix}")
            # Add point C marker with label
            self.point_c_actor = self.add_sphere_marker(point_c, "C", color="Red")
            self.message_text.append(f"Presized Vertical Height AC: {distance:.2f} {units_suffix}")
            self.vtk_widget.GetRenderWindow().Render()
            return distance_meters
        except Exception as e:
            self.message_text.append(f"Error creating presized vertical line: {str(e)}")
            
# ==========================================================================================================================
# Define function for Key press handler for Space bar freeze/unfreeze
    def on_key_press(self, obj, event):
        """Handle key press events"""
        key = obj.GetKeySym()
        # Rotation controls
        if key == 'Up':
            self.rotate_up(15)
            return
        elif key == 'Down':
            self.rotate_down(15)
            return
        elif key == 'Right':
            self.rotate_left(15)
            return
        elif key == 'Left':
            self.rotate_right(15)
            return
        # Existing key handling
        if key == 'space': # Space bar for freeze/unfreeze
            self.freeze_view = not self.freeze_view
            interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
            if self.freeze_view:
                interactor.SetInteractorStyle(None) # Disable interaction
                # self.output_list.addItem("View frozen - press Space to unfreeze")
            else:
                # Re-enable default interaction
                style = vtkInteractorStyleTrackballCamera()
                interactor.SetInteractorStyle(style)
                # self.output_list.addItem("View unfrozen")
            self.vtk_widget.GetRenderWindow().Render()

# ============================================================================================================================
# RESET ACTION (Modified)
    def reset_action(self):
        """Reset the current active line type's drawings from the graph"""
        if self.active_line_type:
            # Store the active line type for the message
            active_type_name = self.active_line_type
            
            # Clear current drawing session for the active line type
            self.current_points = []
            if self.current_artist is not None:
                try:
                    self.current_artist.remove()
                except:
                    pass
                self.current_artist = None
            self.current_redo_points = []
            
            # Clear current point labels for the active line type
            for label in self.current_point_labels:
                try:
                    if label in self.ax.texts:
                        label.remove()
                except:
                    pass
            self.current_point_labels = []
            
            # If we have any finished polylines for this active line type, remove them
            if active_type_name in self.line_types:
                # Remove all artists for this line type
                for artist in self.line_types[active_type_name]['artists']:
                    try:
                        if artist in self.ax.lines or artist in self.ax.collections:
                            artist.remove()
                    except:
                        pass
                # Clear the lists
                self.line_types[active_type_name]['artists'] = []
                self.line_types[active_type_name]['polylines'] = []
                
                # Also remove from all_graph_lines
                new_all_graph_lines = []
                for item in self.all_graph_lines:
                    lt, points, artist, ann = item
                    if lt != active_type_name:
                        new_all_graph_lines.append(item)
                    else:
                        # Remove the annotation if it exists
                        if ann:
                            try:
                                ann.remove()
                            except:
                                pass
                self.all_graph_lines = new_all_graph_lines
            
            # Also remove any point labels for this line type
            if active_type_name == 'construction_dots':
                # For construction dots, remove the P1, P2 labels
                texts_to_remove = []
                for text in self.ax.texts:
                    if hasattr(text, 'point_data') and text.point_data.get('line_type') == 'construction_dots':
                        texts_to_remove.append(text)
                
                for text in texts_to_remove:
                    try:
                        text.remove()
                    except:
                        pass
            
            # Redraw canvas
            self.canvas.draw()
            self.figure.tight_layout()
            
            # Reset the checkbox for this line type
            if active_type_name == 'construction':
                self.construction_line.setChecked(False)
            elif active_type_name == 'surface':
                self.surface_baseline.setChecked(False)
            elif active_type_name == 'road_surface':
                self.road_surface_line.setChecked(False)
            elif active_type_name == 'construction_dots':
                self.construction_dots_line.setChecked(False)
            elif active_type_name == 'deck_line':
                self.deck_line.setChecked(False)
            elif active_type_name == 'projection_line':
                self.projection_line.setChecked(False)
            elif active_type_name == 'zero':
                self.zero_line.setChecked(False)
            
            # Format the message
            display_name = active_type_name.replace('_', ' ').title()
            self.message_text.append(f"Reset {display_name} drawings")
            
            # Reset active line type AFTER using it
            self.active_line_type = None
            
            # Disconnect drawing events if connected
            if self.cid_click is not None:
                self.canvas.mpl_disconnect(self.cid_click)
                self.cid_click = None
            if self.cid_key is not None:
                self.canvas.mpl_disconnect(self.cid_key)
                self.cid_key = None
        else:
            self.message_text.append("No active line type to reset. Please select a line type first.")

        # Clear all curve labels
        if hasattr(self, 'curve_labels'):
            for label in self.curve_labels:
                try:
                    label.remove()
                except:
                    pass
            self.curve_labels = []

        if self.curve_pick_id:
            self.canvas.mpl_disconnect(self.curve_pick_id)
            self.curve_pick_id = None

        self.curve_active = False
        self.current_curve_text = ""
        self.curve_start_x = None

        # Reset button
        self.preview_button.setText("Curve")
        self.preview_button.setStyleSheet("""
            QPushButton { background-color: #808080; color: white; padding: 12px; border-radius: 6px;
                          font-size: 15px; font-weight: bold; }
            QPushButton:hover { background-color: #6E6E6E; }
        """)
            
# ============================================================================================================================
# Define the function for the reset all:
    def reset_all(self):
        """Reset ALL lines from the graph"""
        # First call reset_action to handle any current drawing
        self.reset_action()
        
        # Now remove ALL lines from all line types
        for line_type in self.line_types:
            # Remove all artists for this line type
            for artist in self.line_types[line_type]['artists']:
                try:
                    if artist and hasattr(artist, 'remove'):
                        artist.remove()
                except Exception as e:
                    print(f"Error removing artist for {line_type}: {e}")
            
            # Clear the lists
            self.line_types[line_type]['artists'] = []
            self.line_types[line_type]['polylines'] = []
        
        # Clear all_graph_lines
        for lt, points, artist, ann in self.all_graph_lines:
            try:
                if artist and hasattr(artist, 'remove'):
                    artist.remove()
            except:
                pass
            try:
                if ann and hasattr(ann, 'remove'):
                    ann.remove()
            except:
                pass
        
        self.all_graph_lines = []
        self.redo_stack = []
        
        # Clear ALL point labels (not just current ones)
        for label in self.point_labels:
            try:
                if label and label in self.ax.texts:
                    label.remove()
            except:
                pass
        self.point_labels = []
        
        # Clear ALL current point labels
        for label in self.current_point_labels:
            try:
                if label and label in self.ax.texts:
                    label.remove()
            except:
                pass
        self.current_point_labels = []
        
        # Also clear any remaining text objects (including construction dots labels)
        texts_to_remove = []
        for text in self.ax.texts:
            # Keep only the annotation text
            if text != self.annotation:
                texts_to_remove.append(text)
        
        for text in texts_to_remove:
            try:
                text.remove()
            except:
                pass
        
        # Reset zero line if it exists
        if self.zero_line_set:
            if self.zero_graph_line:
                try:
                    self.zero_graph_line.remove()
                except:
                    pass
            
            # Reset zero line variables but keep the line set
            self.zero_graph_line = None
            
            # Redraw the zero line if checkbox is checked
            if self.zero_line.isChecked():
                self.zero_graph_line, = self.ax.plot([0, self.total_distance], [0, 0], 
                                                    color='purple', linewidth=3)
        
        # Uncheck all checkboxes
        self.construction_line.setChecked(False)
        self.surface_baseline.setChecked(False)
        if hasattr(self, 'zero_line'):
            self.zero_line.setChecked(False)
        if hasattr(self, 'road_surface_line'):
            self.road_surface_line.setChecked(False)
        if hasattr(self, 'construction_dots_line'):
            self.construction_dots_line.setChecked(False)
        if hasattr(self, 'deck_line'):
            self.deck_line.setChecked(False)
        if hasattr(self, 'projection_line'):
            self.projection_line.setChecked(False)
        
        # ===== ADD THIS SECTION: Hide road/bridge baseline checkboxes and reset button names =====
        # Reset road baseline

        self.road_surface_container.setVisible(False)
        self.surface_container.setVisible(False)
        self.zero_container.setVisible(False)
        self.construction_container.setVisible(False)
        # Hide bottom section on full reset
        self.bottom_section.setVisible(False)
        
        self.deck_line_container.setVisible(False)
        self.projection_container.setVisible(False)
        if hasattr(self, 'bridge_zero_container'):
            self.bridge_zero_container.setVisible(False)
        if hasattr(self, 'construction_dots_container'):
            self.construction_dots_container.setVisible(False)
        
        # Hide the additional buttons
        self.preview_button.setVisible(False)
        self.threed_map_button.setVisible(False)
        self.save_button.setVisible(False)
        # ===== END OF ADDED SECTION =====
        
        # Reset active line type and drawing state
        self.active_line_type = None
        self.current_points = []
        if self.current_artist is not None:
            try:
                self.current_artist.remove()
            except:
                pass
            self.current_artist = None
        
        # Disconnect drawing events if connected
        if self.cid_click is not None:
            self.canvas.mpl_disconnect(self.cid_click)
            self.cid_click = None
        if self.cid_key is not None:
            self.canvas.mpl_disconnect(self.cid_key)
            self.cid_key = None
        
        # Reset scale section
        if self.zero_line_set:
            # Keep zero line set but update display
            self.update_chainage_ticks()
            if hasattr(self, 'scale_section'):
                self.scale_section.setVisible(True)
        else:
            # Hide scale section
            if hasattr(self, 'scale_section'):
                self.scale_section.setVisible(False)
        
        # Redraw canvas
        self.canvas.draw()
        self.figure.tight_layout()
        
        # Also reset 3D measurements if needed
        self.message_text.append("All graph lines have been reset")
        
        # Call the original measurement reset logic (keeping your existing code)
        # Reset view and plotting states
        self.freeze_view = False
        self.plotting_active = True
        
        # Reset cropped data
        if hasattr(self, 'cropped_cloud'):
            self.cropped_cloud = None
        
        self.current_measurement = None
        
        # Reset curve-related attributes
        if hasattr(self, 'curve_annotation'):
            try:
                if self.curve_annotation and self.curve_annotation in self.ax.texts:
                    self.curve_annotation.remove()
            except:
                pass
            self.curve_annotation = None
        
        if hasattr(self, 'curve_arrow_annotation'):
            try:
                if self.curve_arrow_annotation and self.curve_arrow_annotation in self.ax.patches:
                    self.curve_arrow_annotation.remove()
            except:
                pass
            self.curve_arrow_annotation = None
        
        if hasattr(self, 'curve_pick_id') and self.curve_pick_id:
            try:
                self.canvas.mpl_disconnect(self.curve_pick_id)
            except:
                pass
            self.curve_pick_id = None
        
        if hasattr(self, 'curve_annotation_x_pos'):
            self.curve_annotation_x_pos = None
        
        if hasattr(self, 'current_curve_config'):
            self.current_curve_config = {'outer_curve': False, 'inner_curve': False, 'angle': 0.0}
        
        if hasattr(self, 'preview_button'):
            self.preview_button.setText("Curve")
            self.preview_button.setStyleSheet("""
                QPushButton {
                    background-color: #808080;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #6E6E6E; }
                QPushButton:pressed { background-color: #5A5A5A; }
            """)
    
        self.loaded_file_name = None
        self.loaded_file_path = None
        actors_to_remove = []
        for actor in self.measurement_actors:
            actors_to_remove.append(actor)
        for actor in actors_to_remove:
            self.renderer.RemoveActor(actor)
            if actor in self.measurement_actors:
                self.measurement_actors.remove(actor)
        # Reset point cloud
        if self.point_cloud_actor:
            self.renderer.RemoveActor(self.point_cloud_actor)
            self.point_cloud_actor = None
            self.point_cloud = None
        # Reset UI state
        self.measurement_active = True

        # Hide scale section
        if hasattr(self, 'scale_section'):
            self.scale_section.setVisible(False)

        # Render the VTK window
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.GetRenderWindow().Render()


        # Clear all curve labels
        if hasattr(self, 'curve_labels'):
            for label in self.curve_labels:
                try:
                    label.remove()
                except:
                    pass
            self.curve_labels = []

        if self.curve_pick_id:
            self.canvas.mpl_disconnect(self.curve_pick_id)
            self.curve_pick_id = None

        self.curve_active = False
        self.current_curve_text = ""
        self.curve_start_x = None

        # Reset button
        self.preview_button.setText("Curve")
        self.preview_button.setStyleSheet("""
            QPushButton { background-color: #808080; color: white; padding: 12px; border-radius: 6px;
                          font-size: 15px; font-weight: bold; }
            QPushButton:hover { background-color: #6E6E6E; }
        """)

        # Clear 3D curve actors
        for actor in self.curve_3d_actors:
            self.renderer.RemoveActor(actor)
        self.curve_3d_actors.clear()
        self.curve_start_point_3d = None

# ===========================================================================================================================================================
    def plot_graph(self, x, y):
        if self.ax:
            self.ax.clear()
            self.ax.plot(x, y)
            self.ax.grid(True)
            self.ax.set_title("Sample Graph")
            self.ax.set_xlabel("X-axis")
            self.ax.set_ylabel("Y-axis")
            self.canvas.draw()
            self.figure.tight_layout()
        else:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.plot(x, y)
            ax.set_title("Sample Graph")
            ax.set_xlabel("X-axis")
            ax.set_ylabel("Y-axis")
            ax.grid(True)
            self.canvas.draw()
            self.figure.tight_layout()

# ===========================================================================================================================================
    def preview_lines_on_3d(self):
        if not self.zero_line_set:
            self.message_text.append("Zero line must be set before previewing.")
            return
        has_polylines = any(self.line_types[lt]['polylines'] for lt in ['surface', 'construction', 'road_surface'])
        if not has_polylines:
            self.message_text.append("No lines drawn to preview.")
            return

        # # Clear road planes when previewing to avoid clutter
        # self.clear_road_planes()

        # Clear previous preview actors
        for actor in self.preview_actors:
            self.renderer.RemoveActor(actor)
        self.preview_actors = []

        dir_vec = self.zero_end_point - self.zero_start_point
        p1_z = self.zero_start_z

        for line_type in ['surface', 'construction', 'road_surface']:
            if self.line_types[line_type]['polylines']:
                color = self.line_types[line_type]['color']
                for poly_2d in self.line_types[line_type]['polylines']:
                    points_3d = []
                    for dist, rel_z in poly_2d:
                        t = dist / self.total_distance
                        pos_along = self.zero_start_point + t * dir_vec
                        z_abs = p1_z + rel_z
                        pos_3d = np.array([pos_along[0], pos_along[1], z_abs])
                        points_3d.append(pos_3d)
                    for i in range(len(points_3d) - 1):
                        self.add_preview_line(points_3d[i], points_3d[i + 1], color)
        self.vtk_widget.GetRenderWindow().Render()
        self.message_text.append("Preview lines mapped on 3D point cloud.")

# ===========================================================================================================================================================
    def add_preview_line(self, p1, p2, color):
        line = vtkLineSource()
        line.SetPoint1(p1[0], p1[1], p1[2])
        line.SetPoint2(p2[0], p2[1], p2[2])
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(line.GetOutputPort())
        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(self.colors.GetColor3d(color))
        actor.GetProperty().SetLineWidth(3)
        self.renderer.AddActor(actor)
        self.preview_actors.append(actor)



# =================================================================================================================================
# MAP ROAD BASELINES TO 3D PLANES
    def map_baselines_to_3d_planes(self):
        """
        Main function: Called when user clicks 'Map on 3D' button.
        Creates planes for ALL currently drawn baseline types.
        Planes are ADDED incrementally — previous planes remain visible.
        Each time user draws a new line and clicks 'Map on 3D', new planes are added on top.
        """
        if not self.zero_line_set:
            QMessageBox.warning(self, "Zero Line Required", "Please set the Zero Line first before mapping baselines to planes.")
            self.message_text.append("Zero line must be set.")
            return

        # Collect all current polylines from baseline types
        current_polylines = {}
        new_segment_count = 0
        for ltype in self.baseline_types:
            polylines = self.line_types[ltype]['polylines']
            if polylines:
                current_polylines[ltype] = polylines
                new_segment_count += sum(len(poly) - 1 for poly in polylines if len(poly) >= 2)

        if new_segment_count == 0:
            QMessageBox.information(self, "No New Lines", "No new baseline segments detected since last mapping.\nDraw or modify lines and try again.")
            self.message_text.append("No new baseline segments to map.")
            return

        # Open dialog for width (same width for all this time)
        dialog = RoadPlaneWidthDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return

        width = dialog.get_width()
        half_width = width / 2.0

        self.last_plane_width = width  # Store for saving

        # DO NOT clear previous planes — we want to accumulate!
        # self.clear_baseline_planes()  ← REMOVED INTENTIONALLY

        zero_dir_vec = self.zero_end_point - self.zero_start_point
        zero_length = self.total_distance
        ref_z = self.zero_start_z

        plane_count_this_time = 0

        for ltype, polylines in current_polylines.items():
            rgba = self.plane_colors.get(ltype, (0.5, 0.5, 0.5, 0.4))
            color_rgb = rgba[:3]
            opacity = rgba[3]

            for poly_2d in polylines:
                if len(poly_2d) < 2:
                    continue

                for i in range(len(poly_2d) - 1):
                    dist1, rel_z1 = poly_2d[i]
                    dist2, rel_z2 = poly_2d[i + 1]

                    pos1 = self.zero_start_point + (dist1 / zero_length) * zero_dir_vec
                    pos2 = self.zero_start_point + (dist2 / zero_length) * zero_dir_vec

                    z1 = ref_z + rel_z1
                    z2 = ref_z + rel_z2

                    center1 = np.array([pos1[0], pos1[1], z1])
                    center2 = np.array([pos2[0], pos2[1], z2])

                    seg_dir = center2 - center1
                    seg_len = np.linalg.norm(seg_dir)
                    if seg_len < 1e-6:
                        continue
                    seg_unit = seg_dir / seg_len

                    # Compute horizontal perpendicular direction
                    horiz = np.array([seg_unit[0], seg_unit[1], 0.0])
                    hlen = np.linalg.norm(horiz)
                    if hlen < 1e-6:
                        # Fallback: perpendicular to zero line
                        zero_unit = zero_dir_vec / np.linalg.norm(zero_dir_vec)
                        perp = np.array([-zero_unit[1], zero_unit[0], 0.0])
                    else:
                        horiz /= hlen
                        perp = np.array([-horiz[1], horiz[0], 0.0])

                    # Normalize perp just in case
                    perp_len = np.linalg.norm(perp)
                    if perp_len > 0:
                        perp /= perp_len

                    # Four corners of the plane segment
                    c1 = center1 + perp * half_width
                    c2 = center1 - perp * half_width
                    c3 = center2 - perp * half_width
                    c4 = center2 + perp * half_width

                    # Create rectangular plane
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

                    # Add to scene and store
                    self.renderer.AddActor(actor)
                    self.baseline_plane_actors.append(actor)
                    plane_count_this_time += 1

        # Final render
        self.vtk_widget.GetRenderWindow().Render()

        # Feedback
        total_planes = len(self.baseline_plane_actors)
        self.message_text.append(f"Added {plane_count_this_time} new plane segments (width: {width:.2f}m). Total visible: {total_planes}")
        
        QMessageBox.information(
            self,
            "Planes Added Successfully",
            f"Added {plane_count_this_time} new plane segments in this mapping.\n"
            f"Width: {width:.2f} m (±{half_width:.2f} m each side)\n\n"
            f"Total planes now visible: {total_planes}\n\n"
            "You can continue drawing more lines and click 'Map on 3D' again — "
            "new planes will be added without removing old ones.\n\n"
            "Color Guide:\n"
            "• Surface → Green\n"
            "• Construction → Red\n"
            "• Road Surface → Blue\n"
            "• Deck Line → Orange\n"
            "• Projection → Purple\n"
            "• Material → Yellow"
        )

# ===========================================================================================================================================================
    def clear_baseline_planes(self):
        """Remove ALL accumulated baseline plane actors — used only on reset or new worksheet."""
        for actor in self.baseline_plane_actors:
            if actor.GetRenderer():
                self.renderer.RemoveActor(actor)
        self.baseline_plane_actors.clear()
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.GetRenderWindow().Render()

# ================================================================================================================================

    def changeEvent(self, event):
        super(PointCloudViewer, self).changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            state = self.windowState()
            if state == Qt.WindowMaximized:
                if self.point_cloud and self.renderer:
                    self.renderer.ResetCamera()
                    if self.vtk_widget:
                        self.vtk_widget.GetRenderWindow().Render()
            elif state == Qt.WindowMinimized:
                pass # No specific action needed for minimize

# =================================================================================================================================
    def resizeEvent(self, event):
        super(PointCloudViewer, self).resizeEvent(event)
        if self.vtk_widget:
            self.vtk_widget.GetRenderWindow().Render()

# =================================================================================================================================
    def load_point_cloud_from_path(self, file_path: str):
        """
        Load a point cloud from a given file path without showing QFileDialog.
        Used for auto-loading point clouds linked to a project after creating a new worksheet.
        Reuses the same logic as load_point_cloud() for consistency.
        """
        if not file_path or not os.path.exists(file_path):
            self.message_text.append(f"Point cloud file not found or invalid: {file_path}")
            return False

        try:
            # Store the loaded file path and name
            self.loaded_file_path = file_path
            self.loaded_file_name = os.path.splitext(os.path.basename(file_path))[0]

            # Show progress bar with file info
            self.show_progress_bar(file_path)
            self.update_progress(10, "Starting file loading...")

            # Read the file
            if file_path.lower().endswith(('.ply', '.pcd')):
                self.update_progress(30, "Loading point cloud data...")
                self.point_cloud = o3d.io.read_point_cloud(file_path)

            elif file_path.lower().endswith('.xyz'):
                self.update_progress(30, "Loading XYZ data...")
                data = np.loadtxt(file_path, usecols=(0, 1, 2))
                self.point_cloud = o3d.geometry.PointCloud()
                self.point_cloud.points = o3d.utility.Vector3dVector(data[:, :3])

            else:
                raise ValueError(f"Unsupported file format: {os.path.splitext(file_path)[1]}")

            if not self.point_cloud.has_points():
                raise ValueError("No points found in the file.")

            if self.point_cloud.has_colors():
                self.update_progress(70, "Processing colors...")
            else:
                self.update_progress(70, "Preparing visualization...")

            self.update_progress(90, "Creating visualization...")
            self.display_point_cloud()

            self.update_progress(100, "Loading complete!")
            QTimer.singleShot(500, self.hide_progress_bar)

            self.message_text.append(f"Successfully loaded point cloud: {os.path.basename(file_path)}")
            return True

        except Exception as e:
            self.hide_progress_bar()
            self.message_text.append(f"Failed to load point cloud '{os.path.basename(file_path)}': {str(e)}")
            QMessageBox.warning(self, "Load Failed", f"Could not load point cloud:\n{file_path}\n\nError: {str(e)}")
            return False
        

# ===========================================================================================================================================================
    def focus_camera_on_full_cloud(self):
        """Focus camera on the entire point cloud"""
        if not self.point_cloud or not self.point_cloud_actor:
            return
        try:
            bounds = self.point_cloud_actor.GetBounds()
            if bounds[0] >= bounds[1]:  # Invalid bounds
                return
            center = [(bounds[0] + bounds[1]) / 2,
                      (bounds[2] + bounds[3]) / 2,
                      (bounds[4] + bounds[5]) / 2]
            size_x = bounds[1] - bounds[0]
            size_y = bounds[3] - bounds[2]
            size_z = bounds[5] - bounds[4]
            avg_size = (size_x + size_y + size_z) / 3.0

            camera = self.renderer.GetActiveCamera()
            camera.SetFocalPoint(*center)
            offset = avg_size * 1.8  # Slightly farther for full view
            camera.SetPosition(center[0] + offset, center[1], center[2] + offset * 0.2)
            camera.SetViewUp(0, 0, 1)
            camera.SetViewAngle(15.0)
            self.renderer.ResetCameraClippingRange()
            self.vtk_widget.GetRenderWindow().Render()
        except Exception as e:
            print(f"Error in full cloud focus: {e}")

# ===========================================================================================================================================================
    def update_camera_view(self, slider_value):
        """Update camera to always look at the current slider marker (red sphere) from a fixed side view."""
        if not self.zero_line_set or not self.point_cloud:
            self.focus_camera_on_full_cloud()
            return

        try:
            # Calculate current position along the zero line
            fraction = slider_value / 100.0
            current_dist = fraction * self.total_distance

            dir_vec = self.zero_end_point - self.zero_start_point
            unit_dir = dir_vec / np.linalg.norm(dir_vec)

            # World position of the marker (on the zero line at reference elevation)
            pos_along = self.zero_start_point + fraction * dir_vec
            marker_pos = np.array([pos_along[0], pos_along[1], self.zero_start_z])

            # Add or update the red sphere marker
            self.add_or_update_slider_marker(marker_pos)

            # Define camera distance and offset (side view, slightly elevated)
            camera_distance = max(self.total_distance * 0.6, 30.0)  # Scale with project size, min 30m
            elevation_offset = camera_distance * 0.2  # Slight upward angle

            # Camera position: offset perpendicular to the zero line direction (to the right side)
            # Compute horizontal perpendicular vector (rotate zero direction 90° clockwise in XY)
            zero_horizontal = np.array([unit_dir[0], unit_dir[1], 0.0])
            h_len = np.linalg.norm(zero_horizontal)
            if h_len < 1e-6:
                perp = np.array([0.0, 1.0, 0.0])
            else:
                perp = np.array([-zero_horizontal[1], zero_horizontal[0], 0.0]) / h_len

            camera_pos = marker_pos + perp * camera_distance
            camera_pos[2] += elevation_offset  # Lift camera a bit for better view

            # Set camera
            camera = self.renderer.GetActiveCamera()
            camera.SetFocalPoint(marker_pos[0], marker_pos[1], marker_pos[2])
            camera.SetPosition(camera_pos[0], camera_pos[1], camera_pos[2])
            camera.SetViewUp(0.0, 0.0, 1.0)  # Keep up vector as +Z
            camera.SetViewAngle(10.0)       # Reasonable field of view

            # Optional: slightly tighter clipping for cleaner view
            self.renderer.ResetCameraClippingRange()

            self.vtk_widget.GetRenderWindow().Render()

        except Exception as e:
            print(f"Error updating camera view: {e}")
            self.focus_camera_on_full_cloud()

# ===========================================================================================================================================================
    def volume_changed(self, value):
        """Main handler when volume slider moves – keeps marker and camera perfectly aligned."""
        print(f"Volume slider changed to: {value}%")

        if self.zero_line_set:
            # Update scale marker and chainage label
            self.update_scale_marker()

            # Update main graph vertical marker
            self.update_main_graph_marker(value)

            # **CRITICAL**: Update camera to follow the red sphere marker exactly
            self.update_camera_view(value)

        else:
            # No zero line → show full cloud and remove marker
            self.focus_camera_on_full_cloud()
            self.remove_slider_marker()

        # Always scroll the 2D graph horizontally
        self.scroll_graph_with_slider(value)

# ===========================================================================================================================================================
    def add_or_update_slider_marker(self, world_pos):
        """Create or move the red sphere that marks the current slider/chainage position"""
        if self.slider_marker_actor is None:
            # Create new sphere
            sphere = vtkSphereSource()
            sphere.SetRadius(self.slider_marker_radius)
            sphere.SetThetaResolution(32)
            sphere.SetPhiResolution(32)

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())

            self.slider_marker_actor = vtkActor()
            self.slider_marker_actor.SetMapper(mapper)
            self.slider_marker_actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # Red
            self.slider_marker_actor.GetProperty().SetOpacity(0.9)

            self.renderer.AddActor(self.slider_marker_actor)

        # Always update position
        self.slider_marker_actor.SetPosition(world_pos[0], world_pos[1], world_pos[2])
        self.vtk_widget.GetRenderWindow().Render()

    def remove_slider_marker(self):
        """Remove the slider position sphere from the scene"""
        if self.slider_marker_actor is not None:
            self.renderer.RemoveActor(self.slider_marker_actor)
            self.slider_marker_actor = None
            self.vtk_widget.GetRenderWindow().Render()

# ============================================================================================================================

    def save_current_design_layer(self):
        """Save all currently drawn and checked baselines as JSON files in the current design layer folder."""
        if not hasattr(self, 'current_worksheet_name') or not self.current_worksheet_name:
            QMessageBox.warning(self, "No Worksheet", "No active worksheet found. Create or open a worksheet first.")
            return

        if not hasattr(self, 'current_layer_name') or not self.current_layer_name:
            QMessageBox.warning(self, "No Layer", "No active design layer. Please create a new design layer first.")
            return

        # Get the design layer folder
        layer_folder = os.path.join(
            self.WORKSHEETS_BASE_DIR,
            self.current_worksheet_name,
            "designs",
            self.current_layer_name
        )

        if not os.path.exists(layer_folder):
            QMessageBox.critical(self, "Folder Missing", f"Design layer folder not found:\n{layer_folder}")
            return

        if not self.zero_line_set:
            QMessageBox.warning(self, "Zero Line Required", "Zero line must be set before saving baselines.")
            return

        # Track what was saved
        saved_count = 0
        saved_files = []

        # Direction vector and reference
        dir_vec = self.zero_end_point - self.zero_start_point
        zero_length = self.total_distance
        ref_z = self.zero_start_z

        # Last used width (we'll use the most recent one from mapping; fallback to 10.0)
        last_width = getattr(self, 'last_plane_width', 10.0)

        # Define baseline types to save (only if checkbox is checked)
        baseline_checkboxes = {
            'surface': self.surface_baseline,
            'construction': self.construction_line,
            'road_surface': self.road_surface_line,
            'deck_line': self.deck_line,
            'projection_line': self.projection_line,
        }

        for ltype, checkbox in baseline_checkboxes.items():
            if not checkbox.isChecked():
                continue

            polylines = self.line_types[ltype]['polylines']
            if not polylines:
                continue

            # Prepare data structure
            baseline_data = {
                "baseline_type": ltype.replace('_', ' ').title(),
                "baseline_key": ltype,
                "color": self.line_types[ltype]['color'],
                "width_meters": last_width,
                "zero_line_start": self.zero_start_point.tolist(),
                "zero_line_end": self.zero_end_point.tolist(),
                "zero_start_elevation": float(ref_z),
                "total_chainage_length": float(zero_length),
                "polylines": []
            }

            # Convert each polyline
            for poly_2d in polylines:
                poly_3d_points = []
                for dist, rel_z in poly_2d:
                    t = dist / zero_length
                    pos_along = self.zero_start_point + t * dir_vec
                    abs_z = ref_z + rel_z
                    world_point = [float(pos_along[0]), float(pos_along[1]), float(abs_z)]

                    poly_3d_points.append({
                        "chainage_m": float(dist),
                        "relative_elevation_m": float(rel_z),
                        "world_coordinates": world_point
                    })

                if len(poly_3d_points) >= 2:
                    start_chainage = poly_3d_points[0]["chainage_m"]
                    end_chainage = poly_3d_points[-1]["chainage_m"]
                    baseline_data["polylines"].append({
                        "start_chainage_m": float(start_chainage),
                        "end_chainage_m": float(end_chainage),
                        "points": poly_3d_points
                    })

            if not baseline_data["polylines"]:
                continue

            # Save to JSON file named after baseline type
            json_filename = f"{ltype}_baseline.json"
            json_path = os.path.join(layer_folder, json_filename)

            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(baseline_data, f, indent=4, ensure_ascii=False)

                saved_count += 1
                saved_files.append(json_filename)

            except Exception as e:
                QMessageBox.critical(self, "Save Failed", f"Could not save {json_filename}:\n{str(e)}")
                self.message_text.append(f"Error saving {ltype}: {str(e)}")
                return

        # Final feedback
        if saved_count > 0:
            file_list = "\n".join([f"• {f}" for f in saved_files])
            self.message_text.append(f"Saved {saved_count} baseline(s) to design layer '{self.current_layer_name}':")
            self.message_text.append(file_list)
            self.message_text.append(f"Location: {layer_folder}")

            QMessageBox.information(
                self,
                "Save Successful",
                f"Successfully saved {saved_count} baseline(s):\n\n{file_list}\n\n"
                f"Folder:\n{layer_folder}\n\n"
                "You can now close or continue editing."
            )
        else:
            QMessageBox.information(self, "Nothing to Save", "No checked baselines with drawn lines found to save.")
            self.message_text.append("No baselines saved (none checked or drawn).")


# ==============================================================================================================================================
    def open_zero_line_dialog(self, auto_opened=False):
            """Open Zero Line Configuration Dialog — called manually or automatically"""
            # Pass current values if already set
            p1 = self.zero_start_point if self.zero_line_set else None
            p2 = self.zero_end_point if self.zero_line_set else None

            km1 = getattr(self, 'zero_start_km', None)
            km2 = getattr(self, 'zero_end_km', None)
            interval = getattr(self, 'zero_interval', 20.0)

            dialog = ZeroLineDialog(
                point1=p1, point2=p2,
                km1=km1, km2=km2,
                interval=interval,
                parent=self
            )

            if dialog.exec_() == QDialog.Accepted:
                p1, p2 = dialog.get_points()
                if p1 is None or p2 is None:
                    QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric coordinates.")
                    if auto_opened:
                        self.zero_line.setChecked(False)
                    return

                try:
                    km1_text = dialog.km1_edit.text().strip()
                    km2_text = dialog.km2_edit.text().strip()
                    interval_text = dialog.interval_edit.text().strip()

                    self.zero_start_km = int(km1_text) if km1_text else None
                    self.zero_end_km = int(km2_text) if km2_text else None
                    self.zero_interval = float(interval_text) if interval_text else 20.0
                except ValueError:
                    QMessageBox.warning(self, "Invalid Input", "KM must be integer, interval must be a number.")
                    if auto_opened:
                        self.zero_line.setChecked(False)
                    return

                # Update zero line state
                self.zero_start_point = p1
                self.zero_end_point = p2
                self.zero_start_z = p1[2]  # Reference elevation from Point 1 Z
                self.zero_line_set = True

                dir_vec = p2 - p1
                self.total_distance = np.linalg.norm(dir_vec)
                self.original_total_distance = self.total_distance

                # Update graph axis and ticks
                self.update_chainage_ticks()
                if hasattr(self, 'scale_section'):
                    self.scale_section.setVisible(True)

                # Redraw zero line on 2D graph
                if hasattr(self, 'zero_graph_line') and self.zero_graph_line:
                    self.zero_graph_line.remove()
                self.zero_graph_line, = self.ax.plot([0, self.total_distance], [0, 0],
                                                    color='purple', linewidth=3, label='Zero Line')
                self.canvas.draw()

                # Refresh 3D view
                if hasattr(self, 'vtk_widget'):
                    self.vtk_widget.GetRenderWindow().Render()

                # === CRITICAL: Save zero line config to current design layer ===
                success = self.save_zero_line_config_to_current_layer()
                if success:
                    self.message_text.append("Zero line successfully configured and saved to current layer!")

                # User feedback
                feedback = [
                    "Zero Line Set Successfully!",
                    f"   • Length: {self.total_distance:.2f} m",
                    f"   • Interval: {self.zero_interval:.1f} m",
                ]
                if self.zero_start_km is not None:
                    feedback.append(f"   • Start KM: {self.zero_start_km}+000")
                if self.zero_end_km is not None:
                    feedback.append(f"   • End KM: {self.zero_end_km}+{int(self.total_distance):03d}")
                for line in feedback:
                    self.message_text.append(line)

            else:
                # Dialog canceled
                if auto_opened and not self.zero_line_set:
                    self.zero_line.setChecked(False)
                self.message_text.append("Zero line configuration canceled.")

# ========================================================================================================================================================
    def get_current_design_layer_path(self):
        """Return path to current active design layer, fallback to worksheet root"""
        if not hasattr(self, 'current_worksheet_name') or not self.current_worksheet_name:
            self.message_text.append("No active worksheet — cannot save zero line config.")
            return None
        worksheet_path = os.path.join(self.WORKSHEETS_BASE_DIR, self.current_worksheet_name)
        if hasattr(self, 'current_layer_name') and self.current_layer_name:
            layer_path = os.path.join(worksheet_path, "designs", self.current_layer_name)
            if os.path.exists(layer_path):
                return layer_path
            else:
                self.message_text.append(f"Design layer folder not found: {layer_path}")
                self.message_text.append("Saving zero_line_config.json in worksheet root.")
        return worksheet_path

# =========================================================================================================================================================
    def save_zero_line_config_to_current_layer(self):
        """Save zero line configuration as JSON in current design layer or worksheet root"""
        save_path = self.get_current_design_layer_path()
        if not save_path:
            return False

        zero_config = {
            "zero_line_set": True,
            "point1": {
                "coordinates": self.zero_start_point.tolist(),
                "km": self.zero_start_km if (hasattr(self, 'zero_start_km') and self.zero_start_km is not None) else None,
                "chainage_m": 0.0
            },
            "point2": {
                "coordinates": self.zero_end_point.tolist(),
                "km": self.zero_end_km if (hasattr(self, 'zero_end_km') and self.zero_end_km is not None) else None,
                "chainage_m": float(self.total_distance)
            },
            "total_length_m": float(self.total_distance),
            "interval_m": float(self.zero_interval),
            "reference_elevation_z": float(self.zero_start_z),
            "saved_at": datetime.now().isoformat(),
            "saved_by": getattr(self, 'current_user', 'unknown')
        }

        json_path = os.path.join(save_path, "zero_line_config.json")
        try:
            os.makedirs(save_path, exist_ok=True)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(zero_config, f, indent=4, ensure_ascii=False)
            self.message_text.append("Zero line configuration saved to:")
            self.message_text.append(f"   {json_path}")
            return True
        except Exception as e:
            error_msg = f"Failed to save zero_line_config.json: {str(e)}"
            self.message_text.append(error_msg)
            QMessageBox.critical(self, "Save Failed", error_msg)
            return False
        
# ========================================================================================================================================
#                                                   *** END OF APPLICAATION ***
# =======================================================================================================================================      