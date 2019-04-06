S_EXPOSURE = 1
S_CONTRAST = 2
S_SATURATION = 4
S_TEMPERATURE = 8
S_TINT = 16
S_HIGHLIGHTS = 32
S_SHADOWS = 64
S_WHITES = 128
S_BLACKS = 256
S_CLARITY = 512
S_VIBRANCE = 1024
S_SHARPENING_AMOUNT = 2048
S_SHARPENING_RADIUS = 4096
S_SHARPENING_MASKING = 8192

def get_setting_name(setting):
    if setting & S_EXPOSURE:
        return "Exposure"
    if setting & S_CONTRAST:
        return "Contrast"
    if setting & S_SATURATION:
        return "Saturation"
    if setting & S_TEMPERATURE:
        return "Temp"
    if setting & S_TINT:
        return "Tint"
    if setting & S_SHARPENING_AMOUNT:
        return "Amount"
    if setting & S_SHARPENING_RADIUS:
        return "Radius"
    if setting & S_SHARPENING_MASKING:
        return "Masking"
    return "Unknown"