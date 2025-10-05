from shared_components import SharedComponents

class MyDashboard(SharedComponents):
    def __init__(self):
        super().__init__()
        self.create_title()
        self.create_left_panel()
        self.create_dashboard_buttons()

    def run(self):
        self.root.mainloop()
