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
            scaled_img = self.image.Scale(self.image_size[0] * w_scale, self.image_size[1] * w_scale, wx.IMAGE_QUALITY_BILINEAR)
            h_pos = (self.panel_size[1] - 20 - self.image_size[1] * w_scale) / 2 + 10
            wx.CallAfter(self.sendResult, (10, h_pos), scaled_img)
        else:
            scaled_img = self.image.Scale(self.image_size[0] * h_scale, self.image_size[1] * h_scale, wx.IMAGE_QUALITY_BILINEAR)
            w_pos = (self.panel_size[0] - 20 - self.image_size[0] * h_scale) / 2 + 10
            wx.CallAfter(self.sendResult, (w_pos, 10), scaled_img)

    def sendResult(self, position, scaled_img):
        pub.sendMessage("scaled", position = position, scaled_image = scaled_img)

class Equalize(threading.Thread):
    def __init__(self, image_processor):
        super(Equalize, self).__init__()
        self.image = image_processor.full_image
        self.start()

    def run(self):
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        equalized = cv2.equalizeHist(hsv[:,:,2])
        hsv[:,:,2] = equalized
        hist_exp = cv2.calcHist([hsv], [2], None, [256], (0,256))
        final = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        hist_b = cv2.calcHist([final], [0], None, [256], (0,256))
        hist_g = cv2.calcHist([final], [1], None, [256], (0,256))
        hist_r = cv2.calcHist([final], [2], None, [256], (0,256))
        wx.CallAfter(self.sendResult, final, (hist_b, hist_g, hist_r, hist_exp))

    def sendResult(self, render, hist_data):
        wx_image = wx.Bitmap.ConvertToImage(wx.Bitmap.FromBuffer(render.shape[1], render.shape[0], cv2.cvtColor(render, cv2.COLOR_BGR2RGB)))
        pub.sendMessage("rendered", render = wx_image, hist_data = hist_data)

class Render(threading.Thread):
    def __init__(self, image_processor, full_render = False):
        super(Render, self).__init__()
        if image_processor.full_image is None:
            return
        self.full_image = image_processor.full_image
        self.full_gauss2d = image_processor.full_gauss2d
        self.full_camera = image_processor.full_camera
        self.quick_image = image_processor.quick_image
        self.quick_gauss2d = image_processor.quick_gauss2d
        self.quick_camera = image_processor.quick_camera
        self.distortion_coeffs = image_processor.distortion_coeffs
        self.exposure = image_processor.exposure
        self.contrast = image_processor.contrast
        self.saturation = image_processor.saturation
        self.sharpen_amount = image_processor.sharpen_amount
        self.sharpen_radius = image_processor.sharpen_radius
        self.sharpen_masking = image_processor.sharpen_masking
        self.denoise = image_processor.denoise
        self.vignette = image_processor.vignette
        self.distort = image_processor.distort
        self.full_render = full_render
        self.start()

    def run(self):
        if self.full_render:
            self.render(self.full_image, self.full_gauss2d, self.full_camera)
        else:
            self.render(self.quick_image, self.quick_gauss2d, self.quick_camera)

    def render(self, image, gauss2d, camera):
        hsv = np.int16(cv2.cvtColor(image, cv2.COLOR_BGR2HSV))

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
        
        if self.sharpen_amount > 0:
            mask = hsv[:,:,2] - cv2.GaussianBlur(hsv[:,:,2], (0, 0), self.sharpen_radius)
            mask[mask < self.sharpen_masking] = 0
            hsv[:,:,2] = hsv[:,:,2] + ((self.sharpen_amount / 50.0) * mask)

        if self.denoise > 0:
            hsv = np.clip(hsv, 0, 255)
            bgr = cv2.cvtColor(np.uint8(hsv), cv2.COLOR_HSV2BGR)
            if self.full_render:
                bgr = cv2.fastNlMeansDenoisingColored(bgr, h = self.denoise / 10.0, templateWindowSize = 5, searchWindowSize = 15)
            else:
                bgr = cv2.GaussianBlur(bgr, (0, 0), self.denoise / 25.0)
            hsv = np.int16(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV))

        if self.vignette != 0:
            hsv[:,:,2] = hsv[:,:,2] + np.int16(gauss2d * self.vignette)
        
        if self.distort != 0:
            self.distortion_coeffs[0,0] = self.distort * 1.0e-5
            h, w, c = image.shape
            matrix, roi = cv2.getOptimalNewCameraMatrix(camera, self.distortion_coeffs, (w,h), 1, (w,h))
            hsv = np.clip(hsv, 0, 255)
            bgr = cv2.cvtColor(np.uint8(hsv), cv2.COLOR_HSV2BGR)
            bgr = cv2.undistort(bgr, camera, self.distortion_coeffs, None, matrix)
            x, y, w, h = roi
            bgr = bgr[y:y+h, x:x+w]
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        hsv = np.clip(hsv, 0, 255)
        hist_exp = cv2.calcHist([np.uint8(hsv)], [2], None, [256], (0,256))
        final = cv2.cvtColor(np.uint8(hsv), cv2.COLOR_HSV2BGR)
        hist_b = cv2.calcHist([final], [0], None, [256], (0,256))
        hist_g = cv2.calcHist([final], [1], None, [256], (0,256))
        hist_r = cv2.calcHist([final], [2], None, [256], (0,256))
        wx.CallAfter(self.sendResult, final, (hist_b, hist_g, hist_r, hist_exp))

    def sendResult(self, render, hist_data):
        wx_image = wx.Bitmap.ConvertToImage(wx.Bitmap.FromBuffer(render.shape[1], render.shape[0], cv2.cvtColor(render, cv2.COLOR_BGR2RGB)))
        pub.sendMessage("rendered", render = wx_image, hist_data = hist_data)

class ImageProcessor():
    def __init__(self):
        self.full_image = None
        self.full_gauss2d = None
        self.full_camera = None
        self.quick_image = None
        self.quick_gauss2d = None
        self.quick_camera = None
        self.distortion_coeffs = np.zeros((4,1), np.float64)
        self.exposure = 0
        self.contrast = 0
        self.saturation = 0
        self.sharpen_amount = 0
        self.sharpen_radius = 1.0
        self.sharpen_masking = 0
        self.denoise = 0
        self.vignette = 0
        self.distort = 0

    def loadImage(self, path):
        self.full_image = cv2.imread(path)
        height, width, channels = self.full_image.shape
        self.full_gauss2d = self.getGauss2D(width, height)
        self.full_camera = self.getCamera(width, height)

        if width > 512 or height > 512:
            w_scale = 512.0 / width
            h_scale = 512.0 / height
            if w_scale < h_scale:
                width = int(width * w_scale) 
                height = int(height * w_scale) 
                self.quick_image = cv2.resize(self.full_image, (width, height), interpolation = cv2.INTER_AREA)
            else:
                width = int(width * h_scale) 
                height = int(height * h_scale) 
                self.quick_image = cv2.resize(self.full_image, (width, height), interpolation = cv2.INTER_AREA)
                
            self.quick_gauss2d = self.getGauss2D(width, height)
            self.quick_camera = self.getCamera(width, height)
        else:
            self.quick_image = self.full_image
            self.quick_gauss2d = self.full_gauss2d
            self.quick_camera = self.full_camera

    def getGauss2D(self, width, height):
        g2d = cv2.getGaussianKernel(height, height / 2) * cv2.getGaussianKernel(width, width / 2).T
        g2d = 1.0 / g2d
        g2d -= g2d.min()
        return g2d / g2d.max()

    def getCamera(self, width, height):
        camera = np.eye(3, dtype = np.float32)
        camera[0,0] = tools.BULHARSKA_KONSTANTA * min(width, height)
        camera[1,1] = tools.BULHARSKA_KONSTANTA * min(width, height)
        camera[0,2] = width / 2.0
        camera[1,2] = height / 2.0
        return camera

    def change(self, setting, value):
        if setting & tools.S_EXPOSURE:
            self.exposure = value
        if setting & tools.S_CONTRAST:
            self.contrast = value
        if setting & tools.S_SATURATION:
            self.saturation = value
        if setting & tools.S_SHARPEN_AMOUNT:
            self.sharpen_amount = value
        if setting & tools.S_SHARPEN_RADIUS:
            self.sharpen_radius = value
        if setting & tools.S_SHARPEN_MASKING:
            self.sharpen_masking = value
        if setting & tools.S_DENOISE:
            self.denoise = value
        if setting & tools.S_VIGNETTE:
            self.vignette = value
        if setting & tools.S_DISTORT:
            self.distort = value