import numpy as np
import cv2
import tools
import wx
import pubsub.pub as pub
import threading
from matplotlib.figure import Figure

class Scale(threading.Thread):
    def __init__(self, panel_size, image_size, image):
        super(Scale, self).__init__()
        self.panel_size = panel_size
        self.image_size = image_size
        self.image = image
        self.start()

    def run(self):
        w_scale = (self.panel_size[0] - 20) / self.image_size[0]
        h_scale = (self.panel_size[1] - 20) / self.image_size[1]
        if w_scale < h_scale:
            scaled_img = self.image.Scale(self.image_size[0] * w_scale, self.image_size[1] * w_scale, wx.IMAGE_QUALITY_NEAREST)
            h_pos = (self.panel_size[1] - 20 - self.image_size[1] * w_scale) / 2 + 10
            wx.CallAfter(self.sendResult, (10, h_pos), scaled_img)
        else:
            scaled_img = self.image.Scale(self.image_size[0] * h_scale, self.image_size[1] * h_scale, wx.IMAGE_QUALITY_NEAREST)
            w_pos = (self.panel_size[0] - 20 - self.image_size[0] * h_scale) / 2 + 10
            wx.CallAfter(self.sendResult, (w_pos, 10), scaled_img)

    def sendResult(self, position, scaled_img):
        pub.sendMessage("scaled", position = position, scaled_image = scaled_img)

class Render(threading.Thread):
    def __init__(self, image_processor, full_render = False):
        super(Render, self).__init__()
        self.image = image_processor.image
        self.exposure = image_processor.exposure
        self.contrast = image_processor.contrast
        self.saturation = image_processor.saturation
        self.sharpening_amount = image_processor.sharpening_amount
        self.sharpening_radius = image_processor.sharpening_radius
        self.sharpening_masking = image_processor.sharpening_masking
        self.denoising = image_processor.denoising
        self.full_render = full_render
        self.start()

    def run(self):
        hsv = np.int16(cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV_FULL))

        if self.exposure != 0:
            hsv[:,:,2] += self.exposure

        if self.contrast != 0:
            old_mean = cv2.mean(hsv[:,:,2])[0]
            if self.contrast < 0:
                c = self.contrast / 125.0 + 1.0
                hsv[:,:,2] = hsv[:,:,2] * c
            if self.contrast > 0:
                c = self.contrast / 50.0 + 1.0
                hsv[:,:,2] = hsv[:,:,2] * c
            correction = int(old_mean - cv2.mean(hsv[:,:,2])[0])
            hsv[:,:,2] += correction
        
        if self.saturation != 0:
            hsv[:,:,1] += self.saturation
        
        if self.sharpening_amount > 0:
            mask = hsv[:,:,2] - cv2.GaussianBlur(hsv[:,:,2], (0, 0), self.sharpening_radius)
            mask[mask < self.sharpening_masking] = 0
            hsv[:,:,2] = hsv[:,:,2] + ((self.sharpening_amount / 50.0) * mask)

        hsv = np.clip(hsv, 0, 255)
        if self.full_render and self.denoising > 0:
            bgr = cv2.cvtColor(np.uint8(hsv), cv2.COLOR_HSV2BGR_FULL)
            bgr = cv2.fastNlMeansDenoisingColored(bgr, h = self.denoising / 10.0, templateWindowSize = 5, searchWindowSize = 15)
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV_FULL)
        
        # TODO correct histogram
        hist_exp = cv2.calcHist([np.uint8(hsv)],[2],None,[256],[0,256])
        final = cv2.cvtColor(np.uint8(hsv), cv2.COLOR_HSV2BGR_FULL)
        hist_b = cv2.calcHist([final],[0],None,[256],[0,256])
        hist_g = cv2.calcHist([final],[1],None,[256],[0,256])
        hist_r = cv2.calcHist([final],[2],None,[256],[0,256])
        wx.CallAfter(self.sendResult, final, (hist_b, hist_g, hist_r, hist_exp))

    def sendResult(self, render, hist_data):
        wx_image = wx.Bitmap.ConvertToImage(wx.Bitmap.FromBuffer(render.shape[1], render.shape[0], cv2.cvtColor(render, cv2.COLOR_BGR2RGB)))
        pub.sendMessage("rendered", render = wx_image, hist_data = hist_data)

class ImageProcessor():
    def __init__(self):
        self.image = None
        self.exposure = 0
        self.contrast = 0
        self.saturation = 0
        self.sharpening_amount = 0
        self.sharpening_radius = 1.0
        self.sharpening_masking = 0
        self.denoising = 0

    def loadImage(self, path):
        self.image = cv2.imread(path)

    def change(self, setting, value):
        if setting & tools.S_EXPOSURE:
            self.exposure = value
        if setting & tools.S_CONTRAST:
            self.contrast = value
        if setting & tools.S_SATURATION:
            self.saturation = value
        if setting & tools.S_SHARPENING_AMOUNT:
            self.sharpening_amount = value
        if setting & tools.S_SHARPENING_RADIUS:
            self.sharpening_radius = value
        if setting & tools.S_SHARPENING_MASKING:
            self.sharpening_masking = value
        if setting & tools.S_DENOISING:
            self.denoising = value