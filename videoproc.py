import wx
import pubsub.pub as pub
import threading
from moviepy.video.io.VideoFileClip import *

class VideoRender(threading.Thread):
    def __init__(self, path, cut_times):
        super(VideoRender, self).__init__()
        self.path = path
        self.cut_times = cut_times
        self.start()

    def run(self):
        video = VideoFileClip(self.path)
        clip = video.subclip(self.cut_times[0], self.cut_times[1])
        clip.write_videofile("_tmp.mp4", audio_codec = "aac")
        wx.CallAfter(self.notifyFinished)

    def notifyFinished(self):
        pub.sendMessage("tmp_video")