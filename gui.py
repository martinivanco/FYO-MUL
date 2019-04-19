import tools
import imgproc
import videoproc
import wx
import wx.lib.scrolledpanel as scroll
import wx.media
import pubsub.pub as pub
import matplotlib as mpl
import matplotlib.backends.backend_wxagg as wxagg
from matplotlib.figure import Figure
import numpy as np
import ffprobe3
import re
import os

class InfoLabel(wx.Panel):
    def __init__(self, parent, name, value = ""):
        super().__init__(parent)
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.label = wx.StaticText(self, label = name, size = (110, 20))
        self.label.SetForegroundColour((255, 255, 255))
        self.label.SetFont(font)
        self.panel_sizer.Add(self.label, 0)

        self.value = wx.StaticText(self, label = str(value))
        self.value.SetForegroundColour((255, 255, 255))
        self.value.SetFont(font)
        self.panel_sizer.Add(self.value, 1, wx.LEFT | wx.EXPAND, 5)

        self.SetSizer(self.panel_sizer)

    def setValue(self, value):
        self.value.SetLabelText(str(value))

class InfoPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.panel_sizer.Add(wx.Panel(self), 1, wx.EXPAND)
        self.red = wx.StaticText(self, label = "R:", size = (50, 20))
        self.red.SetForegroundColour((255, 255, 255))
        self.red.SetFont(font)
        self.panel_sizer.Add(self.red, 0)
        self.green = wx.StaticText(self, label = "G:", size = (50, 20))
        self.green.SetForegroundColour((255, 255, 255))
        self.green.SetFont(font)
        self.panel_sizer.Add(self.green, 0)
        self.blue = wx.StaticText(self, label = "B:", size = (50, 20))
        self.blue.SetForegroundColour((255, 255, 255))
        self.blue.SetFont(font)
        self.panel_sizer.Add(self.blue, 0)
        self.panel_sizer.Add(wx.Panel(self), 1, wx.EXPAND)

        self.SetSizer(self.panel_sizer)
        pub.subscribe(self.onMouseMove, "mouse_move")
        pub.subscribe(self.onMouseLeave, "mouse_leave")

    def onMouseMove(self, values):
        self.red.SetLabelText("R: {}".format(values[0]))
        self.green.SetLabelText("G: {}".format(values[1]))
        self.blue.SetLabelText("B: {}".format(values[2]))

    def onMouseLeave(self):
        self.red.SetLabelText("R:")
        self.green.SetLabelText("G:")
        self.blue.SetLabelText("B:")

class SettingSlider(wx.Panel):
    def __init__(self, parent, setting, image_processor, lower_bound = -100, higher_bound = 100, default = 0, factor = 1):
        super().__init__(parent)
        self.setting = setting
        self.image_processor = image_processor
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.factor = factor
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    
        self.label = wx.StaticText(self, label = tools.get_setting_name(self.setting), size = (80, 18))
        self.label.SetFont(font)
        self.label.SetForegroundColour((255, 255, 255))
        self.panel_sizer.Add(self.label, 0)
        self.slider = wx.Slider(self, value = default, minValue = lower_bound, maxValue = higher_bound)
        self.panel_sizer.Add(self.slider, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        self.value = wx.StaticText(self, label = str(default * self.factor)[:3], size = (40, 15))
        self.value.SetFont(font)
        self.value.SetForegroundColour((255, 255, 255))
        self.panel_sizer.Add(self.value, 0)

        self.slider.Bind(wx.EVT_SCROLL, self.onScroll)
        self.slider.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.onRelease)
        self.SetSizer(self.panel_sizer)

    def onScroll(self, event):
        self.value.SetLabel(str(self.slider.GetValue() * self.factor)[:4 if self.slider.GetValue() < 0 else 3])
        self.image_processor.change(self.setting, self.slider.GetValue() * self.factor)
        imgproc.Render(self.image_processor)
        if event is not None:
            event.Skip()

    def onRelease(self, event):
        imgproc.Render(self.image_processor, True)
        event.Skip()

class TimePanel(wx.Panel):
    def __init__(self, parent, name, video):
        super().__init__(parent)
        self.video = video
        self.time = 0.0
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.label = wx.StaticText(self, label = name)
        self.label.SetForegroundColour((255, 255, 255))
        self.label.SetFont(font)
        self.panel_sizer.Add(self.label, 0, wx.BOTTOM | wx.EXPAND, 5)

        self.input = wx.TextCtrl(self, value = "00:00:00.00")
        self.panel_sizer.Add(self.input, 0, wx.BOTTOM | wx.EXPAND, 5)

        self.button = wx.Button(self, label = "Set Current")
        self.panel_sizer.Add(self.button, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 25)

        self.input.Bind(wx.EVT_KILL_FOCUS, self.onSetTime)
        self.button.Bind(wx.EVT_BUTTON, self.onPress)
        self.SetSizer(self.panel_sizer)

    def onSetTime(self, event):
        f = re.compile("..:..:..{}..".format(re.escape(".")))
        if f.match(self.input.GetValue()) is None:
            self.time = 0.0
            self.input.SetValue("00:00:00.00")
        if event is not None:
            event.Skip()

    def onPress(self, event):
        self.time = self.video.getCurrentTime()
        f = "%02d" % round((self.time % 1) * 100)
        s = "%02d" % round(self.time % 60)
        m = "%02d" % round(self.time % 3600 // 60)
        h = round(self.time // 3600)
        h = "99" if h > 99 else "%02d" % h
        self.input.SetValue("{}:{}:{}.{}".format(h, m, s, f))
        if event is not None:
            event.Skip()

class EditPanel(wx.Panel):
    def __init__(self, parent, video_length):
        super().__init__(parent)
        self.video_length = video_length
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.begin = TimePanel(self, "From:", parent.image_panel)
        self.panel_sizer.Add(self.begin, 1, wx.RIGHT, 10)
        self.end = TimePanel(self, "To:", parent.image_panel)
        self.panel_sizer.Add(self.end, 1)

        self.SetSizer(self.panel_sizer)

    def getCutTimes(self):
        if self.begin.time < self.end.time: # TODO check video length
            return (self.begin.time, self.end.time)
        else:
            return None #TODO show dialog


class SettingsPanel(scroll.ScrolledPanel):
    def __init__(self, parent, image_processor, image_panel):
        super().__init__(parent)
        self.video_mode = False
        self.video_path = None
        self.video_orig = True
        self.image_processor = image_processor
        self.image_panel = image_panel
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.photoSetup()
        self.SetSizer(self.panel_sizer)
        self.SetupScrolling()
        pub.subscribe(self.onHistogram, "rendered")
        pub.subscribe(self.onVideo, "tmp_video")

    def onHistogram(self, render, hist_data = None):
        if hist_data is None:
            return
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

    def resetSettings(self):
        self.exposure.slider.SetValue(0)
        self.exposure.onScroll(None)
        self.contrast.slider.SetValue(0)
        self.contrast.onScroll(None)
        self.saturation.slider.SetValue(0)
        self.saturation.onScroll(None)
        self.sharpen_amount.slider.SetValue(0)
        self.sharpen_amount.onScroll(None)
        self.sharpen_radius.slider.SetValue(10)
        self.sharpen_radius.onScroll(None)
        self.sharpen_masking.slider.SetValue(0)
        self.sharpen_masking.onScroll(None)
        self.denoise.slider.SetValue(0)
        self.denoise.onScroll(None)
        self.vignette.slider.SetValue(0)
        self.vignette.onScroll(None)
        self.distort.slider.SetValue(0)
        self.distort.onScroll(None)

    def photoSetup(self):
        self.figure = Figure()
        self.figure.subplots_adjust(bottom=0.01, top=0.99, left=0.01, right=0.99)
        self.histogram = wxagg.FigureCanvasWxAgg(self, -1, self.figure)
        self.histogram.SetMinSize((1, 150))
        self.figure.set_facecolor('#282828')
        self.panel_sizer.Add(self.histogram, 0, wx.ALL | wx.EXPAND, 5)
        self.info_panel = InfoPanel(self)
        self.panel_sizer.Add(self.info_panel, 0, wx.ALL | wx.EXPAND, 5)
        self.line0 = wx.StaticLine(self, -1, style = wx.LI_HORIZONTAL)
        self.line0.SetBackgroundColour((255, 255, 255))
        self.panel_sizer.Add(self.line0, 0, wx.ALL | wx.EXPAND, 10)

        self.exposure = SettingSlider(self, tools.S_EXPOSURE, self.image_processor)
        self.panel_sizer.Add(self.exposure, 0, wx.ALL | wx.EXPAND, 5)
        self.contrast = SettingSlider(self, tools.S_CONTRAST, self.image_processor)
        self.panel_sizer.Add(self.contrast, 0, wx.ALL | wx.EXPAND, 5)
        self.saturation = SettingSlider(self, tools.S_SATURATION, self.image_processor)
        self.panel_sizer.Add(self.saturation, 0, wx.ALL | wx.EXPAND, 5)
        self.line1 = wx.StaticLine(self, -1, style = wx.LI_HORIZONTAL)
        self.line1.SetBackgroundColour((255, 255, 255))
        self.panel_sizer.Add(self.line1, 0, wx.ALL | wx.EXPAND, 10)

        self.label_sharpen = wx.StaticText(self, label = "Sharpening")
        self.label_sharpen.SetFont(self.font)
        self.label_sharpen.SetForegroundColour((255, 255, 255))
        self.panel_sizer.Add(self.label_sharpen, 0, wx.ALL | wx.EXPAND, 5)
        self.sharpen_amount = SettingSlider(self, tools.S_SHARPEN_AMOUNT, self.image_processor, 0, 150)
        self.panel_sizer.Add(self.sharpen_amount, 0, wx.ALL | wx.EXPAND, 5)
        self.sharpen_radius = SettingSlider(self, tools.S_SHARPEN_RADIUS, self.image_processor, 5, 30, 10, 0.1)
        self.panel_sizer.Add(self.sharpen_radius, 0, wx.ALL | wx.EXPAND, 5)
        self.sharpen_masking = SettingSlider(self, tools.S_SHARPEN_MASKING, self.image_processor, 0)
        self.panel_sizer.Add(self.sharpen_masking, 0, wx.ALL | wx.EXPAND, 5)
        self.denoise = SettingSlider(self, tools.S_DENOISE, self.image_processor, 0)
        self.panel_sizer.Add(self.denoise, 0, wx.ALL | wx.EXPAND, 5)
        self.line2 = wx.StaticLine(self, -1, style = wx.LI_HORIZONTAL)
        self.line2.SetBackgroundColour((255, 255, 255))
        self.panel_sizer.Add(self.line2, 0, wx.ALL | wx.EXPAND, 10)

        self.vignette = SettingSlider(self, tools.S_VIGNETTE, self.image_processor)
        self.panel_sizer.Add(self.vignette, 0, wx.ALL | wx.EXPAND, 5)
        self.distort = SettingSlider(self, tools.S_DISTORT, self.image_processor)
        self.panel_sizer.Add(self.distort, 0, wx.ALL | wx.EXPAND, 5)

    def videoSetup(self, video_path):
        self.video_path = video_path
        self.label_info = wx.StaticText(self, label = "Video properties:")
        self.label_info.SetFont(self.font)
        self.label_info.SetForegroundColour((255, 255, 255))
        self.panel_sizer.Add(self.label_info, 0, wx.ALL | wx.EXPAND, 5)

        metadata = ffprobe3.FFProbe(video_path)
        audio_stream = None
        video_stream = None
        for stream in metadata.streams:
            if stream.is_video():
                video_stream = stream
            if stream.is_audio():
                audio_stream = stream

        if video_stream is None:
            return
        self.resolution = InfoLabel(self, "Resolution:", video_stream.__dict__["width"] + "x" + video_stream.__dict__["height"])
        self.panel_sizer.Add(self.resolution, 0, wx.ALL | wx.EXPAND, 5)
        self.length = InfoLabel(self, "Length:", video_stream.__dict__["duration"] + " s")
        self.panel_sizer.Add(self.length, 0, wx.ALL | wx.EXPAND, 5)
        self.fps = InfoLabel(self, "Frame rate:", video_stream.__dict__["r_frame_rate"].split("/")[0] + " fps")
        self.panel_sizer.Add(self.fps, 0, wx.ALL | wx.EXPAND, 5)
        self.video_codec = InfoLabel(self, "Video codec:", video_stream.codec())
        self.panel_sizer.Add(self.video_codec, 0, wx.ALL | wx.EXPAND, 5)
        self.video_bitrate = InfoLabel(self, "Video bitrate:", video_stream.__dict__["bit_rate"] + " bps")
        self.panel_sizer.Add(self.video_bitrate, 0, wx.ALL | wx.EXPAND, 5)
        if audio_stream is None:
            return
        self.audio_codec = InfoLabel(self, "Audio codec:", audio_stream.codec())
        self.panel_sizer.Add(self.audio_codec, 0, wx.ALL | wx.EXPAND, 5)
        self.audio_bitrate = InfoLabel(self, "Audio bitrate:", audio_stream.__dict__["bit_rate"] + " bps")
        self.panel_sizer.Add(self.audio_bitrate, 0, wx.ALL | wx.EXPAND, 5)

        self.line0 = wx.StaticLine(self, -1, style = wx.LI_HORIZONTAL)
        self.line0.SetBackgroundColour((255, 255, 255))
        self.panel_sizer.Add(self.line0, 0, wx.ALL | wx.EXPAND, 10)
        self.label_cut = wx.StaticText(self, label = "Cut section:")
        self.label_cut.SetFont(self.font)
        self.label_cut.SetForegroundColour((255, 255, 255))
        self.panel_sizer.Add(self.label_cut, 0, wx.ALL | wx.EXPAND, 5)
        self.edit_panel = EditPanel(self, float(video_stream.__dict__["duration"]))
        self.panel_sizer.Add(self.edit_panel, 0, wx.ALL | wx.EXPAND, 5)
        self.button = wx.Button(self, label = "Render")
        self.panel_sizer.Add(self.button, 0, wx.ALL | wx.EXPAND, 30)
        self.button.Bind(wx.EVT_BUTTON, self.onButton)
        
    def setMode(self, mode, video_path = None):
        if not self.video_mode and not mode:
            self.resetSettings()
            return
        if self.video_mode and not mode:
            self.button.Unbind(wx.EVT_BUTTON)
            self.button.Destroy()
            self.edit_panel.Destroy()
            self.label_cut.Destroy()
            self.line0.Destroy()
            self.audio_bitrate.Destroy()
            self.audio_codec.Destroy()
            self.video_bitrate.Destroy()
            self.video_codec.Destroy()
            self.fps.Destroy()
            self.length.Destroy()
            self.resolution.Destroy()
            self.info_title.Destroy()
            self.photoSetup()
            self.panel_sizer.Layout()
            self.video_mode = mode
            return
        if not self.video_mode and mode:
            self.distort.Destroy()
            self.vignette.Destroy()
            self.line2.Destroy()
            self.denoise.Destroy()
            self.sharpen_masking.Destroy()
            self.sharpen_radius.Destroy()
            self.sharpen_amount.Destroy()
            self.label_sharpen.Destroy()
            self.line1.Destroy()
            self.saturation.Destroy()
            self.contrast.Destroy()
            self.exposure.Destroy()
            self.line0.Destroy()
            self.info_panel.Destroy()
            self.histogram.Destroy()
            self.videoSetup(video_path)
            self.panel_sizer.Layout()
            self.video_mode = mode
            return

    def onButton(self, event):
        if self.video_orig:
            cut_times = self.edit_panel.getCutTimes()
            if cut_times is not None:
                self.button.Disable()
                self.button.SetLabel("Rendering...")
                videoproc.VideoRender(self.video_path, cut_times)
        else:
            self.image_panel.loadVideo(self.video_path)
            self.video_orig = True
            self.button.SetLabel("Render")
        if event is not None:
            event.Skip()

    def onVideo(self):
        self.image_panel.loadVideo(os.path.join(os.getcwd(), "_tmp.mp4"))
        self.video_orig = False
        self.button.SetLabel("Show original")
        self.button.Enable()

class ImagePanel(wx.Panel):
    def __init__(self, parent, image_processor):
        super().__init__(parent)
        self.video_mode = False
        self.image_processor = image_processor
        self.image = wx.Image()
        self.img_w = 0
        self.img_h = 0
        self.scaled_image = None
        self.widget = wx.StaticBitmap(self, -1, wx.Bitmap(width = 1, height = 1))
        self.widget.SetPosition((10, 10))
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.widget.Bind(wx.EVT_ENTER_WINDOW, self.onEnterWindow)
        self.widget.Bind(wx.EVT_LEAVE_WINDOW, self.onLeaveWindow)
        pub.subscribe(self.onRender, "rendered")
        pub.subscribe(self.onScale, "scaled")

    def set_mode(self, mode):
        if self.video_mode and not mode:
            self.widget.Destroy()
            self.widget = wx.StaticBitmap(self, -1, wx.Bitmap(width = 1, height = 1))
            self.widget.SetPosition((10, 10))
            self.video_mode = mode
            return
        if not self.video_mode and mode:
            self.image = wx.Image()
            self.scaled_image = None
            self.widget.Destroy()
            self.widget = wx.media.MediaCtrl(self)
            self.video_mode = mode
            return

    def loadImage(self, path):
        self.set_mode(False)
        self.image = wx.Bitmap(path).ConvertToImage()
        self.img_w = self.image.GetWidth()
        self.img_h = self.image.GetHeight()
        self.image_processor.loadImage(path)
        imgproc.Render(self.image_processor, True)

    def loadVideo(self, path):
        self.set_mode(True)
        self.widget.Load(path)
        self.widget.ShowPlayerControls()
        self.img_w = self.widget.GetBestSize().GetWidth()
        self.img_h = self.widget.GetBestSize().GetHeight()
        self.onResize(None)

    def saveImage(self, path):
        self.image.SaveFile(path)

    def getCurrentTime(self):
        if not self.video_mode:
            return None
        return round(self.widget.Tell() / 10) / 100.0

    def onResize(self, event):
        if self.video_mode:
            panel_width = self.GetSize().GetWidth()
            panel_height = self.GetSize().GetHeight()
            w_scale = (panel_width - 20) / self.img_w
            h_scale = (panel_height - 20) / self.img_h
            if w_scale < h_scale:
                self.widget.SetSize((self.img_w * w_scale, self.img_h * w_scale))
                h_pos = (panel_height - 20 - self.img_h * w_scale) / 2 + 10
                self.widget.SetPosition((10, h_pos))
            else:
                self.widget.SetSize((self.img_w * h_scale, self.img_h * h_scale))
                w_pos = (panel_width - 20 - self.img_w * h_scale) / 2 + 10
                self.widget.SetPosition((w_pos, 10))
                
        else:
            if self.image.IsOk():
                imgproc.Scale((self.GetSize().GetWidth(), self.GetSize().GetHeight()), (self.img_w, self.img_h), self.image)
            
            if event is not None:
                event.Skip()

    def onEnterWindow(self, event):
        self.widget.Bind(wx.EVT_MOTION, self.onMouseMove)
        event.Skip()

    def onLeaveWindow(self, event):
        self.widget.Unbind(wx.EVT_MOTION)
        pub.sendMessage("mouse_leave")
        event.Skip()

    def onMouseMove(self, event):
        if self.scaled_image is not None:
            p = event.GetPosition()
            v = (self.scaled_image.GetRed(p.x, p.y), self.scaled_image.GetGreen(p.x, p.y), self.scaled_image.GetBlue(p.x, p.y))
            pub.sendMessage("mouse_move", values = v)
        event.Skip()

    def onScale(self, position, scaled_image):
        self.widget.SetPosition(position)
        self.widget.SetBitmap(wx.Bitmap(scaled_image))
        self.scaled_image = scaled_image

    def onRender(self, render, hist_data = None):
        self.image = render
        self.onResize(None)

class MainFrame(wx.Frame):    
    def __init__(self, image_processor):
        super().__init__(parent=None, title='Brightroom')
        self.main_panel = wx.Panel(self)
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.image_processor = image_processor

        self.image_panel = ImagePanel(self.main_panel, image_processor)
        self.panel_sizer.Add(self.image_panel, 2, wx.ALL | wx.EXPAND, 0)
        self.settings_panel = SettingsPanel(self.main_panel, image_processor, self.image_panel)
        self.panel_sizer.Add(self.settings_panel, 1, wx.ALL | wx.EXPAND, 0)

        self.menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        item_open = file_menu.Append(wx.ID_OPEN, 'Open', 'Open an image or video')
        self.Bind(wx.EVT_MENU, self.onOpen, item_open)
        item_save = file_menu.Append(wx.ID_SAVE, 'Save', 'Save the image or video')
        self.Bind(wx.EVT_MENU, self.onSave, item_save)
        self.menu_bar.Append(file_menu, '&File')

        edit_menu = wx.Menu()
        item_equalize = edit_menu.Append(wx.ID_DEFAULT, 'Equalize', 'Equalize histogram')
        self.Bind(wx.EVT_MENU, self.onEqualize, item_equalize)
        self.menu_bar.Append(edit_menu, '&Edit')
        
        self.SetMenuBar(self.menu_bar)
        self.main_panel.SetBackgroundColour((40, 40, 40))
        self.main_panel.SetSizer(self.panel_sizer)
        self.SetSize((900, 600))
        self.SetMinSize((900, 600))
        self.Show()

    def onOpen(self, event):
        with wx.FileDialog(self, "Open file", wildcard="JPEG, PNG, BMP and MP4 files (*.jpg;*.png;*.bmp;*.mp4)|*.jpg;*.png;*.bmp;*.mp4", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            try:
                fps = file_dialog.GetPath().split('.')
                video = fps[len(fps) - 1] == "mp4"
                self.settings_panel.setMode(video, file_dialog.GetPath())
                if video:
                    self.image_panel.loadVideo(file_dialog.GetPath())
                else:
                    self.image_panel.loadImage(file_dialog.GetPath())
            except:
                print("ERROR: Cannot open file.")

    def onSave(self, event):
        with wx.FileDialog(self, "Save file", wildcard="JPEG, PNG, BMP and MP4 files (*.jpg;*.png;*.bmp;*.mp4)|*.jpg;*.png;*.bmp;*.mp4", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            try:
                self.image_panel.saveImage(file_dialog.GetPath())
            except:
                print("ERROR: Cannot save file.")

    def onEqualize(self, event):
        if self.image_panel.video_mode:
            pass # TODO show dialog
        else:
            imgproc.Equalize(self.image_processor)
