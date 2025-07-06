# UI/UX Improvements for Shopping Cart & Banking System

## 1. Modern Theme System
import tkinter as tk
from tkinter import ttk

class ModernTheme:
    def __init__(self):
        self.themes = {
            'light': {
                'bg_primary': '#ffffff',
                'bg_secondary': '#f8f9fa',
                'bg_accent': '#e9ecef',
                'text_primary': '#212529',
                'text_secondary': '#6c757d',
                'color_success': '#28a745',
                'color_danger': '#dc3545',
                'color_warning': '#ffc107',
                'color_info': '#17a2b8',
                'color_primary': '#007bff'
            },
            'dark': {
                'bg_primary': '#2b2b2b',
                'bg_secondary': '#1e1e1e',
                'bg_accent': '#3a3a3a',
                'text_primary': '#ffffff',
                'text_secondary': '#b3b3b3',
                'color_success': '#4caf50',
                'color_danger': '#f44336',
                'color_warning': '#ff9800',
                'color_info': '#2196f3',
                'color_primary': '#3f51b5'
            },
            'blue': {
                'bg_primary': '#f0f8ff',
                'bg_secondary': '#e6f3ff',
                'bg_accent': '#cce7ff',
                'text_primary': '#1a365d',
                'text_secondary': '#4a5568',
                'color_success': '#38a169',
                'color_danger': '#e53e3e',
                'color_warning': '#ed8936',
                'color_info': '#3182ce',
                'color_primary': '#2b6cb0'
            }
        }
    
    def apply_theme(self, widget, theme_name='light'):
        """Apply theme to widget and all children"""
        theme = self.themes.get(theme_name, self.themes['light'])
        self._apply_colors_recursive(widget, theme)
    
    def _apply_colors_recursive(self, widget, theme):
        """Recursively apply colors to widget tree"""
        try:
            if isinstance(widget, (tk.Button, tk.Label, tk.Frame)):
                widget.configure(
                    bg=theme['bg_primary'],
                    fg=theme['text_primary']
                )
            elif isinstance(widget, tk.Entry):
                widget.configure(
                    bg=theme['bg_secondary'],
                    fg=theme['text_primary'],
                    insertbackground=theme['text_primary']
                )
        except tk.TclError:
            pass
        
        for child in widget.winfo_children():
            self._apply_colors_recursive(child, theme)

## 2. Enhanced Widgets
class ModernButton(tk.Button):
    def __init__(self, parent, text="", command=None, style="primary", **kwargs):
        self.style_colors = {
            'primary': {'bg': '#007bff', 'fg': 'white', 'hover_bg': '#0056b3'},
            'success': {'bg': '#28a745', 'fg': 'white', 'hover_bg': '#218838'},
            'danger': {'bg': '#dc3545', 'fg': 'white', 'hover_bg': '#c82333'},
            'warning': {'bg': '#ffc107', 'fg': 'black', 'hover_bg': '#e0a800'},
            'secondary': {'bg': '#6c757d', 'fg': 'white', 'hover_bg': '#545b62'}
        }
        
        colors = self.style_colors.get(style, self.style_colors['primary'])
        
        super().__init__(
            parent, 
            text=text, 
            command=command,
            bg=colors['bg'],
            fg=colors['fg'],
            relief='flat',
            borderwidth=0,
            padx=20,
            pady=10,
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2',
            **kwargs
        )
        
        self.bind('<Enter>', lambda e: self.configure(bg=colors['hover_bg']))
        self.bind('<Leave>', lambda e: self.configure(bg=colors['bg']))

class ModernEntry(tk.Entry):
    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(
            parent,
            relief='solid',
            borderwidth=1,
            highlightthickness=2,
            highlightcolor='#007bff',
            font=('Segoe UI', 11),
            **kwargs
        )
        
        self.placeholder = placeholder
        self.placeholder_color = '#999999'
        self.default_color = '#000000'
        
        if placeholder:
            self.insert(0, placeholder)
            self.configure(fg=self.placeholder_color)
            
            self.bind('<FocusIn>', self._on_focus_in)
            self.bind('<FocusOut>', self._on_focus_out)
    
    def _on_focus_in(self, event):
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.configure(fg=self.default_color)
    
    def _on_focus_out(self, event):
        if not self.get():
            self.insert(0, self.placeholder)
            self.configure(fg=self.placeholder_color)

## 3. Loading and Progress Indicators
class LoadingSpinner(tk.Frame):
    def __init__(self, parent, size=50, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.canvas = tk.Canvas(self, width=size, height=size, highlightthickness=0)
        self.canvas.pack()
        
        self.size = size
        self.angle = 0
        self.running = False
        
    def start(self):
        """Start the spinning animation"""
        self.running = True
        self._animate()
    
    def stop(self):
        """Stop the animation"""
        self.running = False
        self.canvas.delete("all")
    
    def _animate(self):
        if not self.running:
            return
        
        self.canvas.delete("all")
        
        # Draw spinning arc
        padding = 10
        self.canvas.create_arc(
            padding, padding,
            self.size - padding, self.size - padding,
            start=self.angle,
            extent=270,
            width=3,
            outline='#007bff',
            style='arc'
        )
        
        self.angle = (self.angle + 10) % 360
        self.after(50, self._animate)

## 4. Toast Notifications
class ToastNotification:
    def __init__(self, parent):
        self.parent = parent
        self.notifications = []
    
    def show(self, message, type_="info", duration=3000):
        """Show a toast notification"""
        colors = {
            'success': {'bg': '#d4edda', 'fg': '#155724', 'border': '#c3e6cb'},
            'error': {'bg': '#f8d7da', 'fg': '#721c24', 'border': '#f5c6cb'},
            'warning': {'bg': '#fff3cd', 'fg': '#856404', 'border': '#ffeaa7'},
            'info': {'bg': '#d1ecf1', 'fg': '#0c5460', 'border': '#bee5eb'}
        }
        
        color = colors.get(type_, colors['info'])
        
        # Create notification frame
        notification = tk.Frame(
            self.parent,
            bg=color['bg'],
            relief='solid',
            borderwidth=1
        )
        
        # Position at top-right
        x = self.parent.winfo_width() - 300
        y = 20 + len(self.notifications) * 60
        notification.place(x=x, y=y, width=280, height=50)
        
        # Add message
        tk.Label(
            notification,
            text=message,
            bg=color['bg'],
            fg=color['fg'],
            font=('Segoe UI', 10),
            wraplength=250
        ).pack(pady=10)
        
        self.notifications.append(notification)
        
        # Auto-remove after duration
        self.parent.after(duration, lambda: self._remove_notification(notification))
    
    def _remove_notification(self, notification):
        """Remove a notification"""
        if notification in self.notifications:
            self.notifications.remove(notification)
            notification.destroy()
            self._reposition_notifications()
    
    def _reposition_notifications(self):
        """Reposition remaining notifications"""
        for i, notification in enumerate(self.notifications):
            x = self.parent.winfo_width() - 300
            y = 20 + i * 60
            notification.place(x=x, y=y)

## 5. Data Tables with Sorting and Filtering
class ModernTreeview(ttk.Treeview):
    def __init__(self, parent, columns, **kwargs):
        super().__init__(parent, columns=columns, show="headings", **kwargs)
        
        self.columns_data = columns
        self.sort_reverse = {col: False for col in columns}
        
        # Configure columns and enable sorting
        for col in columns:
            self.heading(col, text=col, command=lambda c=col: self.sort_column(c))
            self.column(col, anchor='w')
        
        # Add filter entry
        self.filter_frame = tk.Frame(parent)
        self.filter_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(self.filter_frame, text="Filter:", font=('Segoe UI', 10)).pack(side='left')
        self.filter_var = tk.StringVar()
        self.filter_entry = ModernEntry(
            self.filter_frame, 
            textvariable=self.filter_var,
            placeholder="Type to filter..."
        )
        self.filter_entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
        self.filter_var.trace('w', self.on_filter_change)
        
        self.original_data = []
    
    def sort_column(self, column):
        """Sort treeview by column"""
        data = [(self.item(item)['values'], item) for item in self.get_children('')]
        
        # Get column index
        col_index = self.columns_data.index(column)
        
        # Sort data
        try:
            # Try numeric sort first
            data.sort(key=lambda x: float(x[0][col_index]), reverse=self.sort_reverse[column])
        except (ValueError, IndexError):
            # Fall back to string sort
            data.sort(key=lambda x: str(x[0][col_index]), reverse=self.sort_reverse[column])
        
        # Rearrange items
        for index, (values, item) in enumerate(data):
            self.move(item, '', index)
        
        # Reverse sort direction for next click
        self.sort_reverse[column] = not self.sort_reverse[column]
    
    def on_filter_change(self, *args):
        """Filter table based on search term"""
        search_term = self.filter_var.get().lower()
        
        # Clear current items
        for item in self.get_children():
            self.delete(item)
        
        # Re-add filtered items
        for values in self.original_data:
            if any(search_term in str(value).lower() for value in values):
                self.insert('', 'end', values=values)
    
    def load_data(self, data):
        """Load data into the treeview"""
        self.original_data = data
        
        # Clear existing items
        for item in self.get_children():
            self.delete(item)
        
        # Insert new data
        for values in data:
            self.insert('', 'end', values=values)
