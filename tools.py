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
S_SHARPEN_AMOUNT = 2048
S_SHARPEN_RADIUS = 4096
S_SHARPEN_MASKING = 8192
S_DENOISE = 16384
S_VIGNETTE = 32768
S_DISTORT = 65536
BULHARSKA_KONSTANTA = 0.083984375

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
    if setting & S_HIGHLIGHTS:
        return "Highlights"
    if setting & S_SHADOWS:
        return "Shadows"
    if setting & S_WHITES:
        return "Whites"
    if setting & S_BLACKS:
        return "Blacks"
    if setting & S_SHARPEN_AMOUNT:
        return "Amount"
    if setting & S_SHARPEN_RADIUS:
        return "Radius"
    if setting & S_SHARPEN_MASKING:
        return "Masking"
    if setting & S_DENOISE:
        return "Denoise"
    if setting & S_VIGNETTE:
        return "Vignetting"
    if setting & S_DISTORT:
        return "Distortion"
    return "Unknown"