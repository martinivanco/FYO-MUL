import wx
import gui
import imgproc
import os

if __name__ == '__main__':
    app = wx.App()
    image_processor = imgproc.ImageProcessor()
    frame = gui.MainFrame(image_processor)
    app.MainLoop()
    if os.path.exists(os.path.join(os.getcwd(), "_tmp.mp4")):
        os.remove(os.path.join(os.getcwd(), "_tmp.mp4"))