"""
ConnectAI - A Modern AI Companion Application
A professional GUI application built with CustomTkinter featuring multiple interaction modes
and a bonding/growth system for enhanced user engagement.
"""

import customtkinter as ctk
from tkinter import PhotoImage
from PIL import Image, ImageDraw
import os

# ============================================================================
# CONFIGURATION & THEME SETTINGS
# ============================================================================

# Set appearance mode and default color theme
ctk.set_appearance_mode("Dark")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

# Color Palette - Calming, Professional Colors
COLORS = {
    "primary_bg": "#F5F7FA",  # Light grey-blue background
    "secondary_bg": "#FFFFFF",  # White for cards/panels
    "accent_blue": "#4A90E2",  # Soft blue accent
    "accent_green": "#6BCF9E",  # Soft green for success/growth
    "text_primary": "#2C3E50",  # Dark blue-grey for primary text
    "text_secondary": "#7F8C9A",  # Medium grey for secondary text
    "border": "#E1E8ED",  # Light border color
    "hover": "#E8F4F8",  # Light blue hover state
    "active": "#4A90E2",  # Active button color
    "shadow": "#00000015",  # Subtle shadow
}

# Mode Configuration - Each mode has its own welcome message and theme
MODES = {
    "Work Mode": {
        "welcome": "Welcome to Work Mode",
        "description":
        "Boost your productivity with AI-powered task management and focus tools.",
        "icon": "💼",
        "color": "#4A90E2"
    },
    "Therapy Mode": {
        "welcome": "Welcome to Therapy Mode",
        "description":
        "A safe space for mindfulness, reflection, and emotional well-being support.",
        "icon": "🧘",
        "color": "#8E7CC3"
    },
    "Companion Mode": {
        "welcome": "Welcome to Companion Mode",
        "description":
        "Your friendly AI companion for casual conversation and daily interaction.",
        "icon": "🌟",
        "color": "#6BCF9E"
    }
}

# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================


class ConnectAIApp(ctk.CTk):
    """
    Main application window for ConnectAI.
    Manages the overall layout, navigation, and mode switching functionality.
    """

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("ConnectAI - Your AI Companion")
        self.geometry("1200x800")
        self.minsize(900, 600)

        # Configure background color
        self.configure(fg_color=COLORS["primary_bg"])

        # Application State
        self.current_mode = "Work Mode"
        self.user_logged_in = False
        self.bonding_progress = 45  # Progress percentage (0-100)

        # Initialize UI Components
        self.setup_ui()

    def setup_ui(self):
        """
        Initialize and arrange all UI components.
        Creates the main layout structure with navigation, sidebar, and content area.
        """
        # Configure grid layout for the main window
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create main UI sections
        self.create_navigation_bar()
        self.create_sidebar()
        self.create_main_content()

    # ========================================================================
    # NAVIGATION BAR
    # ========================================================================

    def create_navigation_bar(self):
        """
        Create the top navigation bar with app branding and login button.
        Spans across the entire width of the application.
        """
        self.nav_bar = ctk.CTkFrame(self,
                                    height=70,
                                    fg_color=COLORS["secondary_bg"],
                                    corner_radius=0)
        self.nav_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.nav_bar.grid_columnconfigure(1, weight=1)

        # App Title/Logo
        self.title_label = ctk.CTkLabel(self.nav_bar,
                                        text="ConnectAI",
                                        font=ctk.CTkFont(size=24,
                                                         weight="bold"),
                                        text_color=COLORS["accent_blue"])
        self.title_label.grid(row=0, column=0, padx=30, pady=20, sticky="w")

        # Login/Profile Button
        self.login_button = ctk.CTkButton(self.nav_bar,
                                          text="Login / Profile",
                                          width=140,
                                          height=36,
                                          corner_radius=20,
                                          fg_color=COLORS["accent_blue"],
                                          hover_color="#3A7BC8",
                                          font=ctk.CTkFont(size=14),
                                          command=self.toggle_login)
        self.login_button.grid(row=0, column=2, padx=30, pady=20, sticky="e")

    def toggle_login(self):
        """
        Handle login/logout functionality.
        Updates button text based on login state.
        """
        self.user_logged_in = not self.user_logged_in
        if self.user_logged_in:
            self.login_button.configure(text="👤 Profile")
            self.show_notification("Welcome back!")
        else:
            self.login_button.configure(text="Login / Profile")
            self.show_notification("Logged out")

    # ========================================================================
    # SIDEBAR - MODE SELECTOR
    # ========================================================================

    def create_sidebar(self):
        """
        Create the left sidebar with mode selection buttons and bonding feature.
        Provides quick access to different interaction modes.
        """
        self.sidebar = ctk.CTkFrame(self,
                                    width=280,
                                    fg_color=COLORS["secondary_bg"],
                                    corner_radius=0)
        self.sidebar.grid(row=1,
                          column=0,
                          sticky="nsw",
                          padx=(0, 0),
                          pady=(0, 0))
        self.sidebar.grid_rowconfigure(
            5, weight=1)  # Push bonding button to bottom

        # Sidebar Header
        sidebar_header = ctk.CTkLabel(self.sidebar,
                                      text="Select Mode",
                                      font=ctk.CTkFont(size=18, weight="bold"),
                                      text_color=COLORS["text_primary"])
        sidebar_header.grid(row=0,
                            column=0,
                            padx=25,
                            pady=(30, 20),
                            sticky="w")

        # Mode Toggle Buttons
        self.mode_buttons = {}
        for idx, (mode_name, mode_data) in enumerate(MODES.items()):
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{mode_data['icon']}  {mode_name}",
                width=230,
                height=50,
                corner_radius=12,
                font=ctk.CTkFont(size=15),
                fg_color=COLORS["primary_bg"],
                text_color=COLORS["text_primary"],
                hover_color=COLORS["hover"],
                border_width=2,
                border_color=COLORS["border"],
                anchor="w",
                command=lambda m=mode_name: self.switch_mode(m))
            btn.grid(row=idx + 1, column=0, padx=25, pady=8, sticky="ew")
            self.mode_buttons[mode_name] = btn

        # Set initial active mode
        self.update_mode_buttons()

        # Bonding Feature Button - Positioned at bottom
        self.bonding_button = ctk.CTkButton(self.sidebar,
                                            text="🌱 Grow Together",
                                            width=230,
                                            height=50,
                                            corner_radius=12,
                                            font=ctk.CTkFont(size=15,
                                                             weight="bold"),
                                            fg_color=COLORS["accent_green"],
                                            hover_color="#5ABD8D",
                                            text_color="white",
                                            command=self.open_bonding_popup)
        self.bonding_button.grid(row=6,
                                 column=0,
                                 padx=25,
                                 pady=(10, 30),
                                 sticky="s")

    def switch_mode(self, mode_name):
        """
        Switch to a different interaction mode.
        Updates the UI to reflect the selected mode.
        
        Args:
            mode_name (str): The name of the mode to switch to
        """
        self.current_mode = mode_name
        self.update_mode_buttons()
        self.update_main_content()

    def update_mode_buttons(self):
        """
        Update the visual state of mode buttons to highlight the active mode.
        Provides clear visual feedback on the current selection.
        """
        for mode_name, button in self.mode_buttons.items():
            if mode_name == self.current_mode:
                # Active state styling
                button.configure(fg_color=COLORS["active"],
                                 text_color="white",
                                 border_color=COLORS["active"])
            else:
                # Inactive state styling
                button.configure(fg_color=COLORS["primary_bg"],
                                 text_color=COLORS["text_primary"],
                                 border_color=COLORS["border"])

    # ========================================================================
    # MAIN CONTENT AREA
    # ========================================================================

    def create_main_content(self):
        """
        Create the main content area where mode-specific content is displayed.
        This area updates dynamically based on the selected mode.
        """
        self.main_content = ctk.CTkFrame(self,
                                         fg_color=COLORS["primary_bg"],
                                         corner_radius=0)
        self.main_content.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        self.main_content.grid_rowconfigure(2, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

        # Mode Title
        self.mode_title = ctk.CTkLabel(self.main_content,
                                       text="",
                                       font=ctk.CTkFont(size=32,
                                                        weight="bold"),
                                       text_color=COLORS["text_primary"])
        self.mode_title.grid(row=0,
                             column=0,
                             padx=40,
                             pady=(40, 10),
                             sticky="w")

        # Mode Description
        self.mode_description = ctk.CTkLabel(
            self.main_content,
            text="",
            font=ctk.CTkFont(size=16),
            text_color=COLORS["text_secondary"])
        self.mode_description.grid(row=1,
                                   column=0,
                                   padx=40,
                                   pady=(0, 30),
                                   sticky="w")

        # Content Card - Main interaction area
        self.content_card = ctk.CTkFrame(self.main_content,
                                         fg_color=COLORS["secondary_bg"],
                                         corner_radius=16)
        self.content_card.grid(row=2,
                               column=0,
                               padx=40,
                               pady=(0, 40),
                               sticky="nsew")
        self.content_card.grid_rowconfigure(0, weight=1)
        self.content_card.grid_columnconfigure(0, weight=1)

        # Placeholder for chat/LLM interactions
        self.chat_placeholder = ctk.CTkLabel(
            self.content_card,
            text=
            "💬 Chat interface coming soon...\n\nThis area will host LLM interactions,\nconversation history, and AI responses.",
            font=ctk.CTkFont(size=16),
            text_color=COLORS["text_secondary"],
            justify="center")
        self.chat_placeholder.grid(row=0, column=0, padx=40, pady=40)

        # Initialize content with default mode
        self.update_main_content()

    def update_main_content(self):
        """
        Update the main content area based on the currently selected mode.
        Changes the title, description, and visual theme.
        """
        mode_data = MODES[self.current_mode]

        self.mode_title.configure(
            text=f"{mode_data['icon']}  {mode_data['welcome']}")
        self.mode_description.configure(text=mode_data['description'])

    # ========================================================================
    # BONDING FEATURE - POPUP WINDOW
    # ========================================================================

    def open_bonding_popup(self):
        """
        Open a popup window displaying the bonding/growth feature.
        Shows progress bar and visual representation of shared growth.
        """
        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title("Grow Together - Bonding Progress")
        popup.geometry("500x600")
        popup.resizable(False, False)

        # Make popup modal
        popup.grab_set()
        popup.focus_set()

        # Configure popup background
        popup.configure(fg_color=COLORS["secondary_bg"])

        # Header
        header = ctk.CTkLabel(popup,
                              text="🌳 Your Growth Journey",
                              font=ctk.CTkFont(size=26, weight="bold"),
                              text_color=COLORS["text_primary"])
        header.pack(pady=(30, 10))

        # Subtitle
        subtitle = ctk.CTkLabel(popup,
                                text="Together, we grow stronger every day",
                                font=ctk.CTkFont(size=14),
                                text_color=COLORS["text_secondary"])
        subtitle.pack(pady=(0, 30))

        # Visual placeholder - Tree/Pet health representation
        visual_frame = ctk.CTkFrame(popup,
                                    width=300,
                                    height=300,
                                    fg_color=COLORS["primary_bg"],
                                    corner_radius=16)
        visual_frame.pack(pady=20, padx=40, fill="both", expand=True)
        visual_frame.pack_propagate(False)

        # Placeholder image/icon
        tree_icon = ctk.CTkLabel(visual_frame,
                                 text="🌱➡️🌿➡️🌳",
                                 font=ctk.CTkFont(size=48),
                                 text_color=COLORS["accent_green"])
        tree_icon.place(relx=0.5, rely=0.4, anchor="center")

        growth_label = ctk.CTkLabel(visual_frame,
                                    text="Your connection is flourishing!",
                                    font=ctk.CTkFont(size=14),
                                    text_color=COLORS["text_secondary"])
        growth_label.place(relx=0.5, rely=0.7, anchor="center")

        # Progress Section
        progress_frame = ctk.CTkFrame(popup, fg_color="transparent")
        progress_frame.pack(pady=(20, 10), padx=40, fill="x")

        # Progress label
        progress_label = ctk.CTkLabel(
            progress_frame,
            text=f"Bonding Level: {self.bonding_progress}%",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"])
        progress_label.pack(pady=(0, 10))

        # Progress bar
        progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=400,
            height=16,
            corner_radius=8,
            progress_color=COLORS["accent_green"])
        progress_bar.pack(pady=(0, 10))
        progress_bar.set(self.bonding_progress / 100)

        # Progress description
        progress_desc = ctk.CTkLabel(
            progress_frame,
            text="Keep interacting to strengthen your bond!",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"])
        progress_desc.pack()

        # Close button
        close_button = ctk.CTkButton(popup,
                                     text="Close",
                                     width=200,
                                     height=40,
                                     corner_radius=20,
                                     fg_color=COLORS["accent_blue"],
                                     hover_color="#3A7BC8",
                                     font=ctk.CTkFont(size=14),
                                     command=popup.destroy)
        close_button.pack(pady=(20, 30))

        # Increment bonding progress as a demo feature
        self.bonding_progress = min(100, self.bonding_progress + 5)

    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================

    def show_notification(self, message):
        """
        Display a temporary notification message.
        
        Args:
            message (str): The notification message to display
        """
        # Create notification label in navigation bar
        notification = ctk.CTkLabel(self.nav_bar,
                                    text=f"✓ {message}",
                                    font=ctk.CTkFont(size=13),
                                    text_color=COLORS["accent_green"])
        notification.grid(row=0, column=1, padx=20)

        # Auto-dismiss after 2 seconds
        self.after(2000, notification.destroy)


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Create and run the application
    app = ConnectAIApp()
    app.mainloop()