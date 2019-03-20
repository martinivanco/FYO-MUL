import wx

class ImagePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.image = wx.Image()
        self.img_w = 0
        self.img_h = 0
        self.widget = wx.StaticBitmap(self, -1, wx.Bitmap(width = 1, height = 1))
        self.widget.SetPosition((5, 5))

    def loadImage(self, path):
        self.image = wx.Bitmap(path).ConvertToImage()
        self.img_w = self.image.GetWidth()
        self.img_h = self.image.GetHeight()
        self.onResize(None)

    def onResize(self, event):
        if self.image.IsOk():
            w_scale = (self.GetSize().GetWidth() - 10) / self.img_w
            h_scale = (self.GetSize().GetHeight() - 10) / self.img_h
            if w_scale < h_scale:
                scaled_img = self.image.Scale(self.img_w * w_scale, self.img_h * w_scale, wx.IMAGE_QUALITY_HIGH)
                h_pos = (self.GetSize().GetHeight() - 10 - self.img_h * w_scale) / 2 + 5
                self.widget.SetPosition((5, h_pos))
            else:
                scaled_img = self.image.Scale(self.img_w * h_scale, self.img_h * h_scale, wx.IMAGE_QUALITY_HIGH)
                w_pos = (self.GetSize().GetWidth() - 10 - self.img_w * h_scale) / 2 + 5
                self.widget.SetPosition((w_pos, 5))
            self.widget.SetBitmap(wx.Bitmap(scaled_img))
            
        if event is not None:
            event.Skip()

class SettingsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

class MainFrame(wx.Frame):    
    def __init__(self):
        super().__init__(parent=None, title='Hello World')
        self.main_panel = wx.Panel(self)
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.image_panel = ImagePanel(self.main_panel)
        self.panel_sizer.Add(self.image_panel, 3, wx.ALL | wx.EXPAND, 0)
        self.settings_panel = SettingsPanel(self.main_panel)
        self.panel_sizer.Add(self.settings_panel, 1, wx.ALL | wx.EXPAND, 0)

        self.main_panel.SetSizer(self.panel_sizer)       
        self.Show()
        self.image_panel.loadImage('test.jpg')

    # def on_press(self, event):
    #     value = self.text_ctrl.GetValue()
    #     if not value:
    #         print("You didn't enter anything!")
    #     else:
    #         print(f'You typed: "{value}"')