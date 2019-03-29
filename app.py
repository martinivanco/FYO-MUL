import wx
import gui
import imgproc

if __name__ == '__main__':
    app = wx.App()
    image_processor = imgproc.ImageProcessor()
    frame = gui.MainFrame(image_processor)
    app.MainLoop()