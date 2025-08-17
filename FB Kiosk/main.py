"""
 FoodBank Kiosk
 Developer: Aarnav Mathur 
 Date: 16/08/25
 License: CustomTkinter, Python and Visual Studio
 Version: 1.0, last updated 17/08/25

 Purpose:
     This program is a kiosk application for a foodbank.
     It lets users:
       - View items loaded from a CSV (data/items.csv)
       - Search, sort (A → Z / Z → A) and filter by category and dietary tag
       - Add items to a cart, adjust quantity (1-10) or remove items
       

  - Functionality of the app
      * The GUI provides three main screens: View Items, Cart, and Info.
      * View Items: displays a scrollable list of items from the CSV, with search,
        category and dietary filters and sorting options.
      * Cart: shows selected items and allows quantity adjustments and removal.
              

  - Use of code structures:
          - Functions are used for GUI screens and utility behaviour.
      * Control structures: if/else for validation and logic, for-loops for rendering items,
        list comprehensions for filtering, try/except for file IO error handling.
      * Data types: strings, integers, lists, dicts (CSV rows).
      * Data sources: CSV files used for persistent storage because they are simple, portable,
       and easy to use

  - Why I chose this data type
      * CSV files are easy to read and easy to manage, and are also easy to export and import
     
"""
#Modifications / Maintenance Log
# 03/08/25 - Changed Cart logic to enforce max 10/item (was unlimited)
# 09/08/25 - Switched from Tkinter to CustomTkinter for better design
# 15/08/25 - Added try/except to load_items and save_order
# 16/08/25 - Replaced manual quantity input with +/- buttons for usability and validation

#Importing
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import csv
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional


# Data classes & structures
@dataclass
class Item:
    #Represents a product item from CSV.
    name: str
    category: str
    tag: str = ""  # dietary tag 
    

class Cart:
    """
    Cart behaviour.
    Stores items as list of name or quantity
    Provides add/remove/adjust/clear operations with quantity caps.
    Encapsulates all cart stuff 
    """
    def __init__(self, max_per_item: int = 10):
        self._items: List[Tuple[str, int]] = []
        self.max_per_item = max_per_item

    def to_list(self) -> List[Tuple[str, int]]:
        #Returns copy of cart contents for display.
        return list(self._items)

    def find_index(self, name: str) -> Optional[int]:
        #Return index of item name in cart, or none if not there
        for i, (n, q) in enumerate(self._items):
            if n == name:
                return i
        return None

    def add_item(self, name: str, qty: int = 1) -> Tuple[bool, str]:
        """
        Add item to cart. If exists, increase quantity up to max_per_item.
        Returns "Added" message
        """
        if qty < 1:
            return False, "Quantity must be at least 1."
        idx = self.find_index(name)
        if idx is None:
            capped = min(qty, self.max_per_item)
            self._items.append((name, capped))
            if qty > self.max_per_item:
                return True, f"Added (capped at {self.max_per_item})."
            return True, "Added."
        else:
            existing_qty = self._items[idx][1]
            new_qty = min(existing_qty + qty, self.max_per_item)
            self._items[idx] = (name, new_qty)
            if existing_qty + qty > self.max_per_item:
                return True, f"Updated (capped at {self.max_per_item})."
            return True, "Updated."

#Remove an item by name. Returns True if removed.
    def remove_item(self, name: str) -> bool:
        idx = self.find_index(name)
        if idx is not None:
            self._items.pop(idx)
            return True
        return False

#Set quantity for an existing item within range 1.max_per_item.
    def adjust_quantity(self, name: str, qty: int) -> Tuple[bool, str]:
        idx = self.find_index(name)
        if idx is None:
            return False, "Item not in cart."
        if qty < 1 or qty > self.max_per_item:
            return False, f"Quantity must be between 1 and {self.max_per_item}."
        self._items[idx] = (name, qty)
        return True, "Quantity updated."

    def clear(self):
        self._items.clear()

    def is_empty(self) -> bool:
        return len(self._items) == 0


cart = Cart(max_per_item=10)


#Loading items from CSV
def load_items(csv_path: str = "data/items.csv") -> List[Dict[str, str]]:
    """
    Loads item rows from a CSV file and returns a list of dictionaries.
    Uses try/except to handle missing or corrupted files
    Returns an empty list if the file cannot be read.
    """
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            items = list(reader)
            
            for r in items:
                # Guarantee keys exist to avoid KeyError in GUI rendering
                r.setdefault('name', '')
                r.setdefault('category', '')
                r.setdefault('tag', '')
              
            return items
    except FileNotFoundError:
        print(f"[ERROR] items.csv not found at path: {csv_path}")
        return []
    except Exception as e:
        # Log unexpected errors and return empty list
        print(f"[ERROR] Failed to load items.csv: {e}")
        return []

def validate_order_fields(item_name: str, quantity) -> Tuple[bool, str]:
    """
    Validates order fields with explicit existence, type or range checks.
    - Existence check: item_name must not be empty.
    - Type check: quantity must be an integer (or numeric string convertible to int).
    - Range check: 1 less than or equal to quantity less than or equal to cart.max_per_item
    Returns (is_valid, message).
    """
    if not item_name or not str(item_name).strip():
        return False, "Item name is required."

    # Type check: allow numeric strings too
    q_str = str(quantity).strip()
    if not q_str.isdigit():
        return False, "Quantity must be a whole number."

    q = int(q_str)
    if q <= 0:
        return False, "Quantity must be greater than zero."
    if q > cart.max_per_item:
        return False, f"Quantity must be no more than {cart.max_per_item}."
    return True, ""



# GUI Configuration
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Colour and font constants (ALL_CAPS for constants)
HEADER_COLOR = "#2C5D5A"
BUTTON_COLOR = "#2C5D5A"
BUTTON_HOVER = "#008C9E"
BACKGROUND_COLOR = "#f5f5f5"

TEXT_FONT = ("Segoe UI", 12)
TITLE_FONT = ("Segoe UI", 18, "bold")

# GUI Screens or Functions

def show_items_window():
    """
     Displays the 'View Items' window:
      - Loads items via load_items()
      - Provides search category dropdown, sort,  dietary buttons
      - Renders results in a scrollable frame and provides Add button for each item
    """
    item_window = ctk.CTkToplevel(root)
    item_window.title("View Items")
    item_window.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
    item_window.configure(fg_color=BACKGROUND_COLOR)
    item_window.transient(root)
    item_window.grab_set()
    item_window.focus_force()
    item_window.lift()

    # Header and labels
    header = ctk.CTkFrame(item_window, fg_color=HEADER_COLOR, height=60)
    header.pack(fill="x")
    ctk.CTkButton(header, text="←", width=40, command=item_window.destroy,
                  fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER).pack(side="left", padx=10, pady=10)
    ctk.CTkLabel(header, text="VIEW ITEMS", font=TITLE_FONT, text_color="white").pack(side="left", padx=20)
    ctk.CTkButton(header, text="Go to Cart 🛒", command=show_order_window,
                  fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER).pack(side="right", padx=20)

    # Controls and list of tags
    control_frame = ctk.CTkFrame(item_window, fg_color="white")
    control_frame.pack(fill="x", padx=40, pady=20)

    search_var = ctk.StringVar()
    ctk.CTkLabel(control_frame, text="Search:", font=TEXT_FONT).grid(row=0, column=0, sticky="w", padx=5)
    search_entry = ctk.CTkEntry(control_frame, textvariable=search_var, width=300)
    search_entry.grid(row=0, column=1, padx=10, pady=10)

    category_var = ctk.StringVar(value="All")
    ctk.CTkLabel(control_frame, text="Category:", font=TEXT_FONT).grid(row=1, column=0, sticky="w", padx=5)
    ctk.CTkOptionMenu(control_frame, variable=category_var,
                      values=["All", "Fruit", "Bakery", "Pantry", "Dairy", "Vegetables",
                              "Meat", "Prepared Meals", "Beverages", "Noodle", "Dessert", "Seafood"]).grid(row=1, column=1, sticky="w", pady=5)

    sort_var = ctk.StringVar(value="A → Z")
    ctk.CTkLabel(control_frame, text="Sort by:", font=TEXT_FONT).grid(row=2, column=0, sticky="w", padx=5)
    ctk.CTkOptionMenu(control_frame, variable=sort_var, values=["A → Z", "Z → A"]).grid(row=2, column=1, sticky="w", pady=5)

    ctk.CTkLabel(control_frame, text="Dietary requirement:", font=TEXT_FONT).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
    dietary_var = ctk.StringVar(value="All")
    dietary_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
    dietary_frame.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)

    for label in ["All", "Vegetarian", "Vegan", "Halal",]:
        ctk.CTkRadioButton(dietary_frame, text=label, variable=dietary_var, value=label).pack(side="left", padx=4)

    # List area
    list_frame = ctk.CTkScrollableFrame(item_window, height=1000, fg_color=BACKGROUND_COLOR)
    list_frame.pack(fill="both", expand=True, padx=40)

    feedback_label = ctk.CTkLabel(item_window, text="", text_color="green", font=("Segoe UI", 18, "bold"))
    feedback_label.pack(pady=5)

    def open_quantity_popup(name: str, parent_button):
        """
        Opens a popup to select quantity. This uses the Cart class for validation and capping.
        The popup ensures type/range/existence checks and provides feedback to the user.
        """
        qty_window = ctk.CTkToplevel(item_window)
        qty_window.title("Select Quantity")
        qty_window.geometry("300x230")
        qty_window.transient(item_window)
        qty_window.grab_set()

        qty_var = ctk.IntVar(value=1)
        warning_label = ctk.CTkLabel(qty_window, text="", text_color="red")
        warning_label.pack(pady=(5, 0))

        ctk.CTkLabel(qty_window, text=f"How many {name}?", font=("Segoe UI", 18, "bold")).pack(pady=8)
        qty_frame = ctk.CTkFrame(qty_window, fg_color="transparent")
        qty_frame.pack()
#Increasing item quantity
        def increase():
            if qty_var.get() < cart.max_per_item:
                qty_var.set(qty_var.get() + 1)
                warning_label.configure(text="")
            else:
                warning_label.configure(text=f"Max limit is {cart.max_per_item} per item.")
#Decreasing item quantity
        def decrease():
            if qty_var.get() > 1:
                qty_var.set(qty_var.get() - 1)
                warning_label.configure(text="")
#plus-minus layout 
        ctk.CTkButton(qty_frame, text="-", width=40, command=decrease).pack(side="left", padx=5)
        ctk.CTkLabel(qty_frame, textvariable=qty_var, font=("Segoe UI", 18)).pack(side="left", padx=5)
        ctk.CTkButton(qty_frame, text="+", width=40, command=increase).pack(side="left", padx=5)
#confirming order
        def confirm():
            q = qty_var.get()
            valid, msg = validate_order_fields(name, q)
            if not valid:
                warning_label.configure(text=msg)
                return
            success, add_msg = cart.add_item(name, q)
            feedback_label.configure(text=f"{q} × {name} added to cart!", text_color="green")
            parent_button.configure(text="Added!", fg_color="#228B22", hover_color="#1E7B1E")
            qty_window.destroy() #closes window after click
#add to cart button
        ctk.CTkButton(qty_window, text="Add to Cart", command=confirm,
                      fg_color="#2E8B57", hover_color="#256D4A").pack(pady=12)
#Load, filter, sort and render items in the list_frame.
    def render_items():
        
        for w in list_frame.winfo_children():
            w.destroy()
        feedback_label.configure(text="")

        items = load_items()
        keyword = search_var.get().strip().lower()  # CHANGED: strip() removes whitespace in search

        sort_by = sort_var.get()
        selected_category = category_var.get()
        selected_diet = dietary_var.get()

        # Filtering existence checks for fields are handled in load_items()
        filtered = [
            item for item in items
            if (keyword in item.get('name', '').lower() or keyword in item.get('category', '').lower())
            and (selected_category == "All" or item.get('category', '') == selected_category)
            and (selected_diet == "All" or (item.get('tag') and item['tag'].lower() == selected_diet.lower()))
        ]

        # Sorting from alphabetical order and reverse
        if sort_by == "A → Z":
            filtered.sort(key=lambda x: x.get('name', '').lower())
        elif sort_by == "Z → A":
            filtered.sort(key=lambda x: x.get('name', '').lower(), reverse=True)

        if not filtered:
            ctk.CTkLabel(list_frame, text="No items found.", font=("Segoe UI", 18, "bold"), text_color="red").pack(pady=20)
            return

        # Render each item
        for item_row in filtered:
            frame = ctk.CTkFrame(list_frame, fg_color="white", corner_radius=20)
            frame.pack(fill="x", padx=10, pady=12)

            item_name = item_row.get('name', '')
            font_size = 28 if item_name.lower() == "apples" else 22
            ctk.CTkLabel(frame, text=item_name, font=("Segoe UI", font_size, "bold"), text_color=HEADER_COLOR).pack(anchor="w", padx=20, pady=(10, 2))

            details_text = f"Category: {item_row.get('category', '')}"
            if item_row.get('tag'):
                details_text += f"    Diet: {item_row.get('tag')}"
            ctk.CTkLabel(frame, text=details_text, font=("Segoe UI", 16), text_color="#555555").pack(anchor="w", padx=20)

            add_btn = ctk.CTkButton(frame, text="Add", fg_color="#2E8B57", hover_color="#256D4A", text_color="white")
            add_btn.configure(command=lambda nm=item_name, btn=add_btn: open_quantity_popup(nm, btn))
            add_btn.pack(anchor="e", padx=10, pady=10)

    # Bindings
    search_entry.bind("<KeyRelease>", lambda e: render_items())
    sort_var.trace_add("write", lambda *args: render_items())
    category_var.trace_add("write", lambda *args: render_items())
    dietary_var.trace_add("write", lambda *args: render_items())
    render_items()

def show_order_window():
    """
    Display cart content with options to remove or adjust quantities and submit the order.
    Uses Cart class methods to manage items.
    """
    order_window = ctk.CTkToplevel(root)
    order_window.title("Cart")
    order_window.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
    order_window.transient(root)
    order_window.grab_set()
    order_window.focus_force()
    order_window.lift()

    header = ctk.CTkFrame(order_window, fg_color=HEADER_COLOR, height=60)
    header.pack(fill="x")
    ctk.CTkButton(header, text="←", width=40, command=order_window.destroy,
                  fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER).pack(side="left", padx=10, pady=10)
    ctk.CTkLabel(header, text="🛒 Your Cart", font=("Segoe UI", 24, "bold"), text_color="white").pack(side="left", padx=20)

    content = ctk.CTkFrame(order_window, fg_color=BACKGROUND_COLOR)
    content.pack(fill="both", expand=True, padx=80, pady=40)

    cart_frame = ctk.CTkScrollableFrame(content, fg_color="white", corner_radius=20)
    cart_frame.pack(fill="both", expand=True, padx=20, pady=20)

    message_label = ctk.CTkLabel(content, text="", font=TEXT_FONT)
    message_label.pack(pady=(5, 0))

    def refresh_cart():
        #Re-render cart contents from Cart.to_list().
        for widget in cart_frame.winfo_children():
            widget.destroy()

        items = cart.to_list()
        if not items:
            ctk.CTkLabel(cart_frame, text="Cart is empty.", font=("Segoe UI", 20, "bold"), text_color="red").pack(pady=20)
            return

        for idx, (name, qty) in enumerate(items):
            row = ctk.CTkFrame(cart_frame, fg_color="#f6f6f6", corner_radius=10)
            row.pack(fill="x", pady=8, padx=8)

            ctk.CTkLabel(row, text=f"{name} x {qty}", font=("Segoe UI", 18)).pack(side="left", padx=20)

            def on_remove(i=idx, n=name):
                removed = cart.remove_item(n)
                refresh_cart()
                if removed:
                    message_label.configure(text=f"{n} removed.", text_color="orange", font=("Segoe UI", 20,))

            def on_adjust(i=idx, n=name):
                # Popup to adjust quantity for this item
                adj_win = ctk.CTkToplevel(order_window)
                adj_win.title(f"Adjust Quantity - {n}")
                adj_win.geometry("300x230")
                adj_win.transient(order_window)
                adj_win.grab_set()

                qty_var = ctk.IntVar(value=cart.to_list()[i][1])
                alert = ctk.CTkLabel(adj_win, text="", text_color="red")
                alert.pack(pady=(5, 0))
                ctk.CTkLabel(adj_win, text=f"Adjust quantity for {n}", font=("Segoe UI", 16, "bold")).pack(pady=10)

                frameq = ctk.CTkFrame(adj_win, fg_color="transparent")
                frameq.pack(pady=8)

                def inc():
                    if qty_var.get() < cart.max_per_item:
                        qty_var.set(qty_var.get() + 1)
                        alert.configure(text="")
                    else:
                        alert.configure(text=f"Max is {cart.max_per_item}")

                def dec():
                    if qty_var.get() > 1:
                        qty_var.set(qty_var.get() - 1)
                        alert.configure(text="")

                ctk.CTkButton(frameq, text="-", width=40, command=dec).pack(side="left", padx=5)
                ctk.CTkLabel(frameq, textvariable=qty_var, font=("Segoe UI", 18)).pack(side="left", padx=6)
                ctk.CTkButton(frameq, text="+", width=40, command=inc).pack(side="left", padx=5)

                def confirm_adj():
                    ok, msg = cart.adjust_quantity(n, qty_var.get())
                    if not ok:
                        alert.configure(text=msg)
                        return
                    refresh_cart()
                    adj_win.destroy()
                    message_label.configure(text=f"{n} quantity updated.", text_color="green", font=("Segoe UI", 20,))

                ctk.CTkButton(adj_win, text="Confirm", command=confirm_adj, fg_color="#2E8B57", hover_color="#256D4A").pack(pady=10)

            ctk.CTkButton(row, text="Remove", command=on_remove, fg_color="orange", hover_color="#e67e22").pack(side="right", padx=6)
            ctk.CTkButton(row, text="Adjust Quantity", command=on_adjust, fg_color="#2E8B57", hover_color="#256D4A").pack(side="right", padx=6)
#validation for submitting with an empty cart and submitting with a valid cart 
    def submit_order_action():
        if cart.is_empty():
            message_label.configure(text="Cart is empty!", text_color="red", font=('Segoe UI', 20))
            return
        if not messagebox.askyesno("Confirm", "Submit your order?"):
            return


#success message 
        messagebox.showinfo("Success", "Your order has been submitted.")
        cart.clear()
        refresh_cart()
        message_label.configure(text="Your order has been submitted!", text_color="green", font=('Segoe UI', 30))

    ctk.CTkButton(content, text="✅ Submit Order", command=submit_order_action,
                  fg_color="#32CD32", hover_color="#28a428", text_color="white",
                  font=("Segoe UI", 20, "bold"), height=55, width=300, corner_radius=15).pack(pady=10)

    refresh_cart()

def show_info_window():
    #Displays help and contact info for the kiosk.
    info_window = ctk.CTkToplevel(root)
    info_window.title("Info / Help")
    info_window.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
    info_window.configure(fg_color=BACKGROUND_COLOR)
    info_window.transient(root)
    info_window.grab_set()
    info_window.focus_force()
    info_window.lift()

    header = ctk.CTkFrame(info_window, fg_color=HEADER_COLOR, height=60)
    header.pack(fill="x")
    ctk.CTkButton(header, text="←", width=40, command=info_window.destroy, fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER).pack(side="left", padx=10, pady=10)
    ctk.CTkLabel(header, text="ℹ️ Info / Help", font=("Segoe UI", 24, "bold"), text_color="white").pack(side="left", padx=20)

    content_frame = ctk.CTkFrame(info_window, fg_color=BACKGROUND_COLOR)
    content_frame.pack(fill="both", expand=True, padx=80, pady=40)

    info_text = ( #the text for the help page
        "📍 123 Banana Street, Melbourne\n"
        "📞 (03) 1234 5678\n"
        "📧 support@fbkiosk.org\n\n"
        "Instructions:\n"
        "1. From the main menu select 'View Items'.\n"
        "2. Use search, category and dietary filters to find items.\n"
        "3. Press 'Add' to select quantity and add to your cart.\n"
        "4. Go to 'View Cart' to review, adjust or remove items, then submit.\n\n"
        "Orders are anonymous. For help ask a staff member."
    )
    ctk.CTkLabel(content_frame, text=info_text, justify="left", font=("Segoe UI", 18), text_color="#333333", wraplength=1000).pack(anchor="w", pady=20)



# Main Root UI
root = ctk.CTk()
root.title("FoodBank Kiosk")
root.geometry("1200x720")
root.configure(fg_color=BACKGROUND_COLOR)

# Title
ctk.CTkLabel(root, text="FoodBank Kiosk", font=("Segoe UI", 36, "bold"), text_color=HEADER_COLOR).pack(pady=30)

# Main menu buttons
ctk.CTkButton(root, text="View Items", command=show_items_window,
              fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER,
              font=("Segoe UI", 20), height=60, width=320).pack(pady=12)

ctk.CTkButton(root, text="View Cart", command=show_order_window,
              fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER,
              font=("Segoe UI", 20), height=60, width=320).pack(pady=12)

ctk.CTkButton(root, text="Info / Help", command=show_info_window,
              fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER,
              font=("Segoe UI", 20), height=60, width=320).pack(pady=12)

ctk.CTkButton(root, text="Exit", command=root.destroy,
              fg_color="#cc3300", hover_color="#990000",
              font=("Segoe UI", 20), height=60, width=320).pack(pady=18)

# Footer
ctk.CTkLabel(root, text="Serving since 2025 | FoodBank Kiosk", font=("Segoe UI", 14), text_color="#666666").pack(side="bottom", pady=8)


# Launch app
root.mainloop()
