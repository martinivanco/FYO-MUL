import numpy as np
import cv2
import tools
import wx
import pubsub.pub as pub
import threading

class Render(threading.Thread):
    def __init__(self, image_processor):
        super(Render, self).__init__()
        self.image = image_processor.image
        self.exposure = image_processor.exposure
        self.contrast = image_processor.contrast
        self.saturation = image_processor.saturation
        self.start()

    def run(self):
        hsv = np.int16(cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV_FULL))
        hsv[:,:,2] += self.exposure
        hsv = np.clip(hsv, 0, 255)
        final = cv2.cvtColor(np.uint8(hsv), cv2.COLOR_HSV2BGR_FULL)
        wx.CallAfter(self.sendResult, final)

    def sendResult(self, render):
        wx_image = wx.Bitmap.ConvertToImage(wx.Bitmap.FromBuffer(render.shape[1], render.shape[0], cv2.cvtColor(render, cv2.COLOR_BGR2RGB)))
        pub.sendMessage("rendered", render = wx_image)

class ImageProcessor():
    def __init__(self):
        self.image = None
        self.exposure = 0
        self.contrast = 0
        self.saturation = 0

    def loadImage(self, path):
        self.image = cv2.imread(path)

    def change(self, setting, value):
        if setting & tools.S_EXPOSURE:
            self.exposure = value
        if setting & tools.S_CONTRAST:
            self.contrast = value
        if setting & tools.S_SATURATION:
            self.saturation = value