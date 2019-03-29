import tools
import imgproc
import wx
import wx.lib.scrolledpanel as scroll
import pubsub.pub as pub

class SettingSlider(wx.Panel):
    def __init__(self, parent, setting, image_processor):
        super().__init__(parent)
        self.setting = setting
        self.image_processor = image_processor
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
    
        self.label = wx.StaticText(self, label = tools.get_setting_name(self.setting), size = (70, 15))
        self.panel_sizer.Add(self.label, 0)
        self.slider = wx.Slider(self, value = 0, minValue = -100, maxValue = 100)
        self.panel_sizer.Add(self.slider, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        self.value = wx.StaticText(self, label = "0", size = (30, 15))
        self.panel_sizer.Add(self.value, 0)

        self.slider.Bind(wx.EVT_SCROLL, self.onScroll)
        self.SetSizer(self.panel_sizer)

    def onScroll(self, event):
        self.value.SetLabel(str(self.slider.GetValue()))
        self.image_processor.change(self.setting, self.slider.GetValue())
        imgproc.Render(self.image_processor)

class SettingsPanel(scroll.ScrolledPanel):
    def __init__(self, parent, image_processor):
        super().__init__(parent)
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)

        self.exposure = SettingSlider(self, tools.S_EXPOSURE, image_processor)
        self.panel_sizer.Add(self.exposure, 0, wx.ALL | wx.EXPAND, 5)
        self.contrast = SettingSlider(self, tools.S_CONTRAST, image_processor)
        self.panel_sizer.Add(self.contrast, 0, wx.ALL | wx.EXPAND, 5)
        self.saturation = SettingSlider(self, tools.S_SATURATION, image_processor)
        self.panel_sizer.Add(self.saturation, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(self.panel_sizer)
        self.SetupScrolling()

class ImagePanel(wx.Panel):
    def __init__(self, parent, image_processor):
        super().__init__(parent)
        self.image_processor = image_processor
        self.image = wx.Image()
        self.img_w = 0
        self.img_h = 0
        self.widget = wx.StaticBitmap(self, -1, wx.Bitmap(width = 1, height = 1))
        self.widget.SetPosition((10, 10))
        self.Bind(wx.EVT_SIZE, self.onResize)
        pub.subscribe(self.onRender, "rendered")

    def loadImage(self, path):
        self.image = wx.Bitmap(path).ConvertToImage()
        self.img_w = self.image.GetWidth()
        self.img_h = self.image.GetHeight()
        self.onResize(None)
        self.image_processor.loadImage(path)

    def onResize(self, event):
        # TODO DO THIS IN ANOTHER THREAD
        if self.image.IsOk():
            w_scale = (self.GetSize().GetWidth() - 20) / self.img_w
            h_scale = (self.GetSize().GetHeight() - 20) / self.img_h
            if w_scale < h_scale:
                scaled_img = self.image.Scale(self.img_w * w_scale, self.img_h * w_scale, wx.IMAGE_QUALITY_NEAREST)
                h_pos = (self.GetSize().GetHeight() - 20 - self.img_h * w_scale) / 2 + 10
                self.widget.SetPosition((10, h_pos))
            else:
                scaled_img = self.image.Scale(self.img_w * h_scale, self.img_h * h_scale, wx.IMAGE_QUALITY_NEAREST)
                w_pos = (self.GetSize().GetWidth() - 20 - self.img_w * h_scale) / 2 + 10
                self.widget.SetPosition((w_pos, 10))
            self.widget.SetBitmap(wx.Bitmap(scaled_img))
            
        if event is not None:
            event.Skip()

    def onRender(self, render):
        self.image = render
        self.onResize(None)

class MainFrame(wx.Frame):    
    def __init__(self, image_processor):
        super().__init__(parent=None, title='Brightroom')
        self.main_panel = wx.Panel(self)
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.image_panel = ImagePanel(self.main_panel, image_processor)
        self.panel_sizer.Add(self.image_panel, 2, wx.ALL | wx.EXPAND, 0)
        self.settings_panel = SettingsPanel(self.main_panel, image_processor)
        self.panel_sizer.Add(self.settings_panel, 1, wx.ALL | wx.EXPAND, 0)

        self.main_panel.SetSizer(self.panel_sizer)
        self.SetSize((900, 600))
        self.SetMinSize((900, 600))
        self.Show()
        self.image_panel.loadImage('test.jpg')
