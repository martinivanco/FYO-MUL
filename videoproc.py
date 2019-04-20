import wx
import pubsub.pub as pub
import threading
from moviepy.video.io.VideoFileClip import *
from moviepy.video.compositing.concatenate import *

class VideoCut(threading.Thread):
    def __init__(self, path, cut_times):
        super(VideoCut, self).__init__()
        self.path = path
        self.cut_times = cut_times
        self.start()

    def run(self):
        video = VideoFileClip(self.path)
        clip = video.subclip(self.cut_times[0], self.cut_times[1])
        clip.write_videofile("_tmp.mp4", audio_codec = "aac", verbose = False)
        wx.CallAfter(self.notifyFinished)

    def notifyFinished(self):
        pub.sendMessage("tmp_video")

class VideoMerge(threading.Thread):
    def __init__(self, path1, path2, save_path):
        super(VideoMerge, self).__init__()
        self.path1 = path1
        self.path2 = path2
        self.save_path = save_path
        self.start()

    def run(self):
        try:
            clip1 = VideoFileClip(self.path1)
        except Exception:
            wx.CallAfter(self.notifyFinished, False, "Couldn't open first video.")
            return
        try:
            clip2 = VideoFileClip(self.path2)
        except Exception:
            wx.CallAfter(self.notifyFinished, False, "Couldn't open second video.")
            return
        merged = concatenate_videoclips([clip1,clip2])
        merged.write_videofile(self.save_path, audio_codec = "aac", verbose = False)
        wx.CallAfter(self.notifyFinished, True)

    def notifyFinished(self, status, message = None):
        pub.sendMessage("merged", status = status, message = message)