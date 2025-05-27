import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

def generate_specular_streak_image(width=800, height=600, streak_width=3, orientation='horizontal'):
    # bacxkground
    img = np.zeros((height, width), dtype=np.float32)

    if orientation == 'horizontal':
        center_y = height // 2
        img[center_y - streak_width // 2:center_y + streak_width // 2, :] = 1.0
    elif orientation == 'vertical':
        center_x = width // 2
        img[:, center_x - streak_width // 2:center_x + streak_width // 2] = 1.0
    elif orientation == 'diagonal':
        for i in range(-streak_width//2, streak_width//2 + 1):
            np.fill_diagonal(np.roll(img, i, axis=1), 1.0)

    img = gaussian_filter(img, sigma=2.0)

    # Sav
    plt.imsave('specular_streak.png', img, cmap='gray')

generate_specular_streak_image()



