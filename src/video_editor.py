from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, ColorClip, CompositeVideoClip, concatenate_audioclips, concatenate_videoclips, CompositeAudioClip
import moviepy.video.fx.all as vfx
import os
from moviepy.audio.fx.all import audio_loop
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
from src.constants import MUSIC_MOODS, FONT_PATH, CHANNEL_NAME

# Fix for Pillow 10+ removing ANTIALIAS
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

class EffectsManager:
    """
    Manages the visual style ("Vibe") and Effects of the video.
    Ensures mandatory Intro/Outro and varied Middle effects.
    """
    STYLE_HIGH_ENERGY = "high_energy"
    STYLE_SMOOTH = "smooth"
    STYLE_MINIMAL = "minimal"
    
    def __init__(self):
        self.current_style = random.choice([
            self.STYLE_HIGH_ENERGY,
            self.STYLE_SMOOTH,
            self.STYLE_MINIMAL,
            self.STYLE_HIGH_ENERGY # Slight bias towards energy
        ])
        print(f"🎬 VIDEO VIBE: {self.current_style.upper()}")
        
        # Track usage to avoid repetition
        self.used_middle_effects = []
        self.last_effect_time = -10
        
        # Select Mandatory Effects
        # User requested MANDATORY 'glitch' for Intro (after title) and Outro (end).
        self.intro_effect = "glitch_start"
        self.outro_effect = "glitch_out"
        
        print(f"   ✨ Intro: {self.intro_effect} | Outro: {self.outro_effect}")

    def get_zoom_func(self, direction="in", duration=5):
        if direction == "in":
            return lambda t: 1 + 0.04 * (t / duration)
        else: # out
            return lambda t: 1.04 - 0.04 * (t / duration)

    def get_middle_effect(self, current_time, duration):
        """
        Decides if a middle effect should be applied and which one.
        Returns: effect_name or None
        """
        # Minimum padding between effects (e.g., 5 seconds)
        if current_time - self.last_effect_time < 5.0:
            return None
            
        # Probability based on style
        prob = 0.3
        if self.current_style == self.STYLE_HIGH_ENERGY: prob = 0.5
        elif self.current_style == self.STYLE_SMOOTH: prob = 0.2
        elif self.current_style == self.STYLE_MINIMAL: prob = 0.1
        
        if random.random() > prob and duration < 6.0:
            return None
            
        # Available effects
        # User requested DYNAMIC but NOT NOISY.
        # Added: 'soft_zoom', 'slide_left'
        opts = ["glitch_mild", "soft_zoom", "slide_left"]
        
        # Filter recently used
        choices = [o for o in opts if o not in self.used_middle_effects[-2:]]
        if not choices: choices = opts
        
        effect = random.choice(choices)
        self.used_middle_effects.append(effect)
        self.last_effect_time = current_time
        return effect

    def get_transition_prob(self):
        if self.current_style == self.STYLE_HIGH_ENERGY:
            return 0.7 # High chance of transition
        elif self.current_style == self.STYLE_SMOOTH:
            return 0.4
        return 0.1 # Minimal

    def should_glitch(self, duration):
        prob = 0.15
        if self.current_style == self.STYLE_HIGH_ENERGY:
            prob = 0.35
        elif self.current_style == self.STYLE_SMOOTH:
            prob = 0.05
        
        return (random.random() < prob) or (duration > 6.0)

# --- VFX PRIMITIVES ---

def vfx_pulse(clip, duration=0.3):
    """Brief brightness pulse"""
    return clip.fx(vfx.colorx, 1.5).set_duration(duration)

def vfx_slide_in(clip, duration=0.5, direction="left"):
    w, h = clip.size
    if direction == "left":
        return clip.set_position(lambda t: (int(-w + w*(t/duration)), "center") if t < duration else "center")
    return clip

def vfx_zoom_fast(clip, mode="in", duration=0.5):
    if mode == "in":
        return clip.resize(lambda t: 1 + 0.5 * t)
    return clip.resize(lambda t: 1 - 0.5 * t)

def _glitch_frame_impl(im, intensity=25):
    """
    Applies RGB Split glitch to a single frame.
    """
    shift = random.randint(-intensity, intensity)
    if shift == 0: return im
    
    # Roll R and G channels in opposite directions
    r = np.roll(im[:,:,0], shift, axis=1)
    g = np.roll(im[:,:,1], -shift, axis=1)
    b = im[:,:,2]
    return np.stack([r, g, b], axis=2)

def create_flash_transition():
    """Returns a white ColorClip fading out."""
    return ColorClip(size=(1080, 1920), color=(255,255,255), duration=0.3).fadeout(0.3)

def vfx_glitch_clip(clip, duration=0.4):
    """
    Takes a clip, slices the first 'duration' seconds, applies glitch, 
    and returns it. 
    """
    if clip.duration < duration:
        duration = clip.duration
    c = clip.subclip(0, duration)
    return c.fl_image(_glitch_frame_impl)

def vfx_shake(clip, strength=5):
    """Simple random shake effect"""
    return clip.set_position(lambda t: (random.randint(-strength, strength), random.randint(-strength, strength)))

def vfx_soft_zoom(clip, duration=None, mode="in"):
    """
    Subtle Ken Burns effect (1.0 -> 1.1).
    Efficient enough for short clips.
    """
    if duration is None: duration = clip.duration
    
    # OPTIMIZATION: Use Crop instead of Resize per frame (Huge speedup)
    # 1. Resize ONCE to target scale (e.g. 1.15x)
    # 2. Crop a moving window
    
    w, h = clip.size
    target_scale = 1.15
    new_w = int(w * target_scale)
    new_h = int(h * target_scale)
    
    # Resize once
    large_clip = clip.resize((new_w, new_h))
    
    # Define Crop Window Movement
    # Mode IN: Start from Center (cropped) -> End at Full?
    # Actually Ken Burns "Zoom In" means the view gets smaller relative to image -> Image gets bigger.
    # So we view a smaller and smaller portion of the original?
    # Or simplified: We have a Big Image. We show a 1080x1920 window.
    # Zoom IN: Window starts Large (scaled down to fit) -> Window ends Small (actual pixels).
    # That implies per-frame Resize of the window? Yes.
    
    # RE-THINK:
    # "Zoom In" visual effect = The object gets bigger. 
    # Implementation: Object scales UP.
    # Previous (Slow): clip.resize(t: 1.0 -> 1.15)
    #
    # Optimization with Crop (Mock Zoom):
    # If we have a 1.15x image.
    # We can take a 1080x1920 crop.
    # If we pan across it, it's a Pan, not Zoom.
    # To do a Zoom *without* resize per frame is impossible unless we accept "Pixelated Zoom" (nearest neighbor)? No.
    #
    # ACTUALLY: MoviePy's 'resize' is slow because it uses PIL.resize every frame.
    # Is there a faster way? 
    # 'scikit-image' or 'cv2' backends? MoviePy defaults to PIL.
    #
    # COMPROMISE:
    # 1. Make the zoom very subtle (1.05x) and accept the cost?
    # 2. OR use a simple Pan (Ken Burns Pan) which IS optimizable via crop.
    # The user accepted "Ken Burns" which usually implies Pan & Zoom.
    # Let's switch to a "Slow Pan" effect for the images. It looks Cinematic and is 10x faster.
    #
    # Optimized Pan Logic:
    # Resize to 1.1x ONCE.
    # Pan from (0,0) to (end, end) or similar.
    
    extra_scale = 0.10
    new_w = int(w * (1 + extra_scale))
    new_h = int(h * (1 + extra_scale))
    
    large_clip = clip.resize((new_w, new_h))
    
    # Center crop dimensions
    x_center = new_w // 2
    y_center = new_h // 2
    
    # We need a 1080x1920 window
    # Pan range
    max_dx = (new_w - w) // 2
    max_dy = (new_h - h) // 2
    
    if mode == "in":
        # Pan from Top-Left to Center? Or Center to Bottom-Right?
        # Let's just do a subtle linear pan.
        # From (-dx, -dy) to (dx, dy) relative to center?
        # clip.crop expects x1, y1, w, h
        
        # We use scroll.
        # large_clip is 1188x2112. We need 1080x1920.
        # Available slack: 108px x 192px.
        
        return large_clip.fx(vfx.scroll, w=w, h=h, x_speed=10, y_speed=10)
        
    # BACKTRACK: vfx.scroll is weird loops.
    # Let's just stick to the specific lambda crop on the large clip.
    # Crop is faster than resize.
    
    def crop_get_frame(t):
        # Linear interp
        progress = t / duration
        
        # Start at Top Left slack, End at Bottom Right slack
        # Slack
        slack_w = new_w - w
        slack_h = new_h - h
        
        if mode == "in":
             # Pan Down-Right
             x1 = int(slack_w * progress)
             y1 = int(slack_h * progress)
        else:
             # Pan Up-Left
             x1 = int(slack_w * (1-progress))
             y1 = int(slack_h * (1-progress))
             
        return large_clip.crop(x1=x1, y1=y1, width=w, height=h).get_frame(0)
        
    # Return a VideoClip with the custom make_frame
    # Note: 'large_clip' is an ImageClip so get_frame(0) is fast/cached? 
    # Actually ImageClip stores img in memory. Crop is fast array slice.
    
    return VideoFileClip(None) if False else clip.resize(lambda t: 1.0 + 0.05 * (t/duration)) 
    
    # WAIT. Writing a custom MakeFrame is risky if I get it wrong (user corruption fear).
    # The SAFEST optimization is to reduce the zoom amount and ensuring 'preset=veryfast'.
    # 50 minutes is definitely primarily due to the SUBTITLES (hundreds of text layers).
    # The Ken Burns resize is heavy but for 3-5 images it shouldn't be 50 mins.
    #
    # Let's revert to a simpler, lighter resize using only 1.05x (less interpolation work?)
    # No, work is same.
    #
    # Decision: Keep the Resize but strictly minimal, AND confirm the Subtitle Fix is the hero.
    # I will just clean up the 'extra_scale' variable to be consistent.
    
    extra_scale = 0.05 # Reduced from 0.15 to 0.05 for speed/subtlety
    if mode == "in":
        return clip.resize(lambda t: 1 + extra_scale * (t / duration))
    else:
        return clip.resize(lambda t: 1.05 - extra_scale * (t / duration))

def vfx_slide_transition(clip, start_delay=0, duration=0.5, direction="left"):
    """
    Simulates the clip 'sliding in' from a direction.
    """
    w, h = clip.size
    
    def pos(t):
        if t < start_delay: 
            # Not started yet (effectively invisible if we manage layering right, or just static)
            # Actually for a transition, we usually start at t=0 relative to the clip start
            return "center"
            
        rel_t = t - start_delay
        if rel_t > duration:
            return "center"
        
        progress = rel_t / duration
        # Ease out cubic
        progress = 1 - (1 - progress)**3
        
        if direction == "left": # From Left to Center
            start_x = -w
            return (int(start_x + (0 - start_x)*progress), "center")
        elif direction == "right":
             start_x = w
             return (int(start_x + (0 - start_x)*progress), "center")
        elif direction == "bottom":
             start_y = h
             return ("center", int(start_y + (0 - start_y)*progress))
             
        return "center"

    return clip.set_position(pos)

def vfx_vignette(clip, intensity=0.3):
    """
    Adds a subtle dark vignette to the corners.
    intensity: 0.0 to 1.0 (opacity of the vignette layer)
    """
    # Create a radial gradient mask? MoviePy is slow at this.
    # Alternatives: Just a PNG overlay or a simple color mask.
    # Let's try to perform it using standard composition if possible, 
    # OR simpler: just darken borders?
    
    # Efficient method: 
    # Create an image with radial gradient and overlay it.
    # Since generating it on fly is annoying with PIL every frame, let's make it once.
    w, h = clip.size
    
    # Check if we have a mask cached? No, just create new.
    # For speed, let's assume 1080x1920.
    
    return clip.fx(vfx.margin, 0).fx(vfx.mask_color, color=[0,0,0], thr=0, s=0) 
    # ACTUALLY, simpler approach for "Texture": 
    # Just a very low opacity dark frame
    return clip # Placeholder if too complex for speed.
    
    # Real Vignette implementation using ColorClip + Mask? Too slow.

def vfx_progress_bar(clip, color=(255, 0, 0), height=15):
    """
    Adds a progress bar at the bottom.
    Dynamically generated per frame = Unique frames.
    """
    w, h = clip.size
    d = clip.duration
    
    # We create a ColorClip that moves?
    # Or simpler: A generator clip.
    def make_bar(t):
        if d == 0: progress = 0
        else: progress = t / d
        
        bar_w = int(w * progress)
        # Return a numpy array for the bar?
        # Actually, using ColorClip is easier but requires compositing every frame.
        # Let's use a simpler approach: A static ColorClip of full width, masked by a moving mask?
        # No, moving mask checks duration. 
        return ColorClip(size=(max(1, bar_w), height), color=color).get_frame(t)

    # Efficient way: 
    # Create a full width ColorClip, set a mask that reveals it over time.
    bar = ColorClip(size=(w, height), color=color)
    bar = bar.set_duration(d) # CRITICAL FIX: Set duration!
    
    # Mask: Moving white rectangle.
    # It's faster to just use a custom clip generation function if we wanted, 
    # but MoviePy composition is easier.
    
    # Let's use a dynamic position approach.
    # 1. Start with bar at x = -w
    # 2. Move to x = 0
    # No, that slides it. We want stretch.
    
    # Resize approach (easiest for GPU/CPU):
    # Take a 1xHeight pixel bar, resize its Width over time.
    # But resize is slow per frame.
    
    # Let's try the Sliding Bar approach: simpler and looks cool.
    # Bar starts fully off-screen left, slides in.
    bar = bar.set_position(lambda t: (int(-w + w*(t/d)), h - height))
    
    # CRITICAL: Ensure composite has duration
    return CompositeVideoClip([clip, bar], size=(w,h)).set_duration(d)

def vfx_grain(clip, intensity=0.05):
    """
    Adds film grain noise overlay. 
    Using a static noise image looped is faster than generating per frame.
    """
    # Just return clip if noise is too heavy.
    # We will simulate "Noise" by just adding a static overlay with very low opacity
    # that jitters position slightly.
    return clip # Placeholder for now to avoid rendering crash.
    # Grain is heavy.


def vfx_color_grade(clip, preset="cinematic"):
    """
    Applies a color grade to make the video look more produced.
    Standard 'Cinematic' = slight contrast boost + saturation helper.
    """
    # Contrast Boost (lum=0, contrast=0.15) makes it punchy
    # This helps differentiate from flat raw stock footage.
    return clip.fx(vfx.lum_contrast, lum=0, contrast=0.15, contrast_thr=127)

def vfx_mirror(clip):
    """
    Horizontally flips the video. 
    Strong signature change for avoiding 'Reused Content'.
    """
    return clip.fx(vfx.mirror_x)

def create_title_card(text, duration=2.5, width=1080, height=1920):
    """
    Creates a 'Cuadradito' style title badge.
    Deep Yellow/Orange background box, Black text. 
    Appears centered.
    """
    if not text: return None
    
    # Font Setup
    # Font Setup
    fontsize = 90
    font_path = FONT_PATH  # Use the constant instead of hardcoded Windows path
    try:
        font = ImageFont.truetype(font_path, fontsize)
    except IOError:
        # Fallback: Try to find any .ttf in assets
        try:
            possible_fonts = [f for f in os.listdir("assets/fonts") if f.endswith(".ttf")]
            if possible_fonts:
                fallback = os.path.join("assets/fonts", possible_fonts[0])
                font = ImageFont.truetype(fallback, fontsize)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
    # Wrap text
    lines = textwrap.wrap(text, width=18)
    
    # Measure Text
    img_temp = Image.new('RGBA', (1, 1))
    draw_temp = ImageDraw.Draw(img_temp)
    
    line_metrics = []
    max_w = 0
    total_text_h = 0
    
    for line in lines:
        bbox = draw_temp.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        max_w = max(max_w, w)
        line_metrics.append((w, h))
        total_text_h += h + 15 # Line spacing
    
    total_text_h -= 15 # Remove last spacing
    
    # Box Dimensions (Padding)
    pad_x = 40
    pad_y = 30
    box_w = max_w + (pad_x * 2)
    box_h = total_text_h + (pad_y * 2)
    
    # Draw Final Image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Center Box
    box_x1 = (width - box_w) // 2
    box_y1 = (height - box_h) // 2
    box_x2 = box_x1 + box_w
    box_y2 = box_y1 + box_h
    
    # Draw "Cuadradito" (Rounded Rect logic manually or just rect)
    # Yellow/Gold Background
    draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill="#FFC107", outline="white", width=4)
    
    # Draw Text
    curr_y = box_y1 + pad_y
    for i, line in enumerate(lines):
        w, h = line_metrics[i]
        line_x = box_x1 + (box_w - w) // 2
        
        # Black Text
        draw.text((line_x, curr_y), line, font=font, fill="black")
        curr_y += h + 15
        
    # Clip
    clip = ImageClip(np.array(img)).set_duration(duration).set_position(("center", 350))
    
    # Animation: Slide Up or Just Pop
    # Let's do a simple pop in
    clip = clip.resize(lambda t: min(1, 0.8 + 2*t) if t < 0.1 else 1)
    
    return clip

def create_karaoke_clips(word_timings, duration, start_offset, width=1080, height=1920, fontsize=110, raw_text="", is_header=False):
    # Professional Shorts Style: Single Line Focused
    if is_header:
        fontsize = 90 # Slightly smaller to fit box
    else:
        fontsize = 110 # Bigger
    
    # Load Font - Custom Branding
    font_path = FONT_PATH
    font = None
    
    print(f"   🔎 Debug Font Path: {os.path.abspath(font_path)}")
    if os.path.exists(font_path):
        print("      ✅ Font file exists at path.")
    else:
        print("      ❌ Font file NOT FOUND at path.")
        
    try:
        font = ImageFont.truetype(font_path, fontsize)
        print(f"      ✅ Loaded Custom Font: {font_path}")
    except IOError as e:
        print(f"      ⚠️ Failed to load custom font {font_path}: {e}")
        # Fallback: Try to find any .ttf in assets
        try:
            possible_fonts = [f for f in os.listdir("assets/fonts") if f.endswith(".ttf")]
            if possible_fonts:
                fallback = os.path.join("assets/fonts", possible_fonts[0])
                print(f"      🔄 Retrying with fallback: {fallback}")
                font = ImageFont.truetype(fallback, fontsize)
            else:
                print("      ❌ No fallback fonts found in assets/fonts.")
                font = ImageFont.load_default()
        except Exception as ex:
            print(f"      ❌ Fallback failed: {ex}")
            font = ImageFont.load_default()

    # Pre-calculate Layout (Map words to lines)
    if is_header:
        # Box header: Allow slightly wider lines
        chars_per_line = 20
    else:
        # If fallback to default font (PIL default is tiny), we need huge adjustments or it will be unreadable.
        # But load_default() returns a font object that might behave differently.
        # Let's verify what font object we have.
        if isinstance(font, ImageFont.FreeTypeFont): # Changed from ImageFont.ImageFont to ImageFont.FreeTypeFont for accuracy
             # TrueType
             # INCREASED ESTIMATE: Montserrat ExtraBold is WIDE. 0.50 was too optimistic.
             avg_char_width = fontsize * 0.65 
        else:
             # Default (Bitmap?)
             avg_char_width = 10 # Tiny
             
        # Use narrower width to force 2-4 words per line (Punchy style)
        # Reduced multiplier from 0.7 to 0.6 to give more safety margin
        chars_per_line = int((width * 0.6) / avg_char_width) 
    
    # Prepare full_text
    full_text = raw_text if raw_text else ""
    
    if not full_text and not word_timings:
        return []

    # --- CRITICAL FIX: Sanitize Timings to match Visual Tokens ---
    # Issue: TTS might return "New York" as 1 item, but textwrap splits it into 2.
    # Result: Desync.
    # Solution: Flatten timings so 1 timing entry = 1 visual word.
    
    sanitized_timings = []
    if word_timings:
        for w_data in word_timings:
            # 1. Strip whitespace
            raw_w = w_data.get('word', '').strip()
            if not raw_w: continue # Skip empty/silence
            
            # 2. Check for internal spaces
            sub_words = raw_w.split()
            if len(sub_words) == 1:
                sanitized_timings.append({
                    'word': raw_w,
                    'start': w_data['start'],
                    'end': w_data['end']
                })
            else:
                # Split duration among sub-words
                total_dur = w_data['end'] - w_data['start']
                char_counts = [len(sw) for sw in sub_words]
                total_chars = sum(char_counts)
                
                curr_start = w_data['start']
                for sw, chars in zip(sub_words, char_counts):
                    # Proportional duration
                    portion = chars / total_chars if total_chars > 0 else 1/len(sub_words)
                    sw_dur = total_dur * portion
                    
                    sanitized_timings.append({
                        'word': sw,
                        'start': curr_start,
                        'end': curr_start + sw_dur
                    })
                    curr_start += sw_dur
    
    word_timings = sanitized_timings # Replace with clean list
    
    # Re-generate full_text strictly from sanitized list to ensure 100% match
    full_text = " ".join([w['word'] for w in word_timings])

    if not full_text:
        return []

    lines_strings = textwrap.wrap(full_text, width=chars_per_line)
    
    # Map global word index to (line_index, word_in_line_index, line_string)
    word_map = {} 
    
    global_w_idx = 0
    parsed_lines = []
    
    for l_idx, line_str in enumerate(lines_strings):
        l_words = line_str.split()
        parsed_lines.append(l_words)
        for w_in_l_idx, w_str in enumerate(l_words):
             word_map[global_w_idx] = {
                 "line_idx": l_idx,
                 "word_idx_in_line": w_in_l_idx,
                 "line_words": l_words
             }
             global_w_idx += 1
    
    # Pre-calculate optimal font size per line to prevent clipping
    # Map: line_idx -> (font_object)
    line_font_map = {}
    
    # Init temp drawer for measurement
    img_temp = Image.new('RGBA', (1, 1))
    draw_temp = ImageDraw.Draw(img_temp)
    
    for l_idx, line_str in enumerate(lines_strings):
        # Start with default size
        curr_fontsize = fontsize
        while True:
            try:
                if "impact" in font_path.lower():
                     tmp_font = ImageFont.truetype(font_path, curr_fontsize)
                else:
                     tmp_font = ImageFont.truetype(font_path, curr_fontsize)
            except:
                tmp_font = ImageFont.load_default()
                break
                
            # Measure
            bbox = draw_temp.textbbox((0, 0), line_str, font=tmp_font)
            line_w = bbox[2] - bbox[0]
            
            # Allow smaller font (down to 20px) and check against safe width (width - 100)
            if line_w <= (width - 100) or curr_fontsize <= 20:
                line_font_map[l_idx] = tmp_font
                if curr_fontsize < fontsize:
                     print(f"      🔧 Resizing line '{line_str[:15]}...' to {curr_fontsize}px (Width: {line_w})")
                break
            
            # Reduce and retry
            curr_fontsize -= 5
            
    # Colors
    if is_header:
        active_color = "black" 
        default_color = "black" 
        box_color = "#FFC107"
        box_border = "white"
        stroke_width = 0 
    else:
        active_color = "#FFD700" # Gold
        default_color = "white"
        stroke_color = "black"
        stroke_width = 8 
        shadow_offset = (8, 8)
        shadow_color = "black"

    # --- OPTIMIZATION: Generate Single Concatenated Track ---
    # 1. Resolve Overlaps & Gaps
    final_timings = []
    prev_end = 0
    
    for i in range(len(word_timings)):
        w = word_timings[i]
        start = w['start'] + start_offset
        end = w['end'] + start_offset
        
        if start < prev_end:
            start = max(start, prev_end)
        if end <= start: end = start + 0.1 
        
        gap = start - prev_end
        if gap < 0: gap = 0 
        
        final_timings.append({
            'word': w['word'],
            'start': start,
            'end': end,
            'duration': end - start,
            'gap_before': gap,
            'original_idx': i
        })
        prev_end = end

    # 2. Build Clip Sequence
    clips_sequence = []
    
    # Initial Gap from 0 to first word
    if final_timings and final_timings[0]['start'] > 0:
        clips_sequence.append(ColorClip(size=(width, height), color=(0,0,0,0), duration=final_timings[0]['start']))
        
    for ft in final_timings:
        # Add Gap
        if ft['gap_before'] > 0.05:
            clips_sequence.append(ColorClip(size=(width, height), color=(0,0,0,0), duration=ft['gap_before']))
            
        # Add Word Frame
        orig_i = ft['original_idx']
        if orig_i not in word_map: continue
        
        mapping = word_map[orig_i]
        current_line_words = mapping["line_words"]
        l_idx = mapping["line_idx"]
        active_word_in_line = mapping["word_idx_in_line"]
        
        line_font = line_font_map.get(l_idx, font)
        
        # Draw Frame
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        full_line_lbl = " ".join(current_line_words)
        bbox = draw.textbbox((0, 0), full_line_lbl, font=line_font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        
        # Position
        if is_header:
             start_y = 350
        else:
             start_y = (height - line_h) // 2
             
        # Draw Words
        current_x = (width - line_w) // 2
        
        # Draw Header Box if needed
        if is_header:
             pad = 20
             draw.rounded_rectangle(
                 [current_x - pad, start_y - pad, current_x + line_w + pad, start_y + line_h + pad],
                 radius=15, fill=box_color, outline=box_border, width=3
             )
             
        for w_idx, w_txt in enumerate(current_line_words):
             # Color logic
             if w_idx == active_word_in_line:
                 fill = active_color
             else:
                 fill = default_color
                 
             # Draw Stroke (Manual)
             if not is_header and stroke_width > 0:
                 min_range = -stroke_width
                 max_range = stroke_width + 1
                 # Optim: Draw fewer strokes? (Corners only + centers)
                 # Full stroke
                 for dx in range(min_range, max_range, 2): # Skip pixels for speed
                     for dy in range(min_range, max_range, 2):
                         # Approx stroke
                         draw.text((current_x + dx, start_y + dy), w_txt, font=line_font, fill=stroke_color)
                 # Shadow
                 draw.text((current_x + shadow_offset[0], start_y + shadow_offset[1]), w_txt, font=line_font, fill=shadow_color)
             
             # Draw Text
             draw.text((current_x, start_y), w_txt, font=line_font, fill=fill)
             
             w_bbox = draw.textbbox((0, 0), w_txt, font=line_font)
             w_w = w_bbox[2] - w_bbox[0]
             space_w = draw.textlength(" ", font=line_font)
             current_x += w_w + space_w
             
        # Create Clip
        txt_clip = ImageClip(np.array(img)).set_duration(ft['duration'])
        clips_sequence.append(txt_clip)
        
    if not clips_sequence: return []
    
    # Concatenate to single track
    # Use chain because all are same size (width, height)
    final_track = concatenate_videoclips(clips_sequence, method="chain")
    final_track = final_track.set_position("center") # Ensure position
    
    return [final_track] # Return as list to be compatible with 'extend'


def create_short(script_data, audio_files, background_dir, music_dir, output_file):
    try:
        # Load Audio
        audio_clips = [AudioFileClip(f) for f in audio_files]
        full_audio = concatenate_audioclips(audio_clips)
        total_duration = full_audio.duration

        # Background
        bg_files = [f for f in os.listdir(background_dir) if f.endswith(('.mp4', '.mov'))]
        if not bg_files:
             raise FileNotFoundError(f"No background videos found in {background_dir}")
        bg_path = os.path.join(background_dir, random.choice(bg_files))
        video_bg = VideoFileClip(bg_path)
        
        # ... logic continues ...
        # Use context manager or explicit close for video_bg later

        
        if video_bg.duration < total_duration:
            video_bg = video_bg.loop(duration=total_duration + 1.5)
            
        # Crop 9:16
        target_ratio = 9/16
        if video_bg.w / video_bg.h > target_ratio:
            new_w = int(video_bg.h * target_ratio)
            video_bg = video_bg.crop(x1=video_bg.w/2 - new_w/2, width=new_w, height=video_bg.h)
            
        video_bg = video_bg.resize(height=1920)
        video_bg = video_bg.subclip(0, total_duration)

        # Slow Zoom (Ken Burns) - REMOVED for Performance (Causes 30min+ render times)
        # video_bg = video_bg.resize(lambda t: 1 + 0.02 * t) 
        
        # Dynamic Karaoke Subtitles
        subtitle_clips = []
        current_time = 0
        texts = [script_data['hook'], script_data['body'], script_data['climax']]
        
        for i, audioclip in enumerate(audio_clips):
            txt = texts[i]
            dur = audioclip.duration
            word_clips = create_karaoke_clips(txt, dur, current_time, width=1080, height=1920)
            subtitle_clips.extend(word_clips)
            current_time += dur

        # Music
        final_audio = full_audio
        if os.path.isdir(music_dir):
            m_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
            if m_files:
                music = AudioFileClip(os.path.join(music_dir, random.choice(m_files)))
                if music.duration < total_duration:
                    music = music.loop(duration=total_duration)
                else:
                    music = music.subclip(0, total_duration)
                final_audio = CompositeAudioClip([full_audio, music.volumex(0.15)])

        final_layers = [video_bg] + subtitle_clips
        final = CompositeVideoClip(final_layers, size=(1080, 1920)).set_audio(final_audio)
        final.write_videofile(output_file, fps=30, codec='libx264', audio_codec='aac', bitrate="8000k", preset='medium', threads=2)
        
        # Cleanup
        final.close()
        for c in final_clips:
            try: c.close()
            except: pass
        for sfx in sfx_lib.values():
            try: sfx.close()
            except: pass
            
        return True

    except Exception as e:
        print(f"Error creating visual comp: {e}")
        return False

def assemble_video(scenes, music_dir, output_file, title_text=None, mood="mystery"):
    """
    Assembles the final video from a list of processed scenes.
    OPTIMIZED FOR SPEED: Uses threads, faster preset, and early resizing.
    """
    try:
        final_clips = []
        
        # Initialize Style
        style_mgr = EffectsManager()
        
        # --- LOAD SFX LIBRARY ---
        sfx_dir = "sfx"
        sfx_lib = {}
        if os.path.exists(sfx_dir):
            for f in os.listdir(sfx_dir):
                name = os.path.splitext(f)[0].lower()
                if not (f.endswith('.wav') or f.endswith('.mp3')): continue
                try:
                    clip = AudioFileClip(os.path.join(sfx_dir, f))
                    # Volume Normalization - User requested pleasant/subtle
                    # Significantly reduced volume to avoid "ugly" feedback
                    clip = clip.volumex(0.12)
                    sfx_lib[name] = clip
                except Exception as ex:
                    print(f"Failed to load SFX {f}: {ex}")

        # Helper to get random SFX by type
        def get_sfx(kind):
            # USER REQUEST: remove loud noises (whoosh, impact, riser).
            # Only allow 'glitch' and 'pop' (simulating soft photo/click).
            
            allowed_types = ['glitch', 'pop']
            
            # If the requested kind is NOT allowed, try to map it to a soft one or return None
            if kind not in allowed_types:
                if kind == 'camera' or 'click' in kind:
                    kind = 'pop' # Fallback to pop for "photo" sound
                elif 'glitch' in kind:
                    kind = 'glitch'
                else:
                    return None # Block loud sounds like whoosh/impact/riser
            
            matches = [k for k in sfx_lib.keys() if kind in k]
            if matches:
                # Prefer generated ones if available for variety
                gen_matches = [m for m in matches if '_gen_' in m]
                if gen_matches and random.random() < 0.7:
                     return sfx_lib[random.choice(gen_matches)]
                return sfx_lib[random.choice(matches)]
            return None
        
        for idx, scene in enumerate(scenes):
            # Load assets
            audio_path = scene.get('audio_path')
            if not audio_path: continue
                
            video_paths = scene.get('video_paths', [scene.get('video_path')]) 
            timings = scene.get('timings', [])
            text = scene.get('text', "")
            
            audioclip = AudioFileClip(audio_path)
            duration = audioclip.duration
            
            # --- VISUAL ASSEMBLY --
            num_v_clips = len(video_paths)
            clip_duration_target = duration / max(1, num_v_clips)
            
            scene_v_clips = []
            for i, vp in enumerate(video_paths):
                if not vp or not os.path.exists(vp): continue
                
                # Check for tiny/corrupted files (< 10KB)
                if os.path.getsize(vp) < 10000:
                    print(f"      ⚠️ Skipping suspect file (too small): {vp}")
                    continue

                # Check extensions
                ext = os.path.splitext(vp)[1].lower()
                is_image = ext in ['.jpg', '.jpeg', '.png', '.webp']
                
                if is_image:
                     # KEN BURNS IMAGE
                     try:
                         # Load Image
                         img = ImageClip(vp)
                         needed_dur = clip_duration_target + 0.5
                         img = img.set_duration(needed_dur)
                         
                         # Resize to minimal covering dimension (Cover)
                         ratio = 1080 / 1920
                         img_ratio = img.w / img.h
                         
                         if img_ratio > ratio:
                             # Wider: Resize to Height=1920, Crop Width
                             img = img.resize(height=1920)
                             # Center Crop initial
                             img = img.crop(x1=(img.w - 1080)/2, width=1080, height=1920)
                         else:
                             # Taller: Resize to Width=1080, Crop Height
                             img = img.resize(width=1080)
                             img = img.crop(y1=(img.h - 1920)/2, width=1080, height=1920)
                             
                         # Apply Ken Burns (Slow Zoom)
                         # 1.0 -> 1.15
                         img = vfx_soft_zoom(img, duration=needed_dur, mode=random.choice(["in", "out"]))
                         
                         c = img
                         print(f"      📸 Converted Image to Clip (Ken Burns): {os.path.basename(vp)}")
                         
                     except Exception as e_img:
                         print(f"      ⚠️ Failed to load image clip {vp}: {e_img}")
                         continue
                else:
                    # VIDEO CLIP
                    try:
                        c = VideoFileClip(vp)
                        # ROBUSTNESS CHECK: Try to read a frame to ensure file is valid
                        c.get_frame(0)
                    except Exception as e:
                        print(f"      ⚠️ Failed to load clip {vp} (Corrupt?): {e}")
                        if 'c' in locals(): 
                            try: c.close()
                            except: pass
                        continue
                    
                    # 9:16 Crop/Fill - OPTIMIZED: Resize immediately to avoid processing 4k
                    target_ratio = 1080 / 1920
                    
                    if c.w != 1080 or c.h != 1920:
                        # Only resize if needed (Logic for dynamic resize/crop)
                        # If much larger, resize first close to target height (Optimization)
                        if c.h > 2000:
                            c = c.resize(height=1920) 
                            # Force GC after heavy resize
                            import gc
                            gc.collect() 
                        
                        # OPTIMIZATION: Always use Center Crop (Fill) for standard 16:9 content.
                        # The previous "Blurry Background" effect (Composite 2 layers) was doubling the render time per frame.
                        # For stock footage (atmosphere, people), Center Crop is standard for Shorts.
                        
                        input_ratio = c.w / c.h
                        target_ratio = 1080 / 1920
                         
                        if input_ratio > target_ratio:
                            # Input is "wider" than target (e.g. 16:9 vs 9:16) -> Fill Height, Crop Sides
                            c = c.resize(height=1920)
                            c = c.crop(x1=(c.w - 1080)/2, width=1080, height=1920)
                        else:
                            # Input is "taller" than target (rare/skinny) -> Fill Width, Crop Top/Bottom
                            c = c.resize(width=1080)
                            c = c.crop(y1=(c.h - 1920)/2, width=1080, height=1920)
                
                # --- NEW ORIGINALITY FILTERS ---
                # 1. Color Grading (Cinematic Style)
                c = vfx_color_grade(c)
                
                # 2. Random Mirroring (50% chance) - Only for videos? Images can mirror too.
                if random.random() < 0.5:
                    c = vfx_mirror(c)

                # 3. (REMOVED) Floating Image Overlay 
                # User feedback: "No tiene sentido meter una imagen arriba".
                # We now prioritize full-screen images in the main loop logic (processed above).
                
                scene_v_clips.append(c)

                # Duration Loop
                needed_dur = clip_duration_target + 0.5 
                if c.duration < needed_dur: c = c.loop(duration=needed_dur)
                else: c = c.subclip(0, needed_dur)

                # --- APPLY STYLE MOVEMENT ---
                # OPTIMIZATION: Dynamic resize/position (lambda t) forces full frame re-render.
                # Removing complex movements to fix "30 min render time" issue.
                
                # Simple static or very basic crop is much faster.
                # For now, we kept it static or simple crop.
                pass 
                
                # Grading (Subtle) - Removed for speed
                # c = c.fx(vfx.colorx, random.uniform(1.0, 1.1)) 
                
                scene_v_clips.append(c)
                
            if not scene_v_clips: continue 
                
            # Combine Visuals
            if len(scene_v_clips) > 1:
                print(f"      🔗 Concatenating {len(scene_v_clips)} clips for scene {idx}...")
                full_visual = concatenate_videoclips(scene_v_clips, method="compose", padding=-0.25)
            else:
                full_visual = scene_v_clips[0]
            
            if full_visual.duration < duration:
                full_visual = full_visual.loop(duration=duration)
            full_visual = full_visual.subclip(0, duration)
            
            # --- APPLY MIDDLE EFFECTS ---
            # Current timeframe validation
            # We approximate current_time based on previously added clips
            # (In a real scenario we'd track total duration, here we trust the manager logic purely on sequence)
            
            # Note: For accurate time tracking we'd need to sum durations, but simple sequence logic works for "variety"
            effect_type = style_mgr.get_middle_effect(idx * 3.0, duration) # Approximate time
            effect_applied = False
            
            if effect_type:
                if effect_type == "glitch_mild":
                    glitched_part = vfx_glitch_clip(full_visual, duration=0.4)
                    full_visual = CompositeVideoClip([full_visual, glitched_part.set_start(0)], size=(1080,1920))
                    # Pleasant SFX: Very quiet glitch
                    sfx = get_sfx('glitch_gen') # Use generated ones if possible, usually cleaner
                    if not sfx: sfx = get_sfx('glitch')
                    if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.1)])
                    effect_applied = True
                    
                elif effect_type == "shake":
                    full_visual = vfx_shake(full_visual, strength=8)
                    # Pleasant: Soft impact/whoosh instead of hard hit
                    sfx = get_sfx('pop') 
                    if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.15)])
                    effect_applied = True

                elif effect_type == "pulse":
                    # Flash of brightness at start
                    pulse = full_visual.subclip(0, 0.3).fx(vfx.colorx, 1.4)
                    rest = full_visual.subclip(0.3)
                    full_visual = concatenate_videoclips([pulse, rest])
                    # Pleasant: Pop
                    sfx = get_sfx('pop')
                    if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.15)])
                    effect_applied = True
                    
                elif effect_type == "soft_zoom":
                     # Apply Ken Burns
                     full_visual = vfx_soft_zoom(full_visual, duration=duration, mode=random.choice(["in", "out"]))
                     # No specific SFX needed, or maybe very faint ambience? 
                     # User wants "dynamic" but "no noise". Silence is fine for zoom.
                     # Or subtle pop if it marks a transition? Let's keep it silent/clean.
                     effect_applied = True
                     
                elif effect_type == "slide_left":
                     # Slide this clip IN over the previous one?
                     # Since we are iterating clips, 'full_visual' is the current clip.
                     # If we slide it in, it reveals... what? Black?
                     # Actually, a slide transition usually requires overlap with previous clip.
                     # BUT since `assemble_video` concatenates them sequentially without overlap logic here easily,
                     # we can simulate a "Push" by just animating the entry of this clip, 
                     # assuming the previous clip ended cleanly.
                     
                     # It will look like it slides in from black (or background).
                     # Better than nothing.
                     full_visual = vfx_slide_transition(full_visual, duration=0.6, direction="left")
                     
                     # SFX: Soft swish -> use 'pop' or silence.
                     # Let's use pop or nothing.
                     sfx = get_sfx('pop')
                     if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.1)])
                     effect_applied = True
            
            # --- SUBTITLES & TITLE ---
            scene_overlays = []
            
            # Use 'Title Box' style for the first scene (Hook/Intro)
            is_intro_scene = (idx == 0)
            
            # Generate Subtitles
            # Note: create_karaoke_clips uses t['start'] purely.
            word_clips = create_karaoke_clips(
                timings, 
                duration, 
                0, 
                width=1080, 
                height=1920, 
                raw_text=text,
                is_header=is_intro_scene # Highlight if Intro
            )
            if not word_clips and text:
                 print(f"      ⚠️ Warning: No karaoke clips generated for text: {text[:20]}...")
            
            scene_overlays.extend(word_clips)
            
            # Composite Scene
            scene_comp = CompositeVideoClip([full_visual] + scene_overlays, size=(1080, 1920))
            
            # --- SCENE SFX (Fallback) ---
            # Removed random scene SFX (pops/impacts) as per user request to improve quality
            
            scene_comp = scene_comp.set_audio(audioclip)
            final_clips.append(scene_comp)
            
            # --- MEMORY SAFETY ---
            # Explicitly clear large objects if possible
            del full_visual
            del scene_overlays
            import gc
            if idx % 2 == 0: gc.collect() # Collect every 2 scenes
            
        if not final_clips: return False

        # --- FINAL ASSEMBLY & TRANSITIONS ---
        final_video = concatenate_videoclips(final_clips, method="compose", padding=-0.2)
        
        # Audio Mixing
        main_audio = final_video.audio
        audio_layers = [main_audio]

        # 1. Whooshes - STRIPPED due to user request (loud/annoying)
        # whoosh = get_sfx('whoosh')
        # if whoosh:
        #     curr_t = 0
        #     for i in range(len(final_clips)-1):
        #         curr_t += final_clips[i].duration - 0.2
        #         if random.random() < style_mgr.get_transition_prob():
        #              audio_layers.append(whoosh.set_start(max(0, curr_t - 0.3)))
        
        # 2. Riser - STRIPPED due to user request
        # riser = get_sfx('riser')
        # if riser:
        #     start_t = final_video.duration - 2.5
        #     if start_t > 0:
        #         audio_layers.append(riser.set_start(start_t))

        # 3. Soft Transitions (Pop/Click instead of Whoosh)
        # Add subtle pops at cuts?
        pop_sfx = get_sfx('pop')
        if pop_sfx:
             curr_t = 0
             for i in range(len(final_clips)-1):
                 curr_t += final_clips[i].duration - 0.2
                 # Lower prob, very subtle
                 if random.random() < 0.3: 
                      audio_layers.append(pop_sfx.set_start(max(0, curr_t)).volumex(0.1))

        # 3. Music
        if os.path.isdir(music_dir):
            all_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
            
            # Smart Music Selection
            allowed_files = MUSIC_MOODS.get(mood, [])
            
            # Filter available files that match the mood
            valid_choices = [f for f in all_files if f in allowed_files]
            
            # Fallback: if no specific mood files found, use any
            if not valid_choices:
                print(f"⚠️ No music found for mood '{mood}'. Using random.")
                valid_choices = all_files
            
            if valid_choices:
                selected_track = random.choice(valid_choices)
                print(f"🎵 Music Selected: {selected_track} (Mood: {mood})")
                
                music = AudioFileClip(os.path.join(music_dir, selected_track))
                if music.duration < final_video.duration:
                    music = audio_loop(music, duration=final_video.duration)
                else:
                    music = music.subclip(0, final_video.duration)
                audio_layers.append(music.volumex(0.12))
        
        final_video = final_video.set_audio(CompositeAudioClip(audio_layers))
        
        # --- MANDATORY INTRO EFFECT ---
        intro_dur = 0.5
        if style_mgr.intro_effect == "cinematic_zoom":
            # "Transicion mas linda"
            # Logic: Start Black and Zoomed In (1.2) -> Fade In and Zoom Out to (1.0)
            intro_duration = 0.8
            
            # We apply this to the WHOLE FINAL VIDEO? No, that's heavy.
            # But since we optimized by removing the *constant* zoom, a single short zoom at the start is fine.
            # It only affects the first 0.8s of frames.
            
            # Split into intro part and rest
            intro_part = final_video.subclip(0, intro_duration)
            rest_part = final_video.subclip(intro_duration)
            
            # Visual: Zoom Out (1.2 -> 1.0) + Fade In
            intro_part = intro_part.resize(lambda t: 1.2 - 0.2 * (t/intro_duration))
            intro_part = intro_part.fadein(0.6)
            
            final_video = concatenate_videoclips([intro_part, rest_part])
            
            # Audiovisual: Nice Whoosh + Impact -> REPLACED with Soft Pop/Glitch
            # sfx_whoosh = get_sfx('whoosh')
            # if sfx_whoosh: audio_layers.append(sfx_whoosh.set_start(0).volumex(0.25))
            
            # sfx_impact = get_sfx('impact') 
            # if sfx_impact: audio_layers.append(sfx_impact.set_start(0.1).volumex(0.15))
            
            sfx_soft = get_sfx('pop')
            if sfx_soft: audio_layers.append(sfx_soft.set_start(0).volumex(0.15))

        elif style_mgr.intro_effect == "flash_in":
            flash = create_flash_transition()
            final_video = CompositeVideoClip([final_video, flash.set_start(0)], size=(1080,1920))
            # Pleasant whoosh -> Soft Pop
            sfx_intro = get_sfx('pop')
            if sfx_intro: audio_layers.append(sfx_intro.set_start(0).volumex(0.15))
            
        elif style_mgr.intro_effect == "glitch_start":
            # Apply glitch to first 0.5s
            intro_clip = final_video.subclip(0, 0.6)
            intro_glitch = vfx_glitch_clip(intro_clip, duration=0.6)
            final_video = CompositeVideoClip([final_video, intro_glitch.set_start(0)], size=(1080,1920))
            # Quiet glitch
            sfx_intro = get_sfx('glitch')
            if sfx_intro: audio_layers.append(sfx_intro.set_start(0).volumex(0.15))
            
        elif style_mgr.intro_effect == "slide_in":
             # Moving final_video is okay.
             final_video = final_video.set_position(lambda t: (int(-1080 + 1080*(t/0.5)), "center") if t < 0.5 else "center")
             # Whoosh -> Soft Pop
             sfx_intro = get_sfx('pop')
             if sfx_intro: audio_layers.append(sfx_intro.set_start(0).volumex(0.15))

        # Re-set audio after Intro SFX additions
        if len(audio_layers) > 1:
            final_video = final_video.set_audio(CompositeAudioClip(audio_layers))

        # --- MANDATORY OUTRO EFFECT ---
        outro_dur = 0.8
        total_dur = final_video.duration
        
        if style_mgr.outro_effect == "fade_out":
            final_video = final_video.fadeout(outro_dur)
            
        elif style_mgr.outro_effect == "burn_out":
            # Fade to white
            final_video = final_video.fadeout(outro_dur, (255,255,255))
            
        elif style_mgr.outro_effect == "glitch_out":
            start_glitch = total_dur - 0.6
            if start_glitch > 0:
                end_part = final_video.subclip(start_glitch)
                end_glitch = vfx_glitch_clip(end_part, duration=0.6)
                # Overlay
                final_video = CompositeVideoClip([final_video, end_glitch.set_start(start_glitch)], size=(1080,1920))
                # Quiet glitch out
                sfx_outro = get_sfx('glitch')
                if sfx_outro: 
                     new_audio = CompositeAudioClip([final_video.audio, sfx_outro.set_start(start_glitch).volumex(0.5)])
                     final_video = final_video.set_audio(new_audio)

        if style_mgr.outro_effect == "glitch_out":
            # ... (Glitch out logic kept)
            pass

        # --- ORIGINALITY: PROGRESS BAR ---
        # "Retention Bar"
        final_video = vfx_progress_bar(final_video, color=(200, 0, 0), height=15)

        # --- ORIGINALITY: WATERMARK ---
        # Subtle branding in top-right or bottom
        try:
             # Use TextClip if ImageMagick is configured, OR use PIL ImageClip
             # Using PIL ImageClip for safety (no dependency on ImageMagick binary)
             wm_w, wm_h = 400, 100
             wm_img = Image.new('RGBA', (wm_w, wm_h), (0,0,0,0))
             wm_draw = ImageDraw.Draw(wm_img)
             
             # Load small font
             try:
                 wm_font = ImageFont.truetype(FONT_PATH, 40)
             except:
                 wm_font = ImageFont.load_default()
                 
             # Text with shadow
             wm_text = CHANNEL_NAME
             # Shadow
             wm_draw.text((22, 22), wm_text, font=wm_font, fill=(0,0,0,128))
             # Main
             wm_draw.text((20, 20), wm_text, font=wm_font, fill=(255,255,255,128)) # 50% opacity
             
             wm_clip = ImageClip(np.array(wm_img)).set_duration(final_video.duration)
             # Position: Bottom Center, slightly up
             wm_clip = wm_clip.set_position(("center", 1800))
             
             final_video = CompositeVideoClip([final_video, wm_clip], size=(1080,1920))
             print(f"      💧 Watermark applied: {CHANNEL_NAME}")
             
        except Exception as e_wm:
             print(f"      ⚠️ Watermark error: {e_wm}")

        # Removed Global Title Overlay loop to prevent overlapping/mess ("horrible")
        # Title is now handled sequentially in the first scene loop.

        # OPTIMIZED WRITE: PRESET FASTER, THREADS 4
        final_video.write_videofile(
            output_file, 
            fps=30, 
            codec='libx264', 
            audio_codec='aac', 
            bitrate="8000k", 
            preset='veryfast',   # Balanced speed/stability
            threads=1          # SAFE MODE: Reduce threads to prevent OOM on GitHub Runners
        )
        # Cleanup Resources
        try:
            final_video.close()
            for c in final_clips:
                try: c.close()
                except: pass
            for s in sfx_lib.values():
                try: s.close()
                except: pass
        except:
            pass
            
        return True

    except Exception as e:
        print(f"Error assembling video: {e}")
        import traceback
        traceback.print_exc()
        return False
