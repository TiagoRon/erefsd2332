import numpy as np
from moviepy.editor import VideoClip
import random

def make_frame_semantic(t, width, height, concept, color_palette, camera_motion="none"):
    """
    Generates a frame based on high-level semantic concepts.
    """
    # Base colors based on palette
    colors = {
        "dark": [10, 10, 10],
        "neon": [0, 255, 200],
        "red": [200, 20, 20],
        "blue": [20, 50, 200],
        "gold": [200, 180, 20],
        "contrast": [255, 255, 255] # Black and white logic tailored below
    }
    
    base_c = np.array(colors.get(color_palette, [20, 20, 30]), dtype=float)
    
    # Grid definition for speed
    # Render at low res internal, upscale later handled by moviepy if returns full size
    # We produce 540x960 internally for speed? No, let's try direct math on blocks.
    w_block = width // 20
    h_block = height // 20
    
    # Normalized coordinates
    # We will generate a small texture and resize it up using numpy repeat to get "digital/tech" look
    # or just simple gradients.
    
    small_w, small_h = 60, 100
    img_small = np.zeros((small_h, small_w, 3), dtype=float)
    
    X, Y = np.meshgrid(np.linspace(-1, 1, small_w), np.linspace(-1, 1, small_h))
    
    # CONCEPT LOGIC
    
    if concept == "brain" or concept == "mente":
        # Network / Neurons
        # Points connecting?
        # Sim: pulsing blobs
        d = np.sqrt(X**2 + Y**2)
        activation = np.sin(d * 10 - t * 3)
        activity_mask = activation > 0.5
        
        img_small[:, :, 0] = base_c[0] * (0.5 + 0.5 * activation)
        img_small[:, :, 1] = base_c[1] * (0.5 + 0.5 * activation)
        img_small[:, :, 2] = base_c[2] * (0.5 + 0.5 * activation)
        
    elif concept == "danger" or concept == "peligro":
        # Flash / Pulse / Shake
        pulse = np.sin(t * 15)
        if pulse > 0.8: # Strobe
            img_small[:] = 255
        else:
            # Gradient red
            grad = Y + (np.sin(t)*0.5)
            mask = grad > 0
            img_small[:, :, 0] = 150 * mask
            img_small[:, :, 1] = 0
            img_small[:, :, 2] = 0
            
    elif concept == "time" or concept == "tiempo":
        # Rotating arm?
        # Sim: Spiral
        angle = np.arctan2(Y, X)
        spiral = np.sin(angle * 4 + t * 5)
        img_small[:, :, 0] = base_c[0] * (spiral > 0)
        img_small[:, :, 1] = base_c[1] * (spiral > 0)
        img_small[:, :, 2] = base_c[2] * (spiral > 0)

    elif concept == "speed" or concept == "velocidad":
        # Tunnel effect
        # Radial streaks
        angle = np.arctan2(Y, X)
        radius = np.sqrt(X**2 + Y**2)
        streaks = np.sin(angle * 20 + t * 50)
        motion = np.sin(radius * 10 - t * 20)
        
        val = (streaks * motion) > 0.5
        img_small[:] = base_c * val[:, :, None]

    elif concept == "hidden" or concept == "oculto" or concept == "void":
        # Fog / Noise
        # Moving noise
        noise = np.sin(X*10 + t) * np.cos(Y*10 - t)
        val = noise * 0.5 + 0.5
        img_small[:] = base_c * val[:, :, None] * 0.5 # Dim

    else:
        # Default Tech/Science grid
        grid_x = np.sin(X * 20 + t) > 0.95
        grid_y = np.sin(Y * 20) > 0.95
        grid = np.logical_or(grid_x, grid_y)
        img_small[:] = base_c * 0.2
        img_small[grid] = base_c

    # Convert to uint8
    img_small = np.clip(img_small, 0, 255).astype('uint8')
    
    # Scale up "Nearest Neighbor" style for digital look (and performance)
    scale_w = width // small_w
    scale_h = height // small_h
    # Simple blocky upscale using repeat
    img_large = np.repeat(np.repeat(img_small, scale_h, axis=0), scale_w, axis=1)
    
    # Pad to exact size
    out = np.zeros((height, width, 3), dtype='uint8')
    h_lim = min(height, img_large.shape[0])
    w_lim = min(width, img_large.shape[1])
    out[:h_lim, :w_lim] = img_large[:h_lim, :w_lim]
    
    return out

def generate_scene_clip(concept, color, duration, output_path):
    """
    Generates a clip for a specific scene configuration.
    """
    w, h = 1080, 1920
    try:
        def make_frame(t):
            return make_frame_semantic(t, w, h, concept, color)
            
        clip = VideoClip(make_frame, duration=duration)
        clip.write_videofile(output_path, fps=30, codec='libx264', preset='ultrafast', logger=None)
        return True
    except Exception as e:
        print(f"Error generating scene {concept}: {e}")
        return False

# Deprecated procedural func kept for compat if needed, but mapped to new logic
def generate_procedural_background(theme, output_path, duration=15):
    return generate_scene_clip(theme, "neon", duration, output_path)


if __name__ == "__main__":
    generate_procedural_background("ciencia", "test_bg_ciencia.mp4", duration=5)
