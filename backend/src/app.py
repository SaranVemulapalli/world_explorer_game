import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
import math
import random # Needed for gradient randomness based on seed

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Perlin Noise Helper Functions ---

# Linear interpolation
def lerp(a, b, x):
    return a + x * (b - a)

# Smootherstep (smoother interpolation curve)
def fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)

# Gradient function for 2D noise
# Determines the direction of influence from each grid point
def gradient(ix, iy, x, y, random_seed):
    # Use a pseudo-random number generator for consistent gradients based on seed
    # Re-seed for each grid point to ensure deterministic but varied gradients
    # Mixing grid coords with original seed ensures reproducibility per-grid-point
    random.seed(random_seed + ix * 100000 + iy * 1000) # Increased factors for better spread

    # Predefined 8 gradient vectors for 2D. These give different "looks".
    # (1,0), (0,1), (-1,0), (0,-1) are cardinal directions
    # (1,1), (1,-1), (-1,1), (-1,-1) are diagonal directions
    gradients = [
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (1, -1), (-1, 1), (-1, -1)
    ]
    # Select a random gradient vector from the predefined set.
    # The choice must be consistent for a given (ix, iy) and random_seed.
    grad_vec = gradients[random.randint(0, len(gradients) - 1)]

    # Calculate distance vectors from the point (x,y) to the grid point (ix,iy)
    dx = x - ix
    dy = y - iy

    # Dot product of gradient vector and distance vector
    return (grad_vec[0] * dx + grad_vec[1] * dy)

# --- Perlin Noise Implementation ---
def generate_perlin_noise(width, height, octaves=4, persistence=0.5, lacunarity=2.0, scale=30.0, seed=0):
    """
    Generates a 2D Perlin Noise map using multiple octaves (Fractal Brownian Motion).

    Args:
        width (int): Width of the noise map.
        height (int): Height of the noise map.
        octaves (int): Number of layers of noise. Higher octaves add more detail/roughness.
        persistence (float): How much each successive octave contributes to the overall shape.
                            (e.g., 0.5 means each octave contributes half as much as the previous).
        lacunarity (float): How much the frequency increases with each octave. (e.g., 2.0 means
                            each octave has double the frequency of the previous).
        scale (float): Determines the "zoom level" of the noise. Lower values zoom in (larger,
                       smoother features), higher values zoom out (smaller, more detailed features).
        seed (int): Random seed for reproducible noise generation.

    Returns:
        np.ndarray: A 2D numpy array representing the Perlin noise map, with values
                    normalized to the range [0, 1].
    """
    noise_map = np.zeros((height, width))

    max_amplitude = 0 # Used for normalization
    # Pre-calculate frequencies and amplitudes for all octaves
    amplitudes_config = []
    for octave in range(octaves):
        frequency = lacunarity**octave
        amplitude = persistence**octave
        max_amplitude += amplitude
        amplitudes_config.append((frequency, amplitude))

    # Generate noise for each pixel
    for y in range(height):
        for x in range(width):
            noise_value = 0
            # Sum up noise from all octaves
            for i in range(octaves):
                frequency, amplitude = amplitudes_config[i]

                # Scale x and y based on frequency and overall map scale
                sample_x = x / scale * frequency
                sample_y = y / scale * frequency

                # Determine grid cell coordinates for interpolation
                x0 = math.floor(sample_x)
                x1 = x0 + 1
                y0 = math.floor(sample_y)
                y1 = y0 + 1

                # Calculate interpolation weights using the fade function for smoother transitions
                sx = fade(sample_x - x0)
                sy = fade(sample_y - y0)

                # Calculate dot products for the 4 corners of the grid cell
                # These are the "random" values based on the gradient vectors and distances
                n0 = gradient(x0, y0, sample_x, sample_y, seed)
                n1 = gradient(x1, y0, sample_x, sample_y, seed)
                n2 = gradient(x0, y1, sample_x, sample_y, seed)
                n3 = gradient(x1, y1, sample_x, sample_y, seed)

                # Interpolate along x-axis for top and bottom edges of the cell
                ix0 = lerp(n0, n1, sx)
                ix1 = lerp(n2, n3, sx)

                # Interpolate along y-axis to get the final noise value for this octave
                noise_value += lerp(ix0, ix1, sy) * amplitude

            # Assign the sum of octave noise values to the map
            noise_map[y][x] = noise_value

    # Normalize the entire noise map to the [0, 1] range
    # This is important to map noise values to terrain types consistently.
    min_val = np.min(noise_map)
    max_val = np.max(noise_map)
    if max_val - min_val > 0:
        noise_map = (noise_map - min_val) / (max_val - min_val)
    else:
        # Handle case where all values are the same (e.g., flat noise due to bad parameters)
        noise_map.fill(0.5) # Fill with mid-value

    return noise_map

# --- Flask App Routes ---

@app.route('/')
def index():
    return "Flask backend is running. Access /generate_world for world data."

@app.route('/generate_world')
def generate_world():
    seed = int(request.args.get('seed', 0)) # Default seed 0
    size = int(request.args.get('size', 64)) # Default size 64x64

    print(f"Generating world with seed={seed} and size={size}...")

    # Generate Perlin noise map instead of dummy noise
    # Experiment with these parameters to see different world types!
    # octaves: More layers = more detail/roughness.
    # persistence: How much each detail layer contributes.
    # lacunarity: How much the detail layer's frequency increases.
    # scale: The "zoom" level of the noise. Smaller scale = larger, smoother features.
    noise_map = generate_perlin_noise(width=size, height=size,
                                      octaves=4, persistence=0.01, lacunarity=2.0, scale=30.0,
                                      seed=seed)

    # Convert noise values to terrain types
    # Noise values are between 0 and 1
    # You can adjust these thresholds to control the proportion of each terrain type
    terrain_tiles = []
    for row in noise_map:
        terrain_row = []
        for noise_val in row:
            if noise_val < 0.4:  # Adjust this threshold for more/less water
                terrain_row.append(0)  # Water
            elif noise_val < 0.7: # Adjust this threshold for more/less grass
                terrain_row.append(1)  # Grass
            else:
                terrain_row.append(2)  # Mountain
        terrain_tiles.append(terrain_row)

    print(f"World generated with {len(terrain_tiles)}x{len(terrain_tiles[0])} tiles.")
    return jsonify({'size': size, 'tiles': terrain_tiles})

if __name__ == '__main__':
    print("Starting Flask app...")
    print(f"Access world generation at: http://127.0.0.1:5000/generate_world?seed=123&size=64")
    app.run(debug=True, port=5000)