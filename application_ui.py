# Application_UI.py
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QWidget, QGroupBox, 
    QFrame, QPushButton, QSizePolicy, QTextEdit, QCheckBox, QScrollArea, QSlider

)
from PyQt5.QtCore import Qt, QByteArray, QSize, QRectF, QTimer, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QIcon, QFont
from PyQt5.QtSvg import QSvgRenderer

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

# VTK imports
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import (vtkRenderer)
from vtkmodules.vtkCommonColor import vtkNamedColors

# =====================================================================================================================================
#                                               ***  CLASS - Appilcation UI Constructor ***
# =====================================================================================================================================
class ApplicationUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.point_cloud = None
        self.vtk_widget = None
        self.renderer = None
        self.message_section = None
        self.message_text = None
        self.message_visible = False
        self.canvas = None
        self.ax = None
        self.scale_ax = None # For scale graph
        self.start_point = None
        self.end_point = None
        self.total_distance = 100.0
        self.original_total_distance = self.total_distance
        self.zero_line_actor = None
        self.zero_start_actor = None
        self.zero_end_actor = None
        self.zero_graph_line = None
        self.zero_line_set = False
        self.zero_start_point = None
        self.zero_end_point = None
        self.zero_start_km = None
        self.zero_start_chain = None
        self.zero_end_km = None
        self.zero_end_chain = None
        self.zero_interval = None
        self.zero_physical_dist = 0.0
        self.zero_start_z = 0.0 # Reference zero elevation (Z of Point_1)
        self.drawing_zero_line = False
        self.zero_points = []
        self.temp_zero_actors = []
        self.line_types = {
            'construction': {'color': 'red', 'polylines': [], 'artists': []},
            'surface': {'color': 'green', 'polylines': [], 'artists': []},
            'zero': {'color':'purple', 'polylines': [], 'artists':[]},
            'road_surface': {'color': 'blue', 'polylines': [], 'artists': []},
            'deck_line': {'color': 'blue', 'polylines': [], 'artists': []},
            'projection_line': {'color': 'green', 'polylines': [], 'artists': []},
            'construction_dots': {'color': 'red', 'polylines': [], 'artists': []},
            'material': {'color': 'orange', 'polylines': [], 'artists': []}
        }
        self.active_line_type = None
        self.current_points = []
        self.current_artist = None
        self.cid_click = None
        self.cid_key = None

# --------------------------------------------------------------------------------------------------------------------------------
        self.PENCIL_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
        viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 20h9"/> <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
        </svg>"""

# --------------------------------------------------------------------------------------------------------------------------------
        self.svg_left = b"""<svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M15 18L9 12L15 6" stroke="white" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>"""
        self.svg_right = b"""<svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M9 6L15 12L9 18" stroke="white" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>"""
# --------------------------------------------------------------------------------------------------------------------------------
        # Initialization for the saving the line actor, points actor
        self.measurement_actors = []
        self.measurement_points = []
        self.point_cloud = None
        self.point_cloud_actor = None
        # Colors
        self.colors = vtkNamedColors()
        self.measurement_active = True
        self.current_measurement = None
        self.measurement_started = False
        self.main_line_actor = None
        self.point_a_actor = None
        self.point_b_actor = None

        self.current_vertical_points = []        # stores the two points of the current vertical line
        self.is_presized_mode = False
        # Initialize actors for horizontal line measurement
        self.horizontal_line_actor = None
        self.point_p_actor = None
        self.point_q_actor = None
        self.horizontal_distance_label_actor = None
        # To save and load actors
        self.vertical_points = [] # for vertical line
        self.horizontal_points = [] # for horizontal line
        # For polygon
        self.polygon_points = []
        self.polygon_actors = []
        self.vertical_height_meters = 0.0 # Store vertical height
        self.distance_label_actor = None # Store distance label actor
        self.polygon_area_meters = 0.0 # Store polygon Surface Area
        self.horizontal_length_meters = 0.0 # Store horizontal length
        self.polygon_perimeter_meters = 0.0
        self.polygon_volume_meters = 0.0
        self.polygon_outer_surface_meters = 0.0
        self.presized_volume = 0.0
        self.presized_outer_surface = 0.0
        # NEW: View control states
        self.freeze_view = False # Track if view is frozen
        self.plotting_active = True # Track if plotting is active
        self.preview_actors = []
        self.all_graph_lines = []
        self.redo_stack = []
        self.current_redo_points = []

        # Initialize the list to track items
        self.material_items = []  # Important: add this in __init__ or here

        # Add this new variable to store point labels
        self.point_labels = []  # For storing point label annotations
        self.current_point_labels = []  # For current drawing session

        self.three_D_layers_layout = None
        self.two_D_layers_layout = None

        # ADD THESE TWO LINES
        self.three_D_frame = None   # Will hold the 3D Layers frame
        self.two_D_frame = None     # Will hold the 2D Layers frame

        self.current_worksheet_name = None
        self.current_project_name = None

        # Worksheet display area (top of left panel)
        self.worksheet_display = QGroupBox("Current Worksheet")

        self.worksheet_display.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #7B1FA2;
                border-radius: 10px;
                margin: 0px;           /* ← THIS was 10px → creates the gap */
                margin-top: 20px;      /* ← Keeps the title nicely spaced above the border */
                padding: 10px 10px 10px 10px;
                background-color: rgba(225, 190, 231, 0.3);
                color: #4A148C;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                background-color: white;           /* optional: makes title background clean */
            }
        """)
        worksheet_info_layout = QVBoxLayout(self.worksheet_display)
        self.worksheet_info_label = QLabel("No worksheet loaded")
        self.worksheet_info_label.setWordWrap(True)
        self.worksheet_info_label.setAlignment(Qt.AlignCenter)
        self.worksheet_info_label.setStyleSheet("font-size: 13px; color: #333;")
        worksheet_info_layout.addWidget(self.worksheet_info_label)
        self.worksheet_display.setVisible(False)


        self.initUI()
        self.create_progress_bar()

        # Add curve-related attributes here:
        self.curve_annotation = None
        self.curve_arrow_annotation = None
        self.curve_pick_id = None
        self.curve_annotation_x_pos = None
        self.current_curve_config = {'outer_curve': False, 'inner_curve': False, 'angle': 0.0}

        # To store the last point of the surface line (for curve annotation)
        self.last_surface_point_x = None

        self.curve_annotation_x_pos = None  # To remember where it is placed

        # ADD THESE NEW VARIABLES (near other self. variables)
        self.curve_pick_id = None  # For clickable annotation
        self.curve_annotation = None
        self.curve_arrow_annotation = None
        self.current_curve_config = {'outer_curve': False, 'inner_curve': False, 'angle': 0.0}
        self.curve_active = False  # NEW: Track if a curve is currently active

        # Add these attributes
        self.current_mode = None  # 'road' or 'bridge'
        self.road_lines_data = {}  # Store road lines when switching to bridge
        self.bridge_lines_data = {}  # Store bridge lines when switching to road

        # Add these to the __init__ method
        self.road_lines_data = {
            'construction': {'polylines': [], 'artists': []},
            'surface': {'polylines': [], 'artists': []},
            'road_surface': {'polylines': [], 'artists': []},
            'zero': {'polylines': [], 'artists': []}
        }

        self.bridge_lines_data = {
            'deck_line': {'polylines': [], 'artists': []},
            'projection_line': {'polylines': [], 'artists': []},
            'construction_dots': {'polylines': [], 'artists': []},
            'zero': {'polylines': [], 'artists': []}
        }

        self.current_mode = None 

        # In the __init__ method, add these attributes:
        self.last_click_time = 0
        self.double_click_threshold = 0.5

        self.construction_dot_artists = [] 

        self.material_items = []

        # Create a layout for material items if it doesn't exist
        if not hasattr(self, 'material_items_layout'):
            self.material_items_layout = QVBoxLayout()
            self.material_items_layout.setContentsMargins(0, 0, 0, 0)
            self.material_items_layout.setSpacing(5)
            
            # Create a widget to hold the material items
            material_items_widget = QWidget()
            material_items_widget.setLayout(self.material_items_layout)

# ========================================================================================================================================================
#                                                           *** Application UI Function ***
# =========================================================================================================================================================
    def initUI(self):
        self.setWindowTitle('Point Cloud Viewer')
        self.setGeometry(100, 100, 1200, 800)
        
        # Main vertical layout for the entire window
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)
        
        # -----------------------------------------------------------------
        # TOP SECTION – Toolbar
        # ------------------------------------------------------------------
        top_section = QFrame()
        top_section.setFrameStyle(QFrame.Box | QFrame.Raised)
        top_section.setFixedHeight(80)
        top_section.setStyleSheet("""
            QFrame {
                border: 3px solid #8F8F8F;
                border-radius: 10px;
                background-color: #8FBFEF;
            }
        """)
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(10, 5, 10, 5)
        top_layout.setSpacing(15)
        top_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Title (hamburger)
        top_title = QLabel("☰ Menu")
        top_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        top_layout.addWidget(top_title)

        # ------------------------------------------------------------------
        # Helper: create a button with dropdown (New / Existing)
        # ------------------------------------------------------------------
        def create_dropdown_button(text, emoji, width=120):
            btn = QPushButton(f"{emoji} {text}")
            btn.setFixedWidth(width)
            btn.setCheckable(True)

            # Dropdown widget (the little box that appears below)
            dropdown = QWidget()
            dropdown.setWindowFlags(Qt.Popup)
            dropdown_layout = QVBoxLayout(dropdown)
            dropdown_layout.setContentsMargins(4, 4, 4, 4)
            dropdown_layout.setSpacing(2)

            btn_new = QPushButton("New")
            btn_existing = QPushButton("Existing")
            btn_new.setFixedHeight(40)
            btn_new.setFixedWidth(100)
            btn_existing.setFixedWidth(100)
            btn_existing.setFixedHeight(40)

            dropdown_layout.addWidget(btn_new)
            dropdown_layout.addWidget(btn_existing)

            # Connect (you can change these slots to your real functions)
            btn_new.clicked.connect(lambda: self.on_dropdown_choice(btn, "New"))
            btn_existing.clicked.connect(lambda: self.on_dropdown_choice(btn, "Existing"))

            # Show/hide logic
            def toggle():
                if btn.isChecked():
                    # close any other open dropdown first
                    for other in [self.worksheet_button, self.design_button,
                                self.construction_button, self.measurement_button]:
                        if other is not btn and other.isChecked():
                            other.setChecked(False)
                            other.property("dropdown").hide()

                    # position exactly under the button
                    pos = btn.mapToGlobal(QPoint(0, btn.height()))
                    dropdown.move(pos)
                    dropdown.show()
                    btn.setProperty("dropdown", dropdown)
                else:
                    dropdown.hide()

            btn.clicked.connect(toggle)

            # Close when clicking outside
            dropdown.installEventFilter(self)

            return btn, dropdown, btn_new, btn_existing
        
        # ------------------------------------------------------------------
        # Create Project Button
        # ------------------------------------------------------------------
        self.create_project_button = QPushButton("➕ \n Create Project"
                                        )
        self.create_project_button.setStyleSheet("font-weight: bold;")
        self.create_project_button.setFixedWidth(130)
        # self.create_project_button.clicked.connect(self.open_create_project_dialog)
        top_layout.addWidget(self.create_project_button)

        # ------------------------------------------------------------------
        # Worksheet button + dropdown
        # ------------------------------------------------------------------
        (self.worksheet_button, dropdown1,
        self.new_worksheet_button, self.existing_worksheet_button) = create_dropdown_button(
            "\n Worksheet", "📊", width=130)
        self.worksheet_button.setStyleSheet("font-weight: bold;")
        # self.new_worksheet_button.clicked.connect(self.open_new_worksheet_dialog)
        top_layout.addWidget(self.worksheet_button)

        # ------------------------------------------------------------------
        # Design button + dropdown
        # ------------------------------------------------------------------
        (self.design_button, dropdown2,
        self.new_design_button, self.existing_design_button) = create_dropdown_button(
            "\n Design", "📐", width=130)
        self.design_button.setStyleSheet("font-weight: bold;")
        # self.new_design_button.clicked.connect(self.open_create_new_design_layer_dialog)
        top_layout.addWidget(self.design_button)

        # ------------------------------------------------------------------
        # Construction button + dropdown
        # ------------------------------------------------------------------
        (self.construction_button, dropdown3,
        self.new_construction_button, self.existing_construction_button) = create_dropdown_button(
            "\n Construction", "🏗", width=150)
        self.construction_button.setStyleSheet("font-weight: bold;")
        # self.new_construction_button.clicked.connect(self.open_construction_layer_dialog)
        top_layout.addWidget(self.construction_button)

        # ------------------------------------------------------------------
        # Measurement button + dropdown
        # ------------------------------------------------------------------
        (self.measurement_button, dropdown4,
        self.new_measurement_button, self.existing_measurement_button) = create_dropdown_button(
            "\n Measurement", "📏", width=150)
        self.measurement_button.setStyleSheet("font-weight: bold;")
        # self.new_measurement_button.clicked.connect(self.open_measurement_dialog)
        top_layout.addWidget(self.measurement_button)

        # ------------------------------------------------------------------
        # Other buttons (unchanged)
        # ------------------------------------------------------------------
        self.layers_button = QPushButton("📚 \n Layers")
        self.layers_button.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(self.layers_button)

        self.load_button = QPushButton("💠 \n 3D Point Cloud")
        self.load_button.setStyleSheet("font-weight: bold;")
        self.load_button.setFixedWidth(180)
        # self.load_button.clicked.connect(self.load_point_cloud)
        top_layout.addWidget(self.load_button)

        self.help_button = QPushButton("❓\n Help")
        self.help_button.setStyleSheet("font-weight: bold;")
        # self.help_button.clicked.connect(self.show_help_dialog)
        top_layout.addWidget(self.help_button)

        self.setting_button = QPushButton("⚙ \n Settings")
        self.setting_button.setStyleSheet("font-weight: bold;")
        self.setting_button.setFixedWidth(110)
        top_layout.addWidget(self.setting_button)

        top_layout.addStretch()          # push everything to the left
        main_layout.addWidget(top_section)

        # -----------------------------------------------------------------
        # MIDDLE CONTENT AREA (Left + Right sections)
        # ------------------------------------------------------------------
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        # --------------------------------
        # LEFT SECTION – Settings
        # ------------------------------------------------------------------
        left_section = QFrame()
        left_section.setFrameStyle(QFrame.Box | QFrame.Raised)
        left_section.setStyleSheet("""
            QFrame { 
                border: 2px solid #4CAF50; 
                border-radius: 10px; 
                background-color: #E8F5E9; 
                margin: 5px;
            }
        """)
        left_section.setMinimumWidth(380)
        left_section.setMaximumWidth(420)
        left_layout = QVBoxLayout(left_section)

        # ------------------------------------------------------------------
        # NEW: Mode Banner (Measurement / Design) - TOP MOST in left panel
        # ------------------------------------------------------------------
        self.mode_banner = QLabel("No Mode Active")
        self.mode_banner.setAlignment(Qt.AlignCenter)
        self.mode_banner.setVisible(False)  # Hidden until worksheet is loaded
        left_layout.addWidget(self.mode_banner)

        # Add worksheet display BELOW the mode banner
        left_layout.insertWidget(1, self.worksheet_display)  # You already have this line — keep it

        # ---------------------------------------------------------------------------
        # Merger Layers Section
        # ---------------------------------------------------------------------------
        merger_frame = QFrame()
        merger_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        merger_frame.setStyleSheet("""
            QFrame { 
                border: 2px solid #42A5F5; 
                border-radius: 10px; 
                background-color: #E3F2FD; 
                margin: 10px; 
            }
        """)
        merger_layout = QVBoxLayout(merger_frame)
        merger_frame.setVisible(False)                    # change

        merger_title = QLabel("Merger Layers")
        merger_title.setAlignment(Qt.AlignCenter)
        merger_title.setStyleSheet("""
            font-weight: bold; 
            font-size: 13px; 
            padding: 8px; 
            background-color: #E3F2FD; 
            border-radius: 5px;
        """)
        merger_layout.addWidget(merger_title)
        merger_layout.addStretch()
        
        # --------------------------------------------------------------------------- 
        # 3D Layers Section
        # ---------------------------------------------------------------------------
        self.three_D_frame = QFrame()
        self.three_D_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.three_D_frame.setStyleSheet("""
            QFrame { 
                border: 2px solid #42A5F5; 
                border-radius: 10px; 
                background-color: #E3F2FD; 
                margin: 5px 10px;
            }
        """)
        three_D_layout = QVBoxLayout(self.three_D_frame)
        self.three_D_frame.setVisible(False)

        three_D_title = QLabel("3D Layers")
        three_D_title.setAlignment(Qt.AlignCenter)
        three_D_title.setStyleSheet("""
            font-weight: bold; 
            font-size: 14px; 
            padding: 8px; 
            background-color: #BBDEFB; 
            border-radius: 6px;
            color: #1565C0;
        """)
        three_D_layout.addWidget(three_D_title)

        # Scroll area for 3D layers
        three_D_scroll = QScrollArea()
        three_D_scroll.setWidgetResizable(True)
        three_D_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        three_D_scroll.setStyleSheet("background-color: white; border: none;")
        
        three_D_content = QWidget()
        self.three_D_layers_layout = QVBoxLayout(three_D_content)
        self.three_D_layers_layout.setAlignment(Qt.AlignTop)
        self.three_D_layers_layout.setSpacing(6)
        self.three_D_layers_layout.addStretch()  # Push items to top
        
        three_D_scroll.setWidget(three_D_content)
        three_D_layout.addWidget(three_D_scroll)

        # --------------------------------------------------------------------------- 
        # 2D Layers Section
        # ---------------------------------------------------------------------------
        self.two_D_frame = QFrame()
        self.two_D_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.two_D_frame.setStyleSheet("""
            QFrame { 
                border: 2px solid #66BB6A; 
                border-radius: 10px; 
                background-color: #E8F5E9; 
                margin: 5px 10px;
            }
        """)
        two_D_layout = QVBoxLayout(self.two_D_frame)
        self.two_D_frame.setVisible(False)

        two_D_title = QLabel("2D Layers")
        two_D_title.setAlignment(Qt.AlignCenter)
        two_D_title.setStyleSheet("""
            font-weight: bold; 
            font-size: 14px; 
            padding: 8px; 
            background-color: #C8E6C9; 
            border-radius: 6px;
            color: #2E7D32;
        """)
        two_D_layout.addWidget(two_D_title)

        # Scroll area for 2D layers
        two_D_scroll = QScrollArea()
        two_D_scroll.setWidgetResizable(True)
        two_D_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        two_D_scroll.setStyleSheet("background-color: white; border: none;")
        
        two_D_content = QWidget()
        self.two_D_layers_layout = QVBoxLayout(two_D_content)
        self.two_D_layers_layout.setAlignment(Qt.AlignTop)
        self.two_D_layers_layout.setSpacing(6)
        self.two_D_layers_layout.addStretch()
        
        two_D_scroll.setWidget(two_D_content)
        two_D_layout.addWidget(two_D_scroll)

        # === ADD BOTH FRAMES TO LEFT PANEL ===
        left_layout.addWidget(merger_frame)
        left_layout.addWidget(self.three_D_frame)
        left_layout.addWidget(self.two_D_frame)

        # Optional: Add stretch at bottom so layers stay at top
        left_layout.addStretch()


        # ==================== MESSAGE SECTION (COLLAPSIBLE) ====================
        self.message_button = QPushButton("Message")
        self.message_button.setStyleSheet("""
            QPushButton { 
                background-color: #FF8A65; 
                color: white; 
                border: none; 
                padding: 8px;
                border-radius: 5px; 
                font-weight: bold; 
                font-size: 12px; 
            }
            QPushButton:hover { background-color: #FFCCBC; }
        """)
        self.message_button.clicked.connect(self.toggle_message_section)
        left_layout.addWidget(self.message_button)
        
        self.message_section = QFrame()
        self.message_section.setVisible(False)
        self.message_section.setStyleSheet("""
            QFrame { 
                border: 2px solid #FF5722; 
                border-radius: 8px; 
                background-color: #FFF3E0; 
                margin: 5px 10px; 
            }
        """)
        msg_layout = QVBoxLayout(self.message_section)
        msg_title = QLabel("Terminal Output / Errors")
        msg_title.setStyleSheet("font-weight: bold; color: #D84315; padding: 5px;")
        msg_layout.addWidget(msg_title)
        
        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)
        self.message_text.setStyleSheet("""
            QTextEdit { 
                background-color: #FFF8E1; 
                border: 1px solid #FF8A65; 
                border-radius: 5px;
                font-family: Consolas, monospace; 
                font-size: 11px; 
                padding: 5px; 
            }
        """)
        self.message_text.setMinimumHeight(150)
        msg_layout.addWidget(self.message_text)
        left_layout.addWidget(self.message_section)

        # Reset buttons container
        self.reset_buttons_container = QWidget()
        self.reset_buttons_layout = QHBoxLayout(self.reset_buttons_container)
        self.reset_buttons_layout.setSpacing(10)
        
        self.reset_action_button = QPushButton("Reset")
        self.reset_all_button = QPushButton("Reset_All")
        
        self.reset_buttons_layout.addWidget(self.reset_action_button)
        self.reset_buttons_layout.addWidget(self.reset_all_button)
        
        left_layout.addWidget(self.reset_buttons_container)

        # Add left section to content layout
        content_layout.addWidget(left_section, 1)

        # ------------------------------------------------------------------
        # RIGHT SECTION (Visualization + Controls)
        # ------------------------------------------------------------------
        right_section = QWidget()
        right_layout = QVBoxLayout(right_section)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)

        # ------------------------------------------------------------------
        # MIDDLE SECTION – Visualization
        # ------------------------------------------------------------------
        middle_section = QFrame()
        middle_section.setFrameStyle(QFrame.Box | QFrame.Raised)
        middle_section.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        )
        middle_section.setStyleSheet("""
            QFrame {
                border: 3px solid #BA68C8;
                border-radius: 10px;
                background-color: #E6E6FA;
            }
        """)
        middle_layout = QVBoxLayout(middle_section)
        middle_layout.setContentsMargins(2, 2, 2, 2)
        
        # VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(middle_section)
        self.vtk_widget.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        )
        self.renderer = vtkRenderer()
        self.renderer.SetBackground(1, 1, 1)  # white background
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        middle_layout.addWidget(self.vtk_widget)

        # ------------------------------------------------------------------
        # SCALE SECTION
        # ------------------------------------------------------------------
        scale_section = QFrame()
        scale_section.setFrameStyle(QFrame.Box | QFrame.Raised)
        scale_section.setStyleSheet("""
            QFrame {
                border: 2px solid #FF9800;
                border-radius: 10px;
                background-color: #FFF3E0;
                margin: 5px;
            }
        """)
        scale_layout = QVBoxLayout(scale_section)
        scale_section.setMinimumHeight(180)
        scale_layout.setContentsMargins(0, 0, 0, 0)

        # Volume slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(0)
        self.volume_slider.setTickPosition(QSlider.TicksBelow)
        self.volume_slider.setTickInterval(5)
        self.volume_slider.setStyleSheet("""
            QSlider {
                padding-left: 16px;
                padding-right: 17px;
                margin: 2px 2px;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 9px;
                background: #E0E0E0;
                border-radius: 3px;
                margin: 0px 0;
            }
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 2px solid #4CAF50;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #F1F8E9;
                border: 2px solid #2E7D32;
            }
        """)
        # self.volume_slider.valueChanged.connect(self.volume_changed)
        scale_layout.addWidget(self.volume_slider)

        # Scale figure
        self.scale_figure = Figure(dpi=100)
        self.scale_figure.set_size_inches(8, 1.2)
        self.scale_canvas = FigureCanvas(self.scale_figure)
        self.scale_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.scale_canvas.setMinimumHeight(120)
        self.scale_canvas.setMaximumHeight(140)

        # Initialize the scale axes
        self.scale_ax = self.scale_figure.add_subplot(111)
        self.scale_ax.set_xlim(0, self.total_distance)
        self.scale_ax.set_ylim(0, 1.2)
        self.scale_ax.set_facecolor('#FFF3E0')
        self.scale_ax.set_xlabel('Chainage', labelpad=3)
        self.scale_ax.set_ylabel('')
        self.scale_ax.set_yticks([])
        self.scale_ax.set_yticklabels([])

        # Create initial scale line and marker
        self.scale_line, = self.scale_ax.plot([0, self.total_distance], [0.5, 0.5], 
                                            color='black', linewidth=3)
        self.scale_marker, = self.scale_ax.plot([0, 0], [0, 1], color='red', 
                                            linewidth=2, linestyle='--')

        # Set initial ticks
        self.scale_ax.set_xticks([])
        self.scale_ax.set_xticklabels([])
        self.scale_ax.tick_params(axis='x', which='both', bottom=True, labelbottom=True, pad=5)
        self.scale_ax.grid(True, axis='x', linestyle='-', alpha=0.3)
        self.scale_ax.spines['top'].set_visible(False)
        self.scale_ax.spines['right'].set_visible(False)
        self.scale_ax.spines['left'].set_visible(False)

        # Adjust layout
        self.scale_figure.tight_layout(rect=[0, 0.1, 1, 0.95])
        self.scale_canvas.draw()
        scale_layout.addWidget(self.scale_canvas)

        # HIDE THE SCALE SECTION INITIALLY
        scale_section.setVisible(False)
        self.scale_section = scale_section

        # ------------------------------------------------------------------
        # BOTTOM SECTION – Controls
        # ------------------------------------------------------------------
        bottom_section = QFrame()
        bottom_section.setFrameStyle(QFrame.Box | QFrame.Raised)
        bottom_section.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        )
        bottom_section.setStyleSheet("""
            QFrame {
                border: 3px solid #8F8F8F;
                border-radius: 10px;
                background-color: #8FBFEF;
            }
        """)
        bottom_section.setMinimumHeight(400)
        bottom_layout = QVBoxLayout(bottom_section)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_section.setVisible(False)  # Hide bottom section initially
        self.bottom_section = bottom_section

        # ---------------------------------------------------------------------
        # Line Section (Collapsible)
        # ---------------------------------------------------------------------
        self.line_section = QFrame()
        self.line_section.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.line_section.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        )
        self.line_section.setStyleSheet("""
            QFrame {
                border: 3px solid #BA68C8;
                border-radius: 10px;
                background-color: #E6E6FA;
            }
        """)
        self.line_section.setMinimumWidth(80)
        self.line_section.setMaximumWidth(350)
        line_layout = QVBoxLayout(self.line_section)
        line_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        line_layout.setSpacing(0)  # Remove spacing

        # Create a container for the top bar (header)
        self.header_container = QWidget()
        self.header_container.setFixedHeight(45)  # Fixed height for header
        header_layout = QHBoxLayout(self.header_container)
        header_layout.setContentsMargins(5, 5, 5, 5)
        header_layout.setSpacing(10)

        # Collapse button (left aligned)
        self.collapse_button = QPushButton("◀")
        self.collapse_button.setFixedSize(35, 35)
        self.collapse_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #6A1B9A;
            }
        """)
        self.collapse_button.clicked.connect(self.toggle_line_section)
        self.collapse_button.setCursor(Qt.PointingHandCursor)
        self.collapse_button.setToolTip("Close Line Section")
        header_layout.addWidget(self.collapse_button)

        # Stretch to push undo/redo to right
        header_layout.addStretch()

        # Undo button
        self.undo_button = QPushButton()
        svg_data_left = QByteArray(self.svg_left)
        renderer_left = QSvgRenderer(svg_data_left)
        pixmap_left = QPixmap(30, 30)
        pixmap_left.fill(Qt.transparent)
        painter_left = QPainter(pixmap_left)
        renderer_left.render(painter_left, QRectF(0, 0, 24, 24))
        painter_left.end()
        self.undo_button.setIcon(QIcon(pixmap_left))
        self.undo_button.setIconSize(QSize(24, 24))
        self.undo_button.setFixedSize(35, 35)
        self.undo_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 #6366f1, stop:1 #4f46e5);
                border: none;
                padding: 0px;
                margin: 0px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 #4f46e5, stop:1 #4338ca);
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
        """)
        self.undo_button.setCursor(Qt.PointingHandCursor)
        self.undo_button.setToolTip("Undo")
        header_layout.addWidget(self.undo_button)

        # Redo button
        self.redo_button = QPushButton()
        svg_data_right = QByteArray(self.svg_right)
        renderer_right = QSvgRenderer(svg_data_right)
        pixmap_right = QPixmap(30, 30)
        pixmap_right.fill(Qt.transparent)
        painter_right = QPainter(pixmap_right)
        renderer_right.render(painter_right, QRectF(0, 0, 24, 24))
        painter_right.end()
        self.redo_button.setIcon(QIcon(pixmap_right))
        self.redo_button.setIconSize(QSize(24, 24))
        self.redo_button.setFixedSize(35, 35)
        self.redo_button.setStyleSheet(self.undo_button.styleSheet())
        self.redo_button.setCursor(Qt.PointingHandCursor)
        self.redo_button.setToolTip("Redo")
        header_layout.addWidget(self.redo_button)

        # Add header container to line layout
        line_layout.addWidget(self.header_container)

        # Create line_content_widget (the collapsible part)
        self.line_content_widget = QWidget()
        self.line_content_layout = QVBoxLayout(self.line_content_widget)
        self.line_content_layout.setContentsMargins(5, 5, 5, 5)
        self.line_content_layout.setSpacing(5)

        # Add line_content_widget to line layout
        line_layout.addWidget(self.line_content_widget)

        # Function to create checkbox rows
        def create_line_checkbox_with_pencil(checkbox_text, info_text, item_id, color_style=""):
            container = QWidget()
            container.setFixedWidth(250)
            container.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border: none;
                    margin: 1px;
                }
            """)
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 5, 0, 10)
            layout.setSpacing(5)
            
            checkbox = QCheckBox()
            checkbox.setFixedSize(35, 35)
            checkbox.setText("")
            checkbox.setObjectName(item_id)
            
            pencil_button = QPushButton()
            svg_data = QByteArray()
            svg_data.append(self.PENCIL_SVG)
            renderer = QSvgRenderer(svg_data)
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter, QRectF(pixmap.rect()))
            painter.end()
            icon = QIcon(pixmap)
            pencil_button.setIcon(icon)
            pencil_button.setIconSize(QSize(24, 24))
            pencil_button.setFixedSize(30, 30)
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
            
            text_label = QLabel(checkbox_text)
            text_label.setStyleSheet(f"""
                QLabel {{
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                    font-weight: bold;
                    font-size: 16px;
                    color: #000000;
                    text-align: left;
                }}
            """)
            
            layout.addWidget(checkbox)
            layout.addWidget(text_label, 1)
            layout.addWidget(pencil_button)
            
            return container, checkbox, text_label, pencil_button

        # # Create checkbox rows
        # Zero Line
        self.zero_container, self.zero_line, zero_label, self.zero_pencil = create_line_checkbox_with_pencil(
            "Zero Line",
            "Shows the zero reference line for elevation measurements",
            'zero_line'
        )
        self.zero_line.setStyleSheet("""
            QCheckBox {
                color: black;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.zero_container.setVisible(False)

        # Connect state change → change label text color to purple when checked
        self.zero_line.stateChanged.connect(lambda state: zero_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: purple;
            }
        """ if state == Qt.Checked else """
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: #000000;
            }
        """))
        # self.zero_line.stateChanged.connect(lambda state: self.on_checkbox_changed(state, 'zero'))
        # self.zero_pencil.clicked.connect(self.edit_zero_line)
        line_layout.addWidget(self.zero_container)

        # self.zero_container.setVisible(False)
 

        # Surface Line
        self.surface_container, self.surface_baseline, surface_label, surface_pencil = create_line_checkbox_with_pencil(
            "Surface Line",
            "Shows the ground surface baseline",
            'surface_line'
        )
        self.surface_baseline.setStyleSheet("""
            QCheckBox {
                color: black;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.surface_container.setVisible(False)

        self.surface_baseline.stateChanged.connect(lambda state: surface_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: green;
            }
        """ if state == Qt.Checked else """
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: #000000;
            }
        """))

        line_layout.addWidget(self.surface_container)

        # Construction Line
        self.construction_container, self.construction_line, construction_label, construction_pencil = create_line_checkbox_with_pencil(
            "Construction Line",
            "Shows the construction reference line",
            'construction_line'
        )
        self.construction_line.setStyleSheet("""
            QCheckBox {
                color: black;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.construction_container.setVisible(False)

        self.construction_line.stateChanged.connect(lambda state: construction_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: red;
            }
        """ if state == Qt.Checked else """
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: #000000;
            }
        """))

        line_layout.addWidget(self.construction_container)

        # Road Surface Line
        self.road_surface_container, self.road_surface_line, road_surface_label, road_pencil = create_line_checkbox_with_pencil(
            "Road Surface Line",
            "Shows the road surface elevation profile",
            'road_surface_line'
        )
        self.road_surface_line.setStyleSheet("""
            QCheckBox {
                color: black;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.road_surface_container.setVisible(False)

        self.road_surface_line.stateChanged.connect(lambda state: road_surface_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: blue;
            }
        """ if state == Qt.Checked else """
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: #000000;
            }
        """))

        line_layout.addWidget(self.road_surface_container)

        # Bridge-specific Zero Line
        self.bridge_zero_container, self.bridge_zero_line, bridge_zero_label, self.bridge_zero_pencil = create_line_checkbox_with_pencil(
            "Zero Line",
            "Shows the bridge zero reference line for elevation measurements",
            'zero_line'
        )
        self.bridge_zero_line.setStyleSheet("""
            QCheckBox {
                color: black;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.bridge_zero_container.setVisible(False)

        self.bridge_zero_line.stateChanged.connect(lambda state: bridge_zero_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: purple;
            }
        """ if state == Qt.Checked else """
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: #000000;
            }
        """))

        line_layout.addWidget(self.bridge_zero_container)

        # Projection Line
        self.projection_container, self.projection_line, projection_label, projection_pencil = create_line_checkbox_with_pencil(
            " Projection Line",
            "Shows the projection elevation profile",
            'projection_line'
        )
        self.projection_line.setStyleSheet("""
            QCheckBox {
                color: black;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.projection_container.setVisible(False)

        self.projection_line.stateChanged.connect(lambda state: projection_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: green;
            }
        """ if state == Qt.Checked else """
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: #000000;
            }
        """))

        line_layout.addWidget(self.projection_container)

        # Construction Dots Line
        self.construction_dots_container, self.construction_dots_line, construction_dots_label, self.construction_dots_pencil = create_line_checkbox_with_pencil(
            "Construction Dots",
            "Shows the construction reference dots line",
            'construction_dots_line'
        )
        self.construction_dots_line.setStyleSheet("""
            QCheckBox {
                color: black;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.construction_dots_container.setVisible(False)

        self.construction_dots_line.stateChanged.connect(lambda state: construction_dots_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: red;
            }
        """ if state == Qt.Checked else """
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: #000000;
            }
        """))

        line_layout.addWidget(self.construction_dots_container)

        # Deck Line
        self.deck_line_container, self.deck_line, deck_label, self.deck_pencil = create_line_checkbox_with_pencil(
            "Deck Line",
            "Shows the deck elevation profile",
            'deck_line'
        )
        self.deck_line.setStyleSheet("""
            QCheckBox {
                color: black;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.deck_line_container.setVisible(False)

        self.deck_line.stateChanged.connect(lambda state: deck_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: blue;
            }
        """ if state == Qt.Checked else """
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                font-weight: bold;
                font-size: 16px;
                color: #000000;
            }
        """))

        line_layout.addWidget(self.deck_line_container)

# ================================================================================================================================== 

        # Additional buttons - "Add Material Line" (now always visible)
        self.add_material_line_button = QPushButton("Add Material Line")
        self.add_material_line_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;  /* Green */
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        # Button is now always visible from the start
        self.add_material_line_button.setVisible(True)

        line_layout.addWidget(self.add_material_line_button)

        # Create a dedicated layout for material items (to control order)
        self.material_items_layout = QVBoxLayout()
        self.material_items_layout.setSpacing(6)
        self.material_items_layout.setContentsMargins(0, 10, 0, 0)
        self.material_items_layout.setAlignment(Qt.AlignTop)

        # Add this layout right after the button
        line_layout.addLayout(self.material_items_layout)

        line_layout.addStretch(1)

        # Storage for material configurations and UI items
        self.material_configs = []   # list of dicts with material data
        self.material_items = []     # list of UI item dicts

        # Additional buttons
        self.preview_button = QPushButton("Curve")
        self.threed_map_button = QPushButton("Map on 3D")
        self.save_button = QPushButton("Save")
        
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
        
        self.threed_map_button.setStyleSheet("""
            QPushButton {
                background-color: #008CBA;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #007bb5; }
            QPushButton:pressed { background-color: #006f9a; }
        """)
        
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:pressed { background-color: #EF6C00; }
        """)
        
        self.preview_button.setVisible(False)
        self.threed_map_button.setVisible(False)
        self.save_button.setVisible(False)
        
        line_layout.addWidget(self.preview_button)
        line_layout.addWidget(self.threed_map_button)
        line_layout.addWidget(self.save_button)
        line_layout.addStretch()

        # Graph Canvas
        self.figure = Figure(dpi=100)
        base_width = max(self.total_distance / 3.0, 10)  # Minimum 10 inches
        self.figure.set_size_inches(base_width, 6)
        self.canvas = FigureCanvas(self.figure)

        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumWidth(800)  # Adjust as needed

        self.ax = self.figure.add_subplot(111)
        self.ax.grid(True, which='both', linestyle='-', linewidth=0.5, alpha=0.7)
        self.ax.set_xlim(0, self.total_distance)
        self.ax.set_ylim(-3, 3)
        self.ax.set_xlabel('Y (Distance)')
        self.ax.set_ylabel('Z (Elevation)')
        self.ax.set_title('Road Construction Layers', fontsize=14, fontweight='bold', color='#4A148C')
        
        self.ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
        self.ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        
        self.annotation = self.ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                                        bbox=dict(boxstyle="round,pad=0.5"), arrowprops=dict(arrowstyle="->"),
                                        ha='left', va='bottom')
        self.annotation.set_visible(False)
        
        # self.cid_hover = self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        self.canvas.draw()
        self.figure.tight_layout()


        # ---------------------------------------------------------------------
        # Zoom Controls Toolbar - SIMPLIFIED WORKING VERSION
        # ---------------------------------------------------------------------
        zoom_toolbar = QWidget()
        zoom_toolbar.setFixedHeight(40)
        zoom_toolbar.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                margin: 0px;
            }
        """)

        zoom_layout = QHBoxLayout(zoom_toolbar)
        zoom_layout.setContentsMargins(10, 5, 10, 5)
        zoom_layout.setSpacing(10)

        # Zoom label
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("font-weight: bold; color: #333;")
        zoom_layout.addWidget(zoom_label)

        # Zoom out button
        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.setFixedWidth(30)
        self.zoom_out_button.setFixedHeight(30)
        self.zoom_out_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        zoom_layout.addWidget(self.zoom_out_button)

        # Zoom level display
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(60)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                padding: 5px;
                font-weight: bold;
            }
        """)
        zoom_layout.addWidget(self.zoom_label)

        # Zoom in button
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setFixedWidth(30)
        self.zoom_in_button.setFixedHeight(30)
        self.zoom_in_button.setStyleSheet(self.zoom_out_button.styleSheet())
        zoom_layout.addWidget(self.zoom_in_button)

        # Reset zoom button
        self.reset_zoom_button = QPushButton("Reset")
        self.reset_zoom_button.setFixedHeight(30)
        self.reset_zoom_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        zoom_layout.addWidget(self.reset_zoom_button)

        # Simple slider
        zoom_layout.addWidget(QLabel("Scale:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 200)  # 10% to 200%
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickPosition(QSlider.NoTicks)
        self.zoom_slider.setFixedWidth(100)
        zoom_layout.addWidget(self.zoom_slider)

        # Pan controls
        zoom_layout.addWidget(QLabel("Pan:"))
        self.pan_left_button = QPushButton("◀")
        self.pan_left_button.setFixedWidth(30)
        self.pan_left_button.setFixedHeight(30)
        self.pan_left_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        zoom_layout.addWidget(self.pan_left_button)

        self.pan_right_button = QPushButton("▶")
        self.pan_right_button.setFixedWidth(30)
        self.pan_right_button.setFixedHeight(30)
        self.pan_right_button.setStyleSheet(self.pan_left_button.styleSheet())
        zoom_layout.addWidget(self.pan_right_button)

        self.pan_up_button = QPushButton("▲")
        self.pan_up_button.setFixedWidth(30)
        self.pan_up_button.setFixedHeight(30)
        self.pan_up_button.setStyleSheet(self.pan_left_button.styleSheet())
        zoom_layout.addWidget(self.pan_up_button)

        self.pan_down_button = QPushButton("▼")
        self.pan_down_button.setFixedWidth(30)
        self.pan_down_button.setFixedHeight(30)
        self.pan_down_button.setStyleSheet(self.pan_left_button.styleSheet())
        zoom_layout.addWidget(self.pan_down_button)

        # Auto-fit button
        self.autofit_button = QPushButton("Auto Fit")
        self.autofit_button.setFixedHeight(30)
        self.autofit_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                padding: 0 15px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        zoom_layout.addWidget(self.autofit_button)

        # Add stretch
        zoom_layout.addStretch()

        # Add zoom toolbar to the layout BEFORE the graph
        bottom_layout.addWidget(zoom_toolbar)
        
        # Create horizontal layout for line section and canvas
        content_layout_bottom = QHBoxLayout()
        content_layout_bottom.addWidget(self.line_section)
        content_layout_bottom.addWidget(self.canvas, 4)
        bottom_layout.addLayout(content_layout_bottom)

        # Add middle, scale, and bottom sections to right layout
        right_layout.addWidget(middle_section, 3)  # 3 parts for visualization
        right_layout.addWidget(scale_section, 1)   # 1 part for scale
        right_layout.addWidget(bottom_section, 1)  # 1 part for controls

        # Add right section to content layout
        content_layout.addWidget(right_section, 3)

        # Add content widget to main layout
        main_layout.addWidget(content_widget, 1)

        # Create central widget and set layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Setup zoom and pan controls
        self.setup_zoom_controls()

        # Initial zoom display
        self.update_zoom_display()

    def create_progress_bar(self):
        """Create and configure the progress bar widget"""
        self.progress_bar = QWidget()
        self.progress_bar.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.progress_bar.setStyleSheet("""
            background-color: rgba(50, 50, 50, 220);
            border-radius: 8px;
            border: 1px solid #444;
        """)
        self.progress_bar.setFixedSize(500, 300) # Increased width to accommodate file size
        layout = QVBoxLayout(self.progress_bar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        # Loading label
        self.loading_label = QLabel("Loading Point Cloud Data...")
        self.loading_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
            }
        """)
        self.loading_label.setAlignment(Qt.AlignCenter)
        # File info container (horizontal layout for file name and size)
        file_info_container = QWidget()
        file_info_layout = QHBoxLayout(file_info_container)
        file_info_layout.setContentsMargins(0, 0, 0, 0)
        file_info_layout.setSpacing(10)
        # File name label
        self.file_name_label = QLabel("")
        self.file_name_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: white;
            }
        """)
        self.file_name_label.setAlignment(Qt.AlignCenter)
        self.file_name_label.setWordWrap(True)
        # File size label
        self.file_size_label = QLabel("")
        self.file_size_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: white;
            }
        """)
        self.file_size_label.setAlignment(Qt.AlignCenter)
        file_info_layout.addWidget(self.file_name_label, 70) # 70% width
        file_info_layout.addWidget(self.file_size_label, 30) # 30% width
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(15)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 6px;
                background-color: #333;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        # Percentage label
        self.percentage_label = QLabel("0%")
        self.percentage_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
        """)
        self.percentage_label.setAlignment(Qt.AlignCenter)
        # Add widgets to layout
        layout.addWidget(self.loading_label)
        layout.addWidget(file_info_container)
        layout.addWidget(self.progress)
        layout.addWidget(self.percentage_label)
        # Center the progress bar on screen but shifted slightly to the right
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.progress_bar.width()) // 2 + 150 # Shift 100 pixels right
        y = (screen_geometry.height() - self.progress_bar.height()) // 2
        self.progress_bar.move(x, y)

    def show_progress_bar(self, file_path=None):
        """Show and position the progress bar"""
        if file_path:
            file_name = os.path.basename(file_path)
            self.file_name_label.setText(f"File: {file_name}")
            # Get and format file size
            try:
                file_size_bytes = os.path.getsize(file_path)
                if file_size_bytes < 1024 * 1024: # Less than 1 MB
                    size_str = f"{file_size_bytes/1024:.1f} KB"
                elif file_size_bytes < 1024 * 1024 * 1024: # Less than 1 GB
                    size_str = f"{file_size_bytes/(1024*1024):.1f} MB"
                else: # GB or more
                    size_str = f"{file_size_bytes/(1024*1024*1024):.1f} GB"
                self.file_size_label.setText(f"Size: {size_str}")
            except:
                self.file_size_label.setText("Size: Unknown")
        self.progress.setValue(0)
        self.percentage_label.setText("0%")
        self.progress_bar.show()
        QApplication.processEvents() # Force UI update

    def update_progress(self, value, message=None):
        """Update progress bar value and optionally the message"""
        self.progress.setValue(value)
        self.percentage_label.setText(f"{value}%")
        if message:
            self.loading_label.setText(message)
        QApplication.processEvents() # Ensure UI updates

    def hide_progress_bar(self):
        """Hide the progress bar with a smooth fade-out"""
        self.progress_bar.hide()
        self.progress.setValue(0)
        self.percentage_label.setText("0%")

    def toggle_message_section(self):
        self.message_visible = not self.message_visible
        self.message_section.setVisible(self.message_visible)
        self.message_button.setText("Hide Message" if self.message_visible else "Message")
    
    def toggle_worksheet_options(self):
        checked = self.worksheet_button.isChecked()
        self.sub_buttons_widget.setVisible(checked)
        self.worksheet_button.setText("Worksheet ▼" if checked else "Worksheet")

    def toggle_design_options(self):
        checked = self.design_button.isChecked()
        self.sub_design_buttons_widget.setVisible(checked)
        self.design_button.setText("Design ▼" if checked else "Design")
    
    def toggle_construction_options(self):
        checked = self.construction_button.isChecked()
        self.sub_construction_buttons_widget.setVisible(checked)
        self.construction_button.setText("Construction ▼" if checked else "Construction")

    def toggle_measurement_options(self):
        checked = self.measurement_button.isChecked()
        self.sub_measurement_buttons_widget.setVisible(checked)
        self.measurement_button.setText("Measurement ▼" if checked else "Measurement")

    def toggle_line_section(self):
        """Toggle visibility of the line section"""
        if self.line_content_widget.isVisible():
            # Collapse the section
            self.line_content_widget.hide()
            self.collapse_button.setText("▶")
            self.collapse_button.setToolTip("Open Line Section")
            # Hide undo/redo buttons
            self.undo_button.hide()
            self.redo_button.hide()
            # Set fixed width for collapsed state
            self.line_section.setFixedWidth(50)
            # Update the layout to remove space for hidden buttons
            self.header_container.layout().setContentsMargins(5, 5, 5, 5)
        else:
            # Expand the section
            self.line_content_widget.show()
            self.collapse_button.setText("◀")
            self.collapse_button.setToolTip("Close Line Section")
            # Show undo/redo buttons
            self.undo_button.show()
            self.redo_button.show()
            # Set maximum width for expanded state
            self.line_section.setMaximumWidth(350)
            self.line_section.setFixedWidth(350)
        
        # Force layout update
        self.header_container.updateGeometry()
        self.line_section.updateGeometry()
        QApplication.processEvents()  # Force immediate UI update
        self.canvas.draw()

    def setup_zoom_controls(self):
        """Connect zoom controls to their functions"""
        self.zoom_in_button.clicked.connect(self.zoom_in_simple)
        self.zoom_out_button.clicked.connect(self.zoom_out_simple)
        self.reset_zoom_button.clicked.connect(self.reset_zoom_simple)
        self.zoom_slider.valueChanged.connect(self.zoom_slider_changed_simple)
        
        # Pan controls
        self.pan_left_button.clicked.connect(self.pan_left_simple)
        self.pan_right_button.clicked.connect(self.pan_right_simple)
        self.pan_up_button.clicked.connect(self.pan_up_simple)
        self.pan_down_button.clicked.connect(self.pan_down_simple)
        
        # Set up mouse wheel zoom
        self.canvas.mpl_connect('scroll_event', self.on_mouse_wheel_simple)
        
        # Initialize zoom state
        self.current_zoom = 100  # 100%
        self.original_xlim = (0, self.total_distance)
        self.original_ylim = (-3, 3)

        self.autofit_button.clicked.connect(self.autofit_graph_simple)

    def zoom_in_simple(self):
        """Zoom in by 20%"""
        self.current_zoom = min(500, self.current_zoom * 1.2)  # Cap at 500%
        self.apply_zoom()
        self.update_zoom_display()

    def zoom_out_simple(self):
        """Zoom out by 20%"""
        self.current_zoom = max(10, self.current_zoom / 1.2)  # Minimum 10%
        self.apply_zoom()
        self.update_zoom_display()

    def reset_zoom_simple(self):
        """Reset zoom to original view"""
        self.current_zoom = 100
        self.ax.set_xlim(self.original_xlim)
        self.ax.set_ylim(self.original_ylim)
        self.zoom_slider.setValue(100)
        self.update_zoom_display()
        self.canvas.draw()

    def zoom_slider_changed_simple(self, value):
        """Handle zoom slider changes"""
        self.current_zoom = value
        self.apply_zoom()
        self.update_zoom_display()

    def apply_zoom(self):
        """Apply the current zoom level to the graph - Zoom relative to visible left"""
        current_xlim = self.ax.get_xlim()
        current_left = current_xlim[0]  # Get current left position
        
        # Calculate new range based on zoom level
        original_range = self.original_xlim[1] - self.original_xlim[0]
        new_range = original_range * (100 / self.current_zoom)
        
        # Keep the current left position fixed, adjust right based on zoom
        new_xlim = (current_left, current_left + new_range)
        
        # Apply new limits
        self.ax.set_xlim(new_xlim)
        
        # Keep y-axis at original scale for now
        self.ax.set_ylim(self.original_ylim)
        
        self.canvas.draw()

    def update_zoom_display(self):
        """Update zoom label"""
        self.zoom_label.setText(f"{int(self.current_zoom)}%")

    def on_mouse_wheel_simple(self, event):
        """Mouse wheel zoom - simpler version"""
        if event.inaxes != self.ax:
            return
        
        # Try to detect Ctrl - check both string and Qt modifiers
        ctrl_pressed = False
        
        # Check event.key (matplotlib's representation)
        if event.key and isinstance(event.key, str) and 'control' in event.key.lower():
            ctrl_pressed = True
        
        # Check Qt modifiers if available
        if not ctrl_pressed and hasattr(event, 'guiEvent') and event.guiEvent:
            from PyQt5.QtCore import Qt
            if event.guiEvent.modifiers() & Qt.ControlModifier:
                ctrl_pressed = True
        
        # If Ctrl is pressed, zoom
        if ctrl_pressed:
            if event.button == 'up':
                self.zoom_in_simple()
            elif event.button == 'down':
                self.zoom_out_simple()

    def pan_left_simple(self):
        """Pan graph to the left, but not beyond 0"""
        current_xlim = self.ax.get_xlim()
        
        # Calculate pan amount (10% of current width)
        pan_amount = (current_xlim[1] - current_xlim[0]) * 0.1
        
        # Calculate new left position
        new_left = current_xlim[0] - pan_amount
        
        # Don't go below 0
        if new_left < 0:
            new_left = 0
        
        # Calculate new right position
        new_right = current_xlim[1] - (current_xlim[0] - new_left)
        
        self.ax.set_xlim(new_left, new_right)
        self.canvas.draw()

    def pan_right_simple(self):
        """Pan graph to the right"""
        current_xlim = self.ax.get_xlim()
        pan_amount = (current_xlim[1] - current_xlim[0]) * 0.1
        self.ax.set_xlim(current_xlim[0] + pan_amount, current_xlim[1] + pan_amount)
        self.canvas.draw()

    def pan_up_simple(self):
        """Pan graph up"""
        current_ylim = self.ax.get_ylim()
        pan_amount = (current_ylim[1] - current_ylim[0]) * 0.1
        self.ax.set_ylim(current_ylim[0] + pan_amount, current_ylim[1] + pan_amount)
        self.canvas.draw()

    def pan_down_simple(self):
        """Pan graph down"""
        current_ylim = self.ax.get_ylim()
        pan_amount = (current_ylim[1] - current_ylim[0]) * 0.1
        self.ax.set_ylim(current_ylim[0] - pan_amount, current_ylim[1] - pan_amount)
        self.canvas.draw()

    def autofit_graph_simple(self):
        """Auto-fit the graph to show all lines"""
        try:
            # Get all line data
            all_x = []
            all_y = []
            
            # Check each line type for data
            for line_type, data in self.line_types.items():
                for polyline in data['polylines']:
                    if polyline and len(polyline) > 0:
                        xs = [p[0] for p in polyline]
                        ys = [p[1] for p in polyline]
                        all_x.extend(xs)
                        all_y.extend(ys)
            
            if all_x and all_y:
                # Calculate bounds with 10% padding
                x_min, x_max = min(all_x), max(all_x)
                y_min, y_max = min(all_y), max(all_y)
                
                x_padding = (x_max - x_min) * 0.1
                y_padding = (y_max - y_min) * 0.1
                
                # Apply new bounds
                self.ax.set_xlim(x_min - x_padding, x_max + x_padding)
                self.ax.set_ylim(y_min - y_padding, y_max + y_padding)
                
                # Update zoom display
                visible_range = (x_max + x_padding) - (x_min - x_padding)
                self.current_zoom = (self.original_xlim[1] / visible_range) * 100
                self.update_zoom_display()
                self.zoom_slider.setValue(int(self.current_zoom))
                
                self.canvas.draw()
                self.message_text.append("Graph auto-fitted to show all data.")
            else:
                self.message_text.append("No data available for auto-fit.")
        except Exception as e:
            self.message_text.append(f"Auto-fit error: {str(e)}")

# =============================================================================
    def add_layer_to_panel(self, layer_name: str, dimension: str):
        """
        Adds a layer label to the correct panel (3D or 2D Layers).
        Used for both worksheet initial layers and design layers.
        """
        label = QLabel(f"• {layer_name}")
        label.setStyleSheet("""
            QLabel {
                padding: 8px 12px;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                margin: 3px 8px;
                font-size: 13px;
                color: #0D47A1;
                border-left: 4px solid #1976D2;
            }
            QLabel:hover {
                background-color: #BBDEFB;
            }
        """)
        label.setToolTip(f"{dimension} Layer: {layer_name}")

        if dimension == "3D":
            if self.three_D_layers_layout:
                self.three_D_layers_layout.insertWidget(self.three_D_layers_layout.count() - 1, label)
        elif dimension == "2D":
            if self.two_D_layers_layout:
                self.two_D_layers_layout.insertWidget(self.two_D_layers_layout.count() - 1, label)



