from shared_components import SharedComponents 


class MyDashboard(SharedComponents):
    def __init__(self):
        super().__init__()
        self.create_title()
        self.create_left_panel()
        
        self.create_button(text="Crops in Monitor\n", x=118, y=75,
                           command=None)
        
        self.create_button(text="Recent Diseases \n Detected", x=270, y=75, 
                           anchor="s", 
                           command=None)
        
        self.create_button(text="Manage Files\n", x=422, y=75, 
                           command=None)
        
        self.create_button(text="Analytics", x=121, y=232, 
                           width=205, height=229, anchor="nw",
                           command=None)
        
        self.create_button(text="Capture Gallery", x=340, y=232,
                           width=222, height=229, anchor="nw",
                           command=None)
        
        self.create_button(text="Disease Record History", x=572, y=75,
                           width=217, height=386, anchor="n",
                           command=None)


    def run(self):
        self.root.mainloop()
