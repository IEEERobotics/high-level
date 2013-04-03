"""
Utility classes and functions.
"""

import os
import numpy as np

try:
  import cv2
  from cv2 import cv
except ImportError:
  print "You need OpenCV to use vision modules, sorry."
  sys.exit(1)

image_file_exts = ("png", "jpg", "jpeg", "tiff", "bmp", "gif")  # file extensions that indicate image files

class Enum(tuple):
  """Simple enumeration type based on tuple with indices as integer values."""
  
  __getattr__ = tuple.index
  
  fromString = tuple.index
  
  def toString(self, value):
    return self[value]


class KeyCode:
    """Utility class to manage special keys and other keyboard input."""
    
    NUM_LOCK  = 0x100000  # status
    SHIFT     = 0x010000  # combo
    CAPS_LOCK = 0x020000  # status
    CTRL      = 0x040000  # combo
    ALT       = 0x080000  # combo
    SPECIAL   = 0x00ff00  # key down: CTRL, SHIFT, ALT, SUPER, NUM_LOCK, CAPS_LOCK, Fn etc.
    
    @classmethod
    def describeKey(cls, key, showStatus=False):
        """Describe key with modifiers (SHIFT, CTRL, ALT), and optionally status (NUM_LOCK, CAPS_LOCK)."""
        desc  = ""
        
        # * Status
        if showStatus:
            desc += "[" + \
                    "NUM_LOCK "  + ("ON" if key & KeyCode.NUM_LOCK  else "OFF") + ", " + \
                    "CAPS_LOCK " + ("ON" if key & KeyCode.CAPS_LOCK else "OFF") + \
                    "] "
        
        # * Modifiers
        desc += "" + \
                ("Shift + " if key & KeyCode.SHIFT else "") + \
                ("Ctrl + "  if key & KeyCode.CTRL  else "") + \
                ("Alt + "   if key & KeyCode.ALT   else "")
        
        # * Key
        keyByte = key & 0xff # last 8 bits
        keyCode = key & 0x7f  # last 7 bits (ASCII)
        keyChar = chr(keyCode)
        desc += (hex(keyByte) + " (" + str(keyByte) + ")" if key & KeyCode.SPECIAL or keyCode < 32 else keyChar + " (" + str(keyCode) + ")")
        
        return desc


def log_str(obj, func, msg):
    """Compose a log message with an object's class name and (optional) function name."""
    if func is None:
        return "{0}: {1}".format(obj.__class__.__name__, msg)
    else:
        return "{0}.{1}(): {2}".format(obj.__class__.__name__, func, msg)


def log(obj, func, msg):
    """Log a message composed using log_str() to stdout."""
    print log_str(obj, func, msg)


def getFileExtension(filename):
    """Return the extension part of a filename, sans period, in lowercase."""
    return os.path.splitext(filename)[1][1:].strip().lower()


def isImageFile(filename):
    """Decides whether given filename represents an image file type (solely based on extension."""
    return getFileExtension(filename) in image_file_exts


def cvtColorBGR2CMYK_(imageBGR):
  """
  Convert a BGR image to CMYK and return separate color channels as 4-tuple.
  Usage: C, M, Y, K = cvtColorBGR2CMYK_(imageBGR)
  """
  imageBGRScaled = imageBGR / 255.0  # scale to [0,1] range
  B, G, R = cv2.split(imageBGRScaled)  # split channels
  I = np.ones((imageBGRScaled.shape[0], imageBGRScaled.shape[1]))  # identity matrix
  K = I - imageBGRScaled.max(axis=2) - 0.001  # -0.001 is to prevent divide by zero in later steps
  C = (I - R - K) / (I - K)
  M = (I - G - K) / (I - K)
  Y = (I - B - K) / (I - K)
  return C, M, Y, K  # return 4 separate arrays


def cvtColorBGR2CMYK(imageBGR):
  """
  Convert a BGR image to CMYK and return a 4-channel image.
  Usage: imageCMYK = cvtColorBGR2CMYK(imageBGR)
  """
  return cv2.merge(cvtColorBGR2CMYK_(imageBGR))  # return a combined 4-channel image


def rotateImage(image, angle):
    """Rotate an image by the specified angle."""
    imageSize = (image.shape[1], image.shape[0]) # (width, height)
    imageCenter = (imageSize[0] / 2, imageSize[1] / 2)
    rotMat = cv2.getRotationMatrix2D(imageCenter, angle, 1.0)
    result = cv2.warpAffine(image, rotMat, imageSize, flags=cv2.INTER_LINEAR)
    return result
