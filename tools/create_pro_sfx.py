import numpy as np
from scipy.io import wavfile
import os
import random

def save_wav(filename, rate, data):
    # Normalize to 16-bit PCM
    data = data / np.max(np.abs(data)) * 32767
    wavfile.write(filename, rate, data.astype(np.int16))
    print(f"Generated: {filename}")

def generate_pop(filename):
    rate = 44100
    duration = 0.1
    t = np.linspace(0, duration, int(rate * duration), endpoint=False)
    
    # High frequency sine burst with rapid decay
    freq = 600
    envelope = np.exp(-t * 80) # Fast decay
    # Add a little noise for "click" texture
    noise = np.random.normal(0, 0.1, len(t)) * envelope
    
    wave = np.sin(2 * np.pi * freq * t) * envelope
    wave = wave + noise
    
    save_wav(filename, rate, wave)

def generate_glitch(filename):
    rate = 44100
    duration = 0.4
    
    # Generate chunks of random noise and silence
    chunks = []
    current_time = 0
    while current_time < duration:
        chunk_dur = random.uniform(0.01, 0.05)
        t = np.linspace(0, chunk_dur, int(rate * chunk_dur), endpoint=False)
        
        mode = random.choice(['noise', 'square', 'silence', 'sine'])
        
        if mode == 'noise':
            # Soften noise: use uniform instead of normal, and filter high freqs?
            # Simple "LPF": moving average or just lower amplitude
            raw_noise = np.random.uniform(-0.3, 0.3, len(t))
            # Simple smoothing (Low Pass)
            chunk = np.convolve(raw_noise, np.ones(5)/5, mode='same')
        elif mode == 'square':
            # Lower frequency for less piercing sound
            freq = random.choice([100, 200, 400]) 
            chunk = np.sign(np.sin(2 * np.pi * freq * t)) * 0.2
        elif mode == 'sine':
             freq = random.choice([300, 600])
             chunk = np.sin(2 * np.pi * freq * t) * 0.2
        else:
            chunk = np.zeros(len(t))
            
        chunks.append(chunk)
        current_time += chunk_dur
        
    full_audio = np.concatenate(chunks)
    # Trim to exact duration
    full_audio = full_audio[:int(rate * duration)]
    
    # Global volume reduction
    full_audio = full_audio * 0.5
    
    save_wav(filename, rate, full_audio)

def generate_riser(filename):
    rate = 44100
    duration = 2.0
    t = np.linspace(0, duration, int(rate * duration), endpoint=False)
    
    # Exponential frequency sweep (White Noise filtered or just Sine Sweep)
    # Simple Sine Sweep
    f0 = 200
    f1 = 800
    freq_sweep = np.linspace(f0, f1, len(t))
    phase = 2 * np.pi * np.cumsum(freq_sweep) / rate
    
    sine_wave = np.sin(phase)
    
    # Add White Noise that grows in volume
    noise = np.random.normal(0, 1, len(t))
    
    # Volume envelope: Exponential growth
    volume = np.exp(t * 1.5) - 1
    volume = volume / np.max(volume) # Normalize 0-1
    
    # Combine
    audio = (sine_wave * 0.3 + noise * 0.7) * volume
    
    save_wav(filename, rate, audio)

def generate_impact_thud(filename):
    rate = 44100
    duration = 0.8
    t = np.linspace(0, duration, int(rate * duration), endpoint=False)
    
    # Low frequency sine drop
    f0 = 150
    f1 = 40
    freq_sweep = np.linspace(f0, f1, len(t))
    phase = 2 * np.pi * np.cumsum(freq_sweep) / rate
    
    sine = np.sin(phase)
    
    # Envelope: Fast attack, slow decay
    envelope = np.exp(-t * 5)
    
    audio = sine * envelope
    save_wav(filename, rate, audio)

if __name__ == "__main__":
    output_dir = "sfx"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating SFX library...")
    generate_pop(os.path.join(output_dir, "pop.wav"))
    generate_glitch(os.path.join(output_dir, "glitch_1.wav"))
    generate_glitch(os.path.join(output_dir, "glitch_2.wav"))
    generate_riser(os.path.join(output_dir, "riser.wav"))
    generate_impact_thud(os.path.join(output_dir, "impact.wav"))
    print("Done.")
