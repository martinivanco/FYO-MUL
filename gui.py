import tools
import imgproc
import wx
import wx.lib.scrolledpanel as scroll
import pubsub.pub as pub
import matplotlib as mpl
import matplotlib.backends.backend_wxagg as wxagg
from matplotlib.figure import Figure
import numpy as np

class SettingSlider(wx.Panel):
    def __init__(self, parent, setting, image_processor, lower_bound = -100, higher_bound = 100, default = 0, factor = 1):
        super().__init__(parent)
        self.setting = setting
        self.image_processor = image_processor
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.factor = factor
    
        self.label = wx.StaticText(self, label = tools.get_setting_name(self.setting), size = (70, 18))
        self.panel_sizer.Add(self.label, 0)
        self.slider = wx.Slider(self, value = default, minValue = lower_bound, maxValue = higher_bound)
        self.panel_sizer.Add(self.slider, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        self.value = wx.StaticText(self, label = str(default * self.factor)[:3], size = (30, 15))
        self.panel_sizer.Add(self.value, 0)

        self.slider.Bind(wx.EVT_SCROLL, self.onScroll)
        self.slider.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.onRelease)
        self.SetSizer(self.panel_sizer)

    def onScroll(self, event):
        self.value.SetLabel(str(self.slider.GetValue() * self.factor)[:4 if self.slider.GetValue() < 0 else 3])
        self.image_processor.change(self.setting, self.slider.GetValue() * self.factor)
        imgproc.Render(self.image_processor)
        event.Skip()

    def onRelease(self, event):
        imgproc.Render(self.image_processor, True)
        event.Skip()

class SettingsPanel(scroll.ScrolledPanel):
    def __init__(self, parent, image_processor):
        super().__init__(parent)
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)

        self.figure = Figure()
        self.figure.subplots_adjust(bottom=0.01, top=0.99, left=0.01, right=0.99)
        self.histogram = wxagg.FigureCanvasWxAgg(self, -1, self.figure)
        self.histogram.SetMinSize((1, 150))
        self.panel_sizer.Add(self.histogram, 0, wx.ALL | wx.EXPAND, 5)

        self.exposure = SettingSlider(self, tools.S_EXPOSURE, image_processor)
        self.panel_sizer.Add(self.exposure, 0, wx.ALL | wx.EXPAND, 5)
        self.contrast = SettingSlider(self, tools.S_CONTRAST, image_processor)
        self.panel_sizer.Add(self.contrast, 0, wx.ALL | wx.EXPAND, 5)
        self.saturation = SettingSlider(self, tools.S_SATURATION, image_processor)
        self.panel_sizer.Add(self.saturation, 0, wx.ALL | wx.EXPAND, 5)

        self.label_sharpen = wx.StaticText(self, label = "Sharpening")
        self.panel_sizer.Add(self.label_sharpen, 0, wx.ALL | wx.EXPAND, 5)
        self.sharpen_amount = SettingSlider(self, tools.S_SHARPEN_AMOUNT, image_processor, 0, 150)
        self.panel_sizer.Add(self.sharpen_amount, 0, wx.ALL | wx.EXPAND, 5)
        self.sharpen_radius = SettingSlider(self, tools.S_SHARPEN_RADIUS, image_processor, 5, 30, 10, 0.1)
        self.panel_sizer.Add(self.sharpen_radius, 0, wx.ALL | wx.EXPAND, 5)
        self.sharpen_masking = SettingSlider(self, tools.S_SHARPEN_MASKING, image_processor, 0)
        self.panel_sizer.Add(self.sharpen_masking, 0, wx.ALL | wx.EXPAND, 5)
        self.denoise = SettingSlider(self, tools.S_DENOISE, image_processor, 0)
        self.panel_sizer.Add(self.denoise, 0, wx.ALL | wx.EXPAND, 5)

        self.vignette = SettingSlider(self, tools.S_VIGNETTE, image_processor)
        self.panel_sizer.Add(self.vignette, 0, wx.ALL | wx.EXPAND, 5)
        self.distort = SettingSlider(self, tools.S_DISTORT, image_processor)
        self.panel_sizer.Add(self.distort, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(self.panel_sizer)
        self.SetupScrolling()
        pub.subscribe(self.onHistogram, "rendered")

    def onHistogram(self, render, hist_data):
        self.figure.clf()
        tmp = self.figure.add_subplot(111)
        tmp.axis('off')
        tmp.set_xmargin(0)
        tmp.set_ymargin(0)
        x = np.arange(0, 256, 1)
        tmp.fill_between(x, 0, hist_data[0][:,0], facecolor='#2196f3')
        tmp.fill_between(x, 0, hist_data[1][:,0], facecolor='#4caf50')
        tmp.fill_between(x, 0, hist_data[2][:,0], facecolor='#f44336')
        tmp.fill_between(x, 0, hist_data[3][:,0], facecolor='#9e9e9e')
        self.histogram.draw()

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
        pub.subscribe(self.onScale, "scaled")

    def loadImage(self, path):
        self.image = wx.Bitmap(path).ConvertToImage()
        self.img_w = self.image.GetWidth()
        self.img_h = self.image.GetHeight()
        self.image_processor.loadImage(path)
        imgproc.Render(self.image_processor)

    def onResize(self, event):
        if self.image.IsOk():
            imgproc.Scale((self.GetSize().GetWidth(), self.GetSize().GetHeight()), (self.img_w, self.img_h), self.image)
            
        if event is not None:
            event.Skip()

    def onScale(self, position, scaled_image):
        self.widget.SetPosition(position)
        self.widget.SetBitmap(wx.Bitmap(scaled_image))

    def onRender(self, render, hist_data):
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
